"""
Tenant Models - Multi-tenancy Support
"""

from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from enum import Enum


class TenantTier(str, Enum):
    """Tenant subscription tiers"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    WHITE_LABEL = "white_label"


class TenantStatus(str, Enum):
    """Tenant status"""
    ACTIVE = "active"
    TRIAL = "trial"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class TenantBase(BaseModel):
    """Base tenant model"""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., pattern="^[a-z0-9-]+$")
    domain: Optional[str] = None
    tier: TenantTier = TenantTier.FREE
    status: TenantStatus = TenantStatus.TRIAL


class TenantCreate(TenantBase):
    """Tenant creation model"""
    owner_email: str
    owner_name: str


class TenantUpdate(BaseModel):
    """Tenant update model"""
    name: Optional[str] = None
    domain: Optional[str] = None
    tier: Optional[TenantTier] = None
    status: Optional[TenantStatus] = None
    settings: Optional[Dict] = None


class Tenant(TenantBase):
    """Tenant response model"""
    id: str
    created_at: datetime
    updated_at: datetime
    trial_ends_at: Optional[datetime] = None
    subscription_id: Optional[str] = None
    
    # Limits based on tier
    max_users: int = 5
    max_ai_agents: int = 1
    max_api_calls_per_month: int = 1000
    max_storage_gb: int = 1
    
    # Features enabled
    features: Dict[str, bool] = {
        "ai_intelligence": False,
        "growth_engine": False,
        "marketplace": False,
        "white_label": False,
        "custom_domain": False,
        "priority_support": False,
        "sso": False,
        "audit_logs": False,
    }
    
    # Branding (for white-label)
    branding: Dict[str, str] = {}
    
    # Settings
    settings: Dict = {}
    
    class Config:
        from_attributes = True


class TenantStats(BaseModel):
    """Tenant usage statistics"""
    tenant_id: str
    current_users: int = 0
    current_ai_agents: int = 0
    api_calls_this_month: int = 0
    storage_used_gb: float = 0.0
    total_revenue: float = 0.0
    created_at: datetime


class TenantLimits(BaseModel):
    """Tenant resource limits"""
    tenant_id: str
    tier: TenantTier
    
    # User limits
    max_users: int
    current_users: int
    users_remaining: int
    
    # AI limits
    max_ai_agents: int
    current_ai_agents: int
    ai_agents_remaining: int
    
    # API limits
    max_api_calls_per_month: int
    api_calls_this_month: int
    api_calls_remaining: int
    
    # Storage limits
    max_storage_gb: int
    storage_used_gb: float
    storage_remaining_gb: float
    
    # Feature flags
    features: Dict[str, bool]


class TenantInvite(BaseModel):
    """Tenant user invitation"""
    id: str
    tenant_id: str
    email: str
    role: str
    invited_by: str
    invited_at: datetime
    expires_at: datetime
    accepted: bool = False
    accepted_at: Optional[datetime] = None


class TenantWebhook(BaseModel):
    """Tenant webhook configuration"""
    id: str
    tenant_id: str
    url: str
    events: List[str]
    secret: str
    active: bool = True
    created_at: datetime
    last_triggered_at: Optional[datetime] = None


class TenantAPIKey(BaseModel):
    """Tenant API key"""
    id: str
    tenant_id: str
    name: str
    key_prefix: str  # First 8 chars for display
    key_hash: str  # Hashed full key
    scopes: List[str] = []
    rate_limit: int = 1000  # requests per hour
    expires_at: Optional[datetime] = None
    created_at: datetime
    last_used_at: Optional[datetime] = None
    is_active: bool = True
