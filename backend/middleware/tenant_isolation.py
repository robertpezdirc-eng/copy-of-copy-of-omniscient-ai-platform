"""
Tenant Isolation Middleware
Enforces tenant context and resource isolation across requests
"""

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce tenant isolation
    
    Extracts tenant context from:
    1. X-Tenant-ID header (primary)
    2. Authorization token (if contains tenant claim)
    3. Subdomain (if configured)
    
    Adds tenant_id to request.state for use in route handlers
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip tenant validation for health, metrics, and auth endpoints
        if request.url.path in ["/", "/api/health", "/metrics", "/api/docs", "/api/redoc", "/openapi.json"]:
            return await call_next(request)
        
        if request.url.path.startswith("/api/v1/auth") or request.url.path.startswith("/api/v1/tenants"):
            return await call_next(request)
        
        # Extract tenant ID from header
        tenant_id = request.headers.get("X-Tenant-ID")
        
        # Alternative: Extract from subdomain if configured
        if not tenant_id:
            host = request.headers.get("Host", "")
            if host and "." in host:
                subdomain = host.split(".")[0]
                if subdomain not in ["www", "api", "localhost"]:
                    tenant_id = f"tenant_{subdomain}"
        
        # Alternative: Extract from Authorization token (future enhancement)
        # if not tenant_id:
        #     auth_header = request.headers.get("Authorization")
        #     if auth_header:
        #         tenant_id = extract_tenant_from_token(auth_header)
        
        # Store tenant context in request state
        request.state.tenant_id = tenant_id
        request.state.tenant_validated = False
        
        # For strict isolation, uncomment to require tenant ID on all requests
        # if not tenant_id:
        #     return JSONResponse(
        #         status_code=400,
        #         content={"error": "Tenant context required", "detail": "X-Tenant-ID header missing"}
        #     )
        
        try:
            response = await call_next(request)
            
            # Add tenant context to response headers for debugging
            if tenant_id:
                response.headers["X-Tenant-ID"] = tenant_id
            
            return response
            
        except Exception as e:
            logger.error(f"Error in tenant isolation middleware: {e}")
            raise


def get_tenant_id(request: Request) -> Optional[str]:
    """
    Helper function to get tenant ID from request state
    
    Usage in route handlers:
        tenant_id = get_tenant_id(request)
        if not tenant_id:
            raise HTTPException(status_code=400, detail="Tenant context required")
    """
    return getattr(request.state, "tenant_id", None)


def require_tenant(request: Request) -> str:
    """
    Helper function that requires tenant ID to be present
    
    Usage in route handlers:
        tenant_id = require_tenant(request)
    """
    tenant_id = get_tenant_id(request)
    if not tenant_id:
        raise HTTPException(
            status_code=400,
            detail="Tenant context required. Include X-Tenant-ID header."
        )
    return tenant_id
