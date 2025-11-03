"""
Multi-tenant SaaS Routes - Complete Tenant Management
Handles tenant CRUD, isolation, billing, and resource limits
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Header
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid
import hashlib
import secrets

from models.tenant import (
    TenantCreate, TenantUpdate, Tenant, TenantStats, 
    TenantLimits, TenantTier, TenantStatus, TenantAPIKey
)
from database import get_redis, CacheManager

router = APIRouter()

# In-memory storage for demo (replace with database in production)
_tenants_db = {}
_tenant_stats_db = {}
_tenant_api_keys_db = {}


def _get_tenant_limits(tier: TenantTier) -> dict:
    """Get resource limits based on tenant tier"""
    limits = {
        TenantTier.FREE: {
            "max_users": 5,
            "max_ai_agents": 1,
            "max_api_calls_per_month": 1000,
            "max_storage_gb": 1,
            "features": {
                "ai_intelligence": False,
                "growth_engine": False,
                "marketplace": False,
                "white_label": False,
                "custom_domain": False,
                "priority_support": False,
                "sso": False,
                "audit_logs": False,
            }
        },
        TenantTier.STARTER: {
            "max_users": 10,
            "max_ai_agents": 3,
            "max_api_calls_per_month": 10000,
            "max_storage_gb": 10,
            "features": {
                "ai_intelligence": True,
                "growth_engine": False,
                "marketplace": True,
                "white_label": False,
                "custom_domain": False,
                "priority_support": False,
                "sso": False,
                "audit_logs": True,
            }
        },
        TenantTier.PROFESSIONAL: {
            "max_users": 50,
            "max_ai_agents": 10,
            "max_api_calls_per_month": 100000,
            "max_storage_gb": 100,
            "features": {
                "ai_intelligence": True,
                "growth_engine": True,
                "marketplace": True,
                "white_label": False,
                "custom_domain": True,
                "priority_support": True,
                "sso": True,
                "audit_logs": True,
            }
        },
        TenantTier.ENTERPRISE: {
            "max_users": 500,
            "max_ai_agents": 50,
            "max_api_calls_per_month": 1000000,
            "max_storage_gb": 1000,
            "features": {
                "ai_intelligence": True,
                "growth_engine": True,
                "marketplace": True,
                "white_label": True,
                "custom_domain": True,
                "priority_support": True,
                "sso": True,
                "audit_logs": True,
            }
        },
        TenantTier.WHITE_LABEL: {
            "max_users": -1,  # unlimited
            "max_ai_agents": -1,
            "max_api_calls_per_month": -1,
            "max_storage_gb": -1,
            "features": {
                "ai_intelligence": True,
                "growth_engine": True,
                "marketplace": True,
                "white_label": True,
                "custom_domain": True,
                "priority_support": True,
                "sso": True,
                "audit_logs": True,
            }
        }
    }
    return limits.get(tier, limits[TenantTier.FREE])


def _verify_tenant_header(x_tenant_id: Optional[str] = Header(None)) -> str:
    """Middleware to verify tenant ID from header"""
    if not x_tenant_id:
        raise HTTPException(status_code=401, detail="X-Tenant-ID header required")
    if x_tenant_id not in _tenants_db:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return x_tenant_id


@router.post("/tenants", response_model=Tenant, status_code=201)
async def create_tenant(tenant_data: TenantCreate):
    """Create a new tenant with trial period"""
    
    # Check if slug already exists
    for tenant in _tenants_db.values():
        if tenant["slug"] == tenant_data.slug:
            raise HTTPException(status_code=400, detail="Tenant slug already exists")
    
    tenant_id = f"tenant_{uuid.uuid4().hex[:16]}"
    now = datetime.now(timezone.utc)
    
    limits = _get_tenant_limits(tenant_data.tier)
    
    tenant = {
        "id": tenant_id,
        "name": tenant_data.name,
        "slug": tenant_data.slug,
        "domain": tenant_data.domain,
        "tier": tenant_data.tier,
        "status": TenantStatus.TRIAL,
        "created_at": now,
        "updated_at": now,
        "trial_ends_at": now + timedelta(days=14),
        "subscription_id": None,
        **limits,
        "branding": {},
        "settings": {}
    }
    
    _tenants_db[tenant_id] = tenant
    
    # Initialize stats
    _tenant_stats_db[tenant_id] = {
        "tenant_id": tenant_id,
        "current_users": 0,
        "current_ai_agents": 0,
        "api_calls_this_month": 0,
        "storage_used_gb": 0.0,
        "total_revenue": 0.0,
        "created_at": now
    }
    
    return Tenant(**tenant)


@router.get("/tenants", response_model=List[Tenant])
async def list_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    tier: Optional[TenantTier] = None,
    status: Optional[TenantStatus] = None
):
    """List all tenants with optional filtering"""
    
    tenants = list(_tenants_db.values())
    
    # Apply filters
    if tier:
        tenants = [t for t in tenants if t["tier"] == tier]
    if status:
        tenants = [t for t in tenants if t["status"] == status]
    
    # Apply pagination
    tenants = tenants[skip:skip + limit]
    
    return [Tenant(**t) for t in tenants]


@router.get("/tenants/{tenant_id}", response_model=Tenant)
async def get_tenant(tenant_id: str):
    """Get tenant details by ID"""
    
    if tenant_id not in _tenants_db:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return Tenant(**_tenants_db[tenant_id])


@router.patch("/tenants/{tenant_id}", response_model=Tenant)
async def update_tenant(tenant_id: str, update_data: TenantUpdate):
    """Update tenant configuration"""
    
    if tenant_id not in _tenants_db:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    tenant = _tenants_db[tenant_id]
    update_dict = update_data.dict(exclude_unset=True)
    
    # Update limits if tier changed
    if "tier" in update_dict:
        new_tier = update_dict["tier"]
        limits = _get_tenant_limits(new_tier)
        tenant.update(limits)
    
    tenant.update(update_dict)
    tenant["updated_at"] = datetime.now(timezone.utc)
    
    return Tenant(**tenant)


@router.delete("/tenants/{tenant_id}", status_code=204)
async def delete_tenant(tenant_id: str):
    """Delete tenant (soft delete by setting status to CANCELLED)"""
    
    if tenant_id not in _tenants_db:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    _tenants_db[tenant_id]["status"] = TenantStatus.CANCELLED
    _tenants_db[tenant_id]["updated_at"] = datetime.now(timezone.utc)
    
    return None


@router.get("/tenants/{tenant_id}/stats", response_model=TenantStats)
async def get_tenant_stats(tenant_id: str):
    """Get tenant usage statistics"""
    
    if tenant_id not in _tenants_db:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    if tenant_id not in _tenant_stats_db:
        # Initialize empty stats
        _tenant_stats_db[tenant_id] = {
            "tenant_id": tenant_id,
            "current_users": 0,
            "current_ai_agents": 0,
            "api_calls_this_month": 0,
            "storage_used_gb": 0.0,
            "total_revenue": 0.0,
            "created_at": datetime.now(timezone.utc)
        }
    
    return TenantStats(**_tenant_stats_db[tenant_id])


@router.get("/tenants/{tenant_id}/limits", response_model=TenantLimits)
async def get_tenant_limits(tenant_id: str):
    """Get tenant resource limits and current usage"""
    
    if tenant_id not in _tenants_db:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    tenant = _tenants_db[tenant_id]
    stats = _tenant_stats_db.get(tenant_id, {
        "current_users": 0,
        "current_ai_agents": 0,
        "api_calls_this_month": 0,
        "storage_used_gb": 0.0
    })
    
    max_users = tenant["max_users"]
    max_ai_agents = tenant["max_ai_agents"]
    max_api_calls = tenant["max_api_calls_per_month"]
    max_storage = tenant["max_storage_gb"]
    
    return TenantLimits(
        tenant_id=tenant_id,
        tier=tenant["tier"],
        max_users=max_users,
        current_users=stats["current_users"],
        users_remaining=max_users - stats["current_users"] if max_users > 0 else -1,
        max_ai_agents=max_ai_agents,
        current_ai_agents=stats["current_ai_agents"],
        ai_agents_remaining=max_ai_agents - stats["current_ai_agents"] if max_ai_agents > 0 else -1,
        max_api_calls_per_month=max_api_calls,
        api_calls_this_month=stats["api_calls_this_month"],
        api_calls_remaining=max_api_calls - stats["api_calls_this_month"] if max_api_calls > 0 else -1,
        max_storage_gb=max_storage,
        storage_used_gb=stats["storage_used_gb"],
        storage_remaining_gb=max_storage - stats["storage_used_gb"] if max_storage > 0 else -1,
        features=tenant["features"]
    )


@router.post("/tenants/{tenant_id}/api-keys", response_model=TenantAPIKey)
async def create_tenant_api_key(
    tenant_id: str,
    name: str = Query(..., min_length=1, max_length=255),
    scopes: List[str] = Query(default=[]),
    rate_limit: int = Query(1000, ge=100, le=1000000),
    expires_days: Optional[int] = Query(None, ge=1, le=365)
):
    """Create a new API key for tenant"""
    
    if tenant_id not in _tenants_db:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Generate API key
    api_key = f"sk_{tenant_id[:8]}_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    key_id = f"key_{uuid.uuid4().hex[:16]}"
    now = datetime.now(timezone.utc)
    
    api_key_data = {
        "id": key_id,
        "tenant_id": tenant_id,
        "name": name,
        "key_prefix": api_key[:16],
        "key_hash": key_hash,
        "scopes": scopes,
        "rate_limit": rate_limit,
        "expires_at": now + timedelta(days=expires_days) if expires_days else None,
        "created_at": now,
        "last_used_at": None,
        "is_active": True
    }
    
    _tenant_api_keys_db[key_id] = api_key_data
    
    # Return the key only on creation (never shown again)
    result = TenantAPIKey(**api_key_data)
    result.key_hash = api_key  # Temporarily replace hash with actual key for response
    
    return result


@router.get("/tenants/{tenant_id}/api-keys", response_model=List[TenantAPIKey])
async def list_tenant_api_keys(tenant_id: str):
    """List all API keys for tenant"""
    
    if tenant_id not in _tenants_db:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    keys = [k for k in _tenant_api_keys_db.values() if k["tenant_id"] == tenant_id]
    return [TenantAPIKey(**k) for k in keys]


@router.delete("/tenants/{tenant_id}/api-keys/{key_id}", status_code=204)
async def revoke_tenant_api_key(tenant_id: str, key_id: str):
    """Revoke a tenant API key"""
    
    if tenant_id not in _tenants_db:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    if key_id not in _tenant_api_keys_db:
        raise HTTPException(status_code=404, detail="API key not found")
    
    if _tenant_api_keys_db[key_id]["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="API key does not belong to this tenant")
    
    _tenant_api_keys_db[key_id]["is_active"] = False
    
    return None


@router.post("/tenants/{tenant_id}/usage/track")
async def track_tenant_usage(
    tenant_id: str,
    api_calls: int = Query(1, ge=0),
    storage_delta_gb: float = Query(0.0)
):
    """Track tenant resource usage (called by internal services)"""
    
    if tenant_id not in _tenants_db:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    if tenant_id not in _tenant_stats_db:
        _tenant_stats_db[tenant_id] = {
            "tenant_id": tenant_id,
            "current_users": 0,
            "current_ai_agents": 0,
            "api_calls_this_month": 0,
            "storage_used_gb": 0.0,
            "total_revenue": 0.0,
            "created_at": datetime.now(timezone.utc)
        }
    
    stats = _tenant_stats_db[tenant_id]
    stats["api_calls_this_month"] += api_calls
    stats["storage_used_gb"] += storage_delta_gb
    
    # Check if limits exceeded
    tenant = _tenants_db[tenant_id]
    max_api_calls = tenant["max_api_calls_per_month"]
    max_storage = tenant["max_storage_gb"]
    
    if max_api_calls > 0 and stats["api_calls_this_month"] > max_api_calls:
        return {
            "status": "limit_exceeded",
            "limit_type": "api_calls",
            "current": stats["api_calls_this_month"],
            "max": max_api_calls
        }
    
    if max_storage > 0 and stats["storage_used_gb"] > max_storage:
        return {
            "status": "limit_exceeded",
            "limit_type": "storage",
            "current": stats["storage_used_gb"],
            "max": max_storage
        }
    
    return {
        "status": "ok",
        "api_calls_remaining": max_api_calls - stats["api_calls_this_month"] if max_api_calls > 0 else -1,
        "storage_remaining_gb": max_storage - stats["storage_used_gb"] if max_storage > 0 else -1
    }
