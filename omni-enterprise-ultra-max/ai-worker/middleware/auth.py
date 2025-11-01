"""
API Authentication and Rate Limiting Middleware
Protects endpoints with API key authentication and rate limiting
"""

from fastapi import Request, HTTPException, Header
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import Optional, Dict, Callable
import hashlib
import hmac
import os
from datetime import datetime
from utils.structured_logging import get_logger

logger = get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# In-memory API key store (replace with database in production)
API_KEYS: Dict[str, Dict] = {
    # Format: "api_key": {"tenant_id": str, "tier": str, "name": str}
    # Example keys (generate secure ones in production)
    "demo-free-key-12345": {
        "tenant_id": "demo-tenant-1",
        "tier": "free",
        "name": "Demo Free Account",
        "rate_limit": "100/minute"
    },
    "demo-pro-key-67890": {
        "tenant_id": "demo-tenant-2",
        "tier": "pro",
        "name": "Demo Pro Account",
        "rate_limit": "1000/minute"
    },
    "demo-enterprise-key-abcdef": {
        "tenant_id": "demo-tenant-3",
        "tier": "enterprise",
        "name": "Demo Enterprise Account",
        "rate_limit": "10000/minute"
    }
}

# Load master key from environment
MASTER_API_KEY = os.getenv("MASTER_API_KEY", "master-key-change-in-production")

# Public endpoints that don't require authentication
PUBLIC_ENDPOINTS = [
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/metrics"
]


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip authentication for public endpoints
        if any(request.url.path.startswith(endpoint) for endpoint in PUBLIC_ENDPOINTS):
            return await call_next(request)
        
        # Get API key from header
        api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "")
        
        if not api_key:
            logger.warning(
                "Missing API key",
                path=request.url.path,
                client_ip=request.client.host
            )
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Authentication required",
                    "message": "Please provide an API key in the X-API-Key header or Authorization header",
                    "docs": "/docs"
                }
            )
        
        # Validate API key
        api_key_info = validate_api_key(api_key)
        
        if not api_key_info:
            logger.warning(
                "Invalid API key",
                path=request.url.path,
                client_ip=request.client.host,
                api_key_prefix=api_key[:10] + "..."
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Invalid API key",
                    "message": "The provided API key is not valid"
                }
            )
        
        # Add authentication info to request state
        request.state.tenant_id = api_key_info["tenant_id"]
        request.state.tier = api_key_info["tier"]
        request.state.account_name = api_key_info["name"]
        request.state.rate_limit = api_key_info.get("rate_limit", "100/minute")
        
        logger.info(
            "Request authenticated",
            tenant_id=api_key_info["tenant_id"],
            tier=api_key_info["tier"],
            path=request.url.path
        )
        
        return await call_next(request)


def validate_api_key(api_key: str) -> Optional[Dict]:
    """
    Validate API key and return tenant information
    
    Args:
        api_key: API key to validate
        
    Returns:
        Dict with tenant info if valid, None otherwise
    """
    # Check master key
    if api_key == MASTER_API_KEY:
        return {
            "tenant_id": "master",
            "tier": "enterprise",
            "name": "Master Account",
            "rate_limit": "unlimited"
        }
    
    # Check regular keys
    if api_key in API_KEYS:
        return API_KEYS[api_key]
    
    return None


def get_rate_limit_for_tier(tier: str) -> str:
    """Get rate limit string for tier"""
    limits = {
        "free": "100/minute",
        "pro": "1000/minute",
        "enterprise": "10000/minute"
    }
    return limits.get(tier, "100/minute")


def create_api_key(tenant_id: str, tier: str = "free", name: str = "") -> str:
    """
    Create a new API key (utility function)
    
    Args:
        tenant_id: Tenant ID
        tier: Tier level (free, pro, enterprise)
        name: Account name
        
    Returns:
        Generated API key
    """
    # Generate secure API key
    random_bytes = os.urandom(32)
    api_key = f"omni_{tier}_{hashlib.sha256(random_bytes).hexdigest()[:32]}"
    
    # Store in memory (in production, save to database)
    API_KEYS[api_key] = {
        "tenant_id": tenant_id,
        "tier": tier,
        "name": name or f"{tier.capitalize()} Account",
        "rate_limit": get_rate_limit_for_tier(tier),
        "created_at": datetime.utcnow().isoformat()
    }
    
    logger.info(
        "API key created",
        tenant_id=tenant_id,
        tier=tier,
        api_key_prefix=api_key[:15] + "..."
    )
    
    return api_key


def revoke_api_key(api_key: str) -> bool:
    """
    Revoke an API key
    
    Args:
        api_key: API key to revoke
        
    Returns:
        True if revoked, False if not found
    """
    if api_key in API_KEYS:
        tenant_id = API_KEYS[api_key]["tenant_id"]
        del API_KEYS[api_key]
        
        logger.info(
            "API key revoked",
            tenant_id=tenant_id,
            api_key_prefix=api_key[:15] + "..."
        )
        return True
    
    return False


# Dependency to get authenticated tenant_id
def get_tenant_id(request: Request) -> str:
    """Get tenant_id from authenticated request"""
    return getattr(request.state, "tenant_id", "default")


def get_tier(request: Request) -> str:
    """Get tier from authenticated request"""
    return getattr(request.state, "tier", "free")


# Rate limit decorator helper
def rate_limit_by_tier(request: Request) -> str:
    """Dynamic rate limiting based on tier"""
    tier = getattr(request.state, "tier", "free")
    return get_rate_limit_for_tier(tier)
