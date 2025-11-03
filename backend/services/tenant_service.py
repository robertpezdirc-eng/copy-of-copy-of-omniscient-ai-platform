"""
Multi-Tenant SaaS Service
Provides tenant isolation, management, and context handling
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)


class SubscriptionTier(str, Enum):
    """Subscription tiers for monetization"""
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class TenantStatus(str, Enum):
    """Tenant account status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"


class Tenant:
    """Tenant model for multi-tenant SaaS"""
    
    def __init__(
        self,
        tenant_id: str,
        name: str,
        subscription_tier: SubscriptionTier,
        status: TenantStatus = TenantStatus.ACTIVE,
        created_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.tenant_id = tenant_id
        self.name = name
        self.subscription_tier = subscription_tier
        self.status = status
        self.created_at = created_at or datetime.now(timezone.utc)
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert tenant to dictionary"""
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "subscription_tier": self.subscription_tier.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Tenant":
        """Create tenant from dictionary"""
        return cls(
            tenant_id=data["tenant_id"],
            name=data["name"],
            subscription_tier=SubscriptionTier(data["subscription_tier"]),
            status=TenantStatus(data.get("status", "active")),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else None,
            metadata=data.get("metadata", {})
        )


class TenantFeatures:
    """Feature flags and limits per subscription tier"""
    
    FEATURES = {
        SubscriptionTier.BASIC: {
            "max_api_calls_per_day": 1000,
            "max_users": 5,
            "max_storage_gb": 1,
            "ai_assistant": False,
            "advanced_analytics": False,
            "priority_support": False,
            "custom_domain": False,
            "white_label": False,
            "sla_guarantee": False,
            "rate_limit_per_minute": 10,
        },
        SubscriptionTier.PRO: {
            "max_api_calls_per_day": 10000,
            "max_users": 50,
            "max_storage_gb": 10,
            "ai_assistant": True,
            "advanced_analytics": True,
            "priority_support": True,
            "custom_domain": True,
            "white_label": False,
            "sla_guarantee": "99.9%",
            "rate_limit_per_minute": 100,
        },
        SubscriptionTier.ENTERPRISE: {
            "max_api_calls_per_day": -1,  # Unlimited
            "max_users": -1,  # Unlimited
            "max_storage_gb": -1,  # Unlimited
            "ai_assistant": True,
            "advanced_analytics": True,
            "priority_support": True,
            "custom_domain": True,
            "white_label": True,
            "sla_guarantee": "99.99%",
            "rate_limit_per_minute": -1,  # Unlimited
            "dedicated_support": True,
            "custom_integrations": True,
        }
    }
    
    @classmethod
    def get_features(cls, tier: SubscriptionTier) -> Dict[str, Any]:
        """Get features for a subscription tier"""
        return cls.FEATURES.get(tier, cls.FEATURES[SubscriptionTier.BASIC])
    
    @classmethod
    def has_feature(cls, tier: SubscriptionTier, feature: str) -> bool:
        """Check if tier has a specific feature"""
        features = cls.get_features(tier)
        return features.get(feature, False)


class TenantService:
    """Service for managing multi-tenant operations"""
    
    def __init__(self, redis_client=None, db_client=None):
        self.redis = redis_client
        self.db = db_client
        self._tenant_cache: Dict[str, Tenant] = {}
        
    async def create_tenant(
        self,
        name: str,
        subscription_tier: SubscriptionTier,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tenant:
        """Create a new tenant"""
        tenant_id = f"tenant_{uuid.uuid4().hex[:16]}"
        
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            subscription_tier=subscription_tier,
            status=TenantStatus.TRIAL if subscription_tier == SubscriptionTier.BASIC else TenantStatus.ACTIVE,
            metadata=metadata or {}
        )
        
        # Store in cache
        self._tenant_cache[tenant_id] = tenant
        
        # Store in Redis if available
        if self.redis:
            try:
                await self.redis.setex(
                    f"tenant:{tenant_id}",
                    3600,  # 1 hour TTL
                    str(tenant.to_dict())
                )
            except Exception as e:
                logger.warning(f"Failed to cache tenant in Redis: {e}")
        
        # Store in database if available
        if self.db:
            try:
                # Store in database (implementation depends on DB type)
                pass
            except Exception as e:
                logger.warning(f"Failed to store tenant in DB: {e}")
        
        logger.info(f"Created tenant: {tenant_id} ({name}) with {subscription_tier.value} tier")
        return tenant
    
    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        # Check memory cache first
        if tenant_id in self._tenant_cache:
            return self._tenant_cache[tenant_id]
        
        # Check Redis cache
        if self.redis:
            try:
                cached = await self.redis.get(f"tenant:{tenant_id}")
                if cached:
                    tenant_dict = eval(cached)  # Safe in this context
                    tenant = Tenant.from_dict(tenant_dict)
                    self._tenant_cache[tenant_id] = tenant
                    return tenant
            except Exception as e:
                logger.warning(f"Failed to get tenant from Redis: {e}")
        
        # Check database
        if self.db:
            try:
                # Fetch from database (implementation depends on DB type)
                pass
            except Exception as e:
                logger.warning(f"Failed to get tenant from DB: {e}")
        
        return None
    
    async def update_tenant(
        self,
        tenant_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Tenant]:
        """Update tenant information"""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return None
        
        # Update tenant fields
        for key, value in updates.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)
        
        # Update cache
        self._tenant_cache[tenant_id] = tenant
        
        # Update Redis
        if self.redis:
            try:
                await self.redis.setex(
                    f"tenant:{tenant_id}",
                    3600,
                    str(tenant.to_dict())
                )
            except Exception as e:
                logger.warning(f"Failed to update tenant in Redis: {e}")
        
        logger.info(f"Updated tenant: {tenant_id}")
        return tenant
    
    async def upgrade_subscription(
        self,
        tenant_id: str,
        new_tier: SubscriptionTier
    ) -> Optional[Tenant]:
        """Upgrade tenant subscription tier"""
        return await self.update_tenant(tenant_id, {
            "subscription_tier": new_tier,
            "status": TenantStatus.ACTIVE
        })
    
    async def suspend_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Suspend a tenant"""
        return await self.update_tenant(tenant_id, {"status": TenantStatus.SUSPENDED})
    
    async def activate_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Activate a tenant"""
        return await self.update_tenant(tenant_id, {"status": TenantStatus.ACTIVE})
    
    def get_tenant_features(self, tenant: Tenant) -> Dict[str, Any]:
        """Get features available to a tenant"""
        return TenantFeatures.get_features(tenant.subscription_tier)
    
    def check_feature_access(self, tenant: Tenant, feature: str) -> bool:
        """Check if tenant has access to a feature"""
        return TenantFeatures.has_feature(tenant.subscription_tier, feature)
    
    async def get_tenant_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant usage statistics"""
        # This would query usage from monitoring/analytics
        return {
            "api_calls_today": 0,
            "storage_used_gb": 0,
            "active_users": 0,
            "last_active": datetime.now(timezone.utc).isoformat()
        }
    
    async def list_tenants(
        self,
        status: Optional[TenantStatus] = None,
        tier: Optional[SubscriptionTier] = None,
        limit: int = 100
    ) -> List[Tenant]:
        """List tenants with optional filtering"""
        tenants = list(self._tenant_cache.values())
        
        if status:
            tenants = [t for t in tenants if t.status == status]
        
        if tier:
            tenants = [t for t in tenants if t.subscription_tier == tier]
        
        return tenants[:limit]


# Global tenant service instance
_tenant_service: Optional[TenantService] = None


def get_tenant_service(redis_client=None, db_client=None) -> TenantService:
    """Get or create tenant service instance"""
    global _tenant_service
    if _tenant_service is None:
        _tenant_service = TenantService(redis_client, db_client)
    return _tenant_service
