"""
Quota Enforcement Middleware
Tracks and enforces per-tenant resource quotas
"""
import logging
import time
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# In-memory quota tracking (for demo)
# In production, use Redis or database
_quota_usage = defaultdict(lambda: {
    "api_calls_hour": [],  # List of timestamps
    "api_calls_month": 0,
    "storage_gb": 0.0,
    "last_reset_month": datetime.now()
})


class QuotaEnforcementMiddleware(BaseHTTPMiddleware):
    """
    Enforce per-tenant resource quotas
    
    Tracks and limits:
    - API calls per hour
    - API calls per month
    - Storage usage
    
    Returns 429 Too Many Requests when quota exceeded
    
    Usage:
        app.add_middleware(QuotaEnforcementMiddleware)
    """
    
    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled
    
    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)
        
        # Get tenant ID from request state (set by TenantContextMiddleware)
        tenant_id = getattr(request.state, "tenant_id", None)
        
        # Skip quota enforcement for:
        # 1. Requests without tenant (public endpoints)
        # 2. Internal requests
        # 3. Health checks
        if not tenant_id or self._is_exempt_endpoint(request.url.path):
            return await call_next(request)
        
        # Get tenant tier (in production, fetch from database)
        tenant_tier = self._get_tenant_tier(tenant_id)
        
        # Get quota limits for this tier
        from middleware.tenant_context import get_tenant_limits
        limits = get_tenant_limits(tenant_tier)
        
        # Check API call quotas
        quota_check = self._check_api_quota(
            tenant_id,
            limits["max_api_calls_per_hour"],
            limits["max_api_calls_per_month"]
        )
        
        if not quota_check["allowed"]:
            logger.warning(f"Quota exceeded for tenant {tenant_id}: {quota_check['reason']}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Quota exceeded",
                    "message": quota_check["reason"],
                    "quota_type": quota_check["quota_type"],
                    "limit": quota_check["limit"],
                    "current": quota_check["current"],
                    "reset_at": quota_check["reset_at"]
                },
                headers={
                    "Retry-After": str(quota_check.get("retry_after", 3600)),
                    "X-RateLimit-Limit": str(quota_check["limit"]),
                    "X-RateLimit-Remaining": str(max(0, quota_check["limit"] - quota_check["current"])),
                    "X-RateLimit-Reset": str(quota_check.get("reset_at", ""))
                }
            )
        
        # Record this API call
        self._record_api_call(tenant_id)
        
        # Process request
        start_time = time.time()
        response: Response = await call_next(request)
        duration = time.time() - start_time
        
        # Add quota headers to response
        usage = _quota_usage[tenant_id]
        hourly_calls = len([t for t in usage["api_calls_hour"] if time.time() - t < 3600])
        
        response.headers["X-RateLimit-Limit-Hour"] = str(limits["max_api_calls_per_hour"])
        response.headers["X-RateLimit-Remaining-Hour"] = str(max(0, limits["max_api_calls_per_hour"] - hourly_calls))
        response.headers["X-RateLimit-Limit-Month"] = str(limits["max_api_calls_per_month"])
        response.headers["X-RateLimit-Remaining-Month"] = str(max(0, limits["max_api_calls_per_month"] - usage["api_calls_month"]))
        
        # Track usage for billing
        try:
            from middleware.metrics_enhanced import track_revenue_event
            track_revenue_event(tenant_id, "api_call")
        except Exception:
            pass
        
        return response
    
    def _check_api_quota(self, tenant_id: str, hourly_limit: int, monthly_limit: int) -> dict:
        """Check if tenant is within API call quotas"""
        usage = _quota_usage[tenant_id]
        now = time.time()
        
        # Reset monthly counter if needed
        if datetime.now().month != usage["last_reset_month"].month:
            usage["api_calls_month"] = 0
            usage["last_reset_month"] = datetime.now()
        
        # Clean up old hourly timestamps (older than 1 hour)
        usage["api_calls_hour"] = [t for t in usage["api_calls_hour"] if now - t < 3600]
        
        # Check hourly limit
        hourly_calls = len(usage["api_calls_hour"])
        if hourly_calls >= hourly_limit:
            # Calculate when oldest call will expire
            oldest_call = min(usage["api_calls_hour"])
            retry_after = int(3600 - (now - oldest_call))
            
            return {
                "allowed": False,
                "reason": f"Hourly API call limit exceeded ({hourly_limit} calls/hour)",
                "quota_type": "hourly",
                "limit": hourly_limit,
                "current": hourly_calls,
                "retry_after": retry_after,
                "reset_at": datetime.fromtimestamp(oldest_call + 3600).isoformat()
            }
        
        # Check monthly limit
        if usage["api_calls_month"] >= monthly_limit:
            # Calculate next month
            next_month = (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1)
            
            return {
                "allowed": False,
                "reason": f"Monthly API call limit exceeded ({monthly_limit} calls/month)",
                "quota_type": "monthly",
                "limit": monthly_limit,
                "current": usage["api_calls_month"],
                "reset_at": next_month.isoformat()
            }
        
        return {
            "allowed": True,
            "hourly_remaining": hourly_limit - hourly_calls,
            "monthly_remaining": monthly_limit - usage["api_calls_month"]
        }
    
    def _record_api_call(self, tenant_id: str):
        """Record an API call for quota tracking"""
        usage = _quota_usage[tenant_id]
        usage["api_calls_hour"].append(time.time())
        usage["api_calls_month"] += 1
    
    def _get_tenant_tier(self, tenant_id: str) -> str:
        """Get tenant tier (in production, fetch from database)"""
        # Demo: assign tiers based on tenant ID
        if tenant_id.endswith("-enterprise"):
            return "enterprise"
        elif tenant_id.endswith("-pro"):
            return "professional"
        elif tenant_id.endswith("-starter"):
            return "starter"
        return "free"
    
    def _is_exempt_endpoint(self, path: str) -> bool:
        """Check if endpoint is exempt from quota enforcement"""
        exempt_paths = [
            "/api/health",
            "/api/docs",
            "/api/redoc",
            "/metrics",
            "/api/v1/cache/stats"
        ]
        return path in exempt_paths


def get_tenant_usage(tenant_id: str) -> dict:
    """
    Get current usage stats for a tenant
    
    Usage:
        from middleware.quota_enforcement import get_tenant_usage
        
        @app.get("/api/v1/usage")
        async def get_usage(request: Request):
            tenant_id = require_tenant(request)
            usage = get_tenant_usage(tenant_id)
            return usage
    """
    usage = _quota_usage[tenant_id]
    now = time.time()
    
    # Clean old data
    usage["api_calls_hour"] = [t for t in usage["api_calls_hour"] if now - t < 3600]
    
    # Get limits
    from middleware.tenant_context import get_tenant_limits
    tier = "free"  # In production, fetch from DB
    limits = get_tenant_limits(tier)
    
    hourly_calls = len(usage["api_calls_hour"])
    
    return {
        "tenant_id": tenant_id,
        "tier": tier,
        "api_calls": {
            "hourly": {
                "current": hourly_calls,
                "limit": limits["max_api_calls_per_hour"],
                "remaining": max(0, limits["max_api_calls_per_hour"] - hourly_calls),
                "percentage": round(hourly_calls / limits["max_api_calls_per_hour"] * 100, 2) if limits["max_api_calls_per_hour"] > 0 else 0
            },
            "monthly": {
                "current": usage["api_calls_month"],
                "limit": limits["max_api_calls_per_month"],
                "remaining": max(0, limits["max_api_calls_per_month"] - usage["api_calls_month"]),
                "percentage": round(usage["api_calls_month"] / limits["max_api_calls_per_month"] * 100, 2) if limits["max_api_calls_per_month"] > 0 else 0
            }
        },
        "storage": {
            "current_gb": usage["storage_gb"],
            "limit_gb": limits["max_storage_gb"],
            "remaining_gb": max(0, limits["max_storage_gb"] - usage["storage_gb"])
        },
        "features": limits["features"]
    }


# Example usage in routes:
"""
from middleware.quota_enforcement import get_tenant_usage
from middleware.tenant_context import require_tenant

@app.get("/api/v1/usage")
async def get_my_usage(request: Request):
    '''Get current tenant usage and limits'''
    tenant_id = require_tenant(request)
    usage = get_tenant_usage(tenant_id)
    return usage


@app.get("/api/v1/upgrade-required")
async def check_feature(request: Request, feature: str):
    '''Check if tenant has access to a feature'''
    tenant_id = require_tenant(request)
    usage = get_tenant_usage(tenant_id)
    
    has_feature = usage["features"].get(feature, False)
    if not has_feature:
        return {
            "feature": feature,
            "available": False,
            "message": f"Feature '{feature}' requires upgrade to higher tier",
            "current_tier": usage["tier"],
            "upgrade_url": "/api/v1/upgrade"
        }
    
    return {"feature": feature, "available": True}
"""
