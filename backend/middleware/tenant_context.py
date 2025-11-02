"""
Multi-Tenancy Context Middleware
Extracts tenant_id from requests and enforces tenant isolation
"""
import logging
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi import HTTPException
import hashlib
import os

logger = logging.getLogger(__name__)

# Simple in-memory API key store for demo
# In production, store in database
_API_KEYS = {}


def register_api_key(api_key: str, tenant_id: str, tenant_name: str = ""):
    """Register an API key for a tenant"""
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    _API_KEYS[key_hash] = {
        "tenant_id": tenant_id,
        "tenant_name": tenant_name,
        "rate_limit": 1000,  # per hour
        "is_active": True
    }
    logger.info(f"Registered API key for tenant: {tenant_id}")


def get_tenant_from_api_key(api_key: str) -> Optional[dict]:
    """Get tenant info from API key"""
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    return _API_KEYS.get(key_hash)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Extract tenant_id from request and add to request.state
    
    Supports multiple extraction methods:
    1. API Key in Authorization header: "Bearer <api_key>"
    2. Tenant-ID header
    3. Subdomain: {tenant}.example.com
    4. Query parameter: ?tenant_id=xxx
    
    Usage:
        app.add_middleware(TenantContextMiddleware)
        
        # In route handlers:
        @app.get("/api/v1/data")
        async def get_data(request: Request):
            tenant_id = request.state.tenant_id
            # Use tenant_id for filtering
    """
    
    def __init__(self, app, require_tenant: bool = False):
        super().__init__(app)
        self.require_tenant = require_tenant
    
    async def dispatch(self, request: Request, call_next):
        tenant_id = None
        tenant_name = None
        
        # Skip tenant extraction for public endpoints
        if self._is_public_endpoint(request.url.path):
            request.state.tenant_id = None
            request.state.tenant_name = None
            return await call_next(request)
        
        # Method 1: Extract from Authorization header (API Key)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            api_key = auth_header.replace("Bearer ", "").strip()
            tenant_info = get_tenant_from_api_key(api_key)
            if tenant_info and tenant_info.get("is_active"):
                tenant_id = tenant_info["tenant_id"]
                tenant_name = tenant_info.get("tenant_name", "")
                logger.debug(f"Tenant identified from API key: {tenant_id}")
        
        # Method 2: Extract from Tenant-ID header
        if not tenant_id:
            tenant_id = request.headers.get("X-Tenant-ID") or request.headers.get("Tenant-ID")
            if tenant_id:
                logger.debug(f"Tenant identified from header: {tenant_id}")
        
        # Method 3: Extract from subdomain
        if not tenant_id:
            host = request.headers.get("host", "")
            if "." in host:
                subdomain = host.split(".")[0]
                # Check if subdomain is not 'www', 'api', etc.
                if subdomain not in ["www", "api", "app", "localhost"]:
                    tenant_id = subdomain
                    logger.debug(f"Tenant identified from subdomain: {tenant_id}")
        
        # Method 4: Extract from query parameter (fallback for testing)
        if not tenant_id:
            tenant_id = request.query_params.get("tenant_id")
            if tenant_id:
                logger.debug(f"Tenant identified from query param: {tenant_id}")
        
        # Check if tenant is required
        if self.require_tenant and not tenant_id:
            logger.warning(f"Tenant required but not found for: {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Tenant identification required",
                    "message": "Please provide valid API key or Tenant-ID header"
                }
            )
        
        # Add tenant context to request state
        request.state.tenant_id = tenant_id
        request.state.tenant_name = tenant_name or tenant_id
        
        # Log tenant context
        if tenant_id:
            logger.debug(f"Request from tenant: {tenant_id} -> {request.method} {request.url.path}")
        
        # Continue processing
        response: Response = await call_next(request)
        
        # Add tenant info to response headers (for debugging)
        if tenant_id and os.getenv("DEBUG_TENANT_HEADERS", "false").lower() == "true":
            response.headers["X-Tenant-ID"] = tenant_id
        
        return response
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public (no tenant required)"""
        public_paths = [
            "/",
            "/api/health",
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json",
            "/metrics",
            "/api/v1/cache/stats",
            "/favicon.ico"
        ]
        
        # Exact matches
        if path in public_paths:
            return True
        
        # Prefix matches
        public_prefixes = [
            "/static/",
            "/docs",
            "/redoc"
        ]
        for prefix in public_prefixes:
            if path.startswith(prefix):
                return True
        
        return False


def get_tenant_id(request: Request) -> Optional[str]:
    """
    Helper function to get tenant_id from request
    
    Usage:
        from middleware.tenant_context import get_tenant_id
        
        @app.get("/api/v1/users")
        async def get_users(request: Request):
            tenant_id = get_tenant_id(request)
            if not tenant_id:
                raise HTTPException(status_code=401, detail="Tenant required")
            # Query users for this tenant only
            users = db.query(User).filter(User.tenant_id == tenant_id).all()
    """
    return getattr(request.state, "tenant_id", None)


def require_tenant(request: Request) -> str:
    """
    Helper function that requires tenant_id to be present
    
    Usage:
        from middleware.tenant_context import require_tenant
        
        @app.get("/api/v1/users")
        async def get_users(request: Request):
            tenant_id = require_tenant(request)  # Raises HTTPException if missing
            users = db.query(User).filter(User.tenant_id == tenant_id).all()
    """
    tenant_id = get_tenant_id(request)
    if not tenant_id:
        raise HTTPException(
            status_code=401,
            detail="Tenant identification required. Please provide valid API key or Tenant-ID header."
        )
    return tenant_id


# Example tenant limits configuration
TENANT_LIMITS = {
    "free": {
        "max_users": 5,
        "max_api_calls_per_hour": 100,
        "max_api_calls_per_month": 1000,
        "max_storage_gb": 1,
        "features": {
            "ai_intelligence": False,
            "growth_engine": False,
            "priority_support": False
        }
    },
    "starter": {
        "max_users": 10,
        "max_api_calls_per_hour": 500,
        "max_api_calls_per_month": 10000,
        "max_storage_gb": 5,
        "features": {
            "ai_intelligence": True,
            "growth_engine": False,
            "priority_support": False
        }
    },
    "professional": {
        "max_users": 50,
        "max_api_calls_per_hour": 2000,
        "max_api_calls_per_month": 50000,
        "max_storage_gb": 20,
        "features": {
            "ai_intelligence": True,
            "growth_engine": True,
            "priority_support": False
        }
    },
    "enterprise": {
        "max_users": -1,  # unlimited
        "max_api_calls_per_hour": 10000,
        "max_api_calls_per_month": 500000,
        "max_storage_gb": 100,
        "features": {
            "ai_intelligence": True,
            "growth_engine": True,
            "priority_support": True
        }
    }
}


def get_tenant_limits(tier: str = "free") -> dict:
    """Get limits for a tenant tier"""
    return TENANT_LIMITS.get(tier, TENANT_LIMITS["free"])


# Initialize some demo API keys for testing
# In production, load from database
def init_demo_api_keys():
    """Initialize demo API keys for testing"""
    register_api_key("demo-key-tenant-a", "tenant-a", "Acme Corp")
    register_api_key("demo-key-tenant-b", "tenant-b", "Beta Industries")
    register_api_key("demo-key-tenant-c", "tenant-c", "Gamma Solutions")
    logger.info("✅ Demo API keys initialized")


# Example usage in routes:
"""
from fastapi import Request, HTTPException
from middleware.tenant_context import get_tenant_id, require_tenant

@app.get("/api/v1/users")
async def get_users(request: Request, db: Session = Depends(get_db)):
    # Option 1: Optional tenant (works with or without tenant)
    tenant_id = get_tenant_id(request)
    if tenant_id:
        users = db.query(User).filter(User.tenant_id == tenant_id).all()
    else:
        users = []  # No tenant, return empty or public data
    
    return {"users": users}


@app.get("/api/v1/dashboard")
async def get_dashboard(request: Request):
    # Option 2: Required tenant (raises 401 if missing)
    tenant_id = require_tenant(request)
    
    # Fetch tenant-specific data
    data = fetch_dashboard_data(tenant_id)
    return data


@app.post("/api/v1/data")
async def create_data(request: Request, item: Item):
    tenant_id = require_tenant(request)
    
    # Auto-inject tenant_id into new records
    item_dict = item.dict()
    item_dict['tenant_id'] = tenant_id
    
    # Save to database
    db_item = DBItem(**item_dict)
    db.add(db_item)
    db.commit()
    
    return {"id": db_item.id, "tenant_id": tenant_id}
"""
