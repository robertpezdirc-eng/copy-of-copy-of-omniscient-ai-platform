"""
Multi-Tenant SaaS Routes
Provides tenant management and isolation
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from database import get_redis
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class TenantCreate(BaseModel):
    """Request to create a new tenant"""
    name: str = Field(..., min_length=1, max_length=100)
    subscription_tier: str = Field(..., pattern="^(basic|pro|enterprise)$")
    metadata: Optional[Dict[str, Any]] = None


class TenantUpdate(BaseModel):
    """Request to update a tenant"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    subscription_tier: Optional[str] = Field(None, pattern="^(basic|pro|enterprise)$")
    status: Optional[str] = Field(None, pattern="^(active|suspended|trial|cancelled)$")
    metadata: Optional[Dict[str, Any]] = None


class SubscriptionUpgrade(BaseModel):
    """Request to upgrade subscription"""
    new_tier: str = Field(..., pattern="^(basic|pro|enterprise)$")


@router.post("/tenants", tags=["Multi-Tenant"])
async def create_tenant(
    request: TenantCreate,
    redis=Depends(get_redis)
):
    """Create a new tenant"""
    try:
        from services.tenant_service import get_tenant_service, SubscriptionTier
        
        service = get_tenant_service(redis_client=redis)
        tier = SubscriptionTier(request.subscription_tier)
        
        tenant = await service.create_tenant(
            name=request.name,
            subscription_tier=tier,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "tenant": tenant.to_dict(),
            "features": service.get_tenant_features(tenant)
        }
    except Exception as e:
        logger.error(f"Failed to create tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}", tags=["Multi-Tenant"])
async def get_tenant(
    tenant_id: str,
    redis=Depends(get_redis)
):
    """Get tenant information"""
    try:
        from services.tenant_service import get_tenant_service
        
        service = get_tenant_service(redis_client=redis)
        tenant = await service.get_tenant(tenant_id)
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        return {
            "tenant": tenant.to_dict(),
            "features": service.get_tenant_features(tenant),
            "usage": await service.get_tenant_usage(tenant_id)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/tenants/{tenant_id}", tags=["Multi-Tenant"])
async def update_tenant(
    tenant_id: str,
    request: TenantUpdate,
    redis=Depends(get_redis)
):
    """Update tenant information"""
    try:
        from services.tenant_service import get_tenant_service, SubscriptionTier, TenantStatus
        
        service = get_tenant_service(redis_client=redis)
        
        updates = {}
        if request.name:
            updates["name"] = request.name
        if request.subscription_tier:
            updates["subscription_tier"] = SubscriptionTier(request.subscription_tier)
        if request.status:
            updates["status"] = TenantStatus(request.status)
        if request.metadata:
            updates["metadata"] = request.metadata
        
        tenant = await service.update_tenant(tenant_id, updates)
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        return {
            "success": True,
            "tenant": tenant.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tenants/{tenant_id}/upgrade", tags=["Multi-Tenant"])
async def upgrade_subscription(
    tenant_id: str,
    request: SubscriptionUpgrade,
    redis=Depends(get_redis)
):
    """Upgrade tenant subscription"""
    try:
        from services.tenant_service import get_tenant_service, SubscriptionTier
        
        service = get_tenant_service(redis_client=redis)
        new_tier = SubscriptionTier(request.new_tier)
        
        tenant = await service.upgrade_subscription(tenant_id, new_tier)
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        return {
            "success": True,
            "tenant": tenant.to_dict(),
            "new_features": service.get_tenant_features(tenant),
            "message": f"Successfully upgraded to {new_tier.value} tier"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upgrade subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants", tags=["Multi-Tenant"])
async def list_tenants(
    status: Optional[str] = None,
    tier: Optional[str] = None,
    limit: int = 100,
    redis=Depends(get_redis)
):
    """List tenants with optional filtering"""
    try:
        from services.tenant_service import get_tenant_service, TenantStatus, SubscriptionTier
        
        service = get_tenant_service(redis_client=redis)
        
        status_filter = TenantStatus(status) if status else None
        tier_filter = SubscriptionTier(tier) if tier else None
        
        tenants = await service.list_tenants(
            status=status_filter,
            tier=tier_filter,
            limit=limit
        )
        
        return {
            "tenants": [t.to_dict() for t in tenants],
            "count": len(tenants)
        }
    except Exception as e:
        logger.error(f"Failed to list tenants: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/features", tags=["Multi-Tenant"])
async def get_tenant_features(
    tenant_id: str,
    redis=Depends(get_redis)
):
    """Get features available to a tenant"""
    try:
        from services.tenant_service import get_tenant_service
        
        service = get_tenant_service(redis_client=redis)
        tenant = await service.get_tenant(tenant_id)
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        return {
            "tenant_id": tenant_id,
            "subscription_tier": tenant.subscription_tier.value,
            "features": service.get_tenant_features(tenant)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tenant features: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/usage", tags=["Multi-Tenant"])
async def get_tenant_usage(
    tenant_id: str,
    redis=Depends(get_redis)
):
    """Get tenant usage statistics"""
    try:
        from services.tenant_service import get_tenant_service
        
        service = get_tenant_service(redis_client=redis)
        usage = await service.get_tenant_usage(tenant_id)
        
        return {
            "tenant_id": tenant_id,
            "usage": usage
        }
    except Exception as e:
        logger.error(f"Failed to get tenant usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Legacy route for backwards compatibility
@router.get("/{tid}")
def get_legacy(tid: str):
    """Legacy endpoint for backwards compatibility"""
    return {"id": tid, "message": "Use /tenants/{tenant_id} endpoint instead"}
