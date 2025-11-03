"""
Database Models for OMNI Enterprise Ultra Max

All Pydantic models and SQLAlchemy ORM models
"""

from .user import User, UserCreate, UserUpdate, UserInDB
from .tenant import Tenant, TenantCreate, TenantUpdate
from .subscription import Subscription, SubscriptionPlan, Payment
from .affiliate import Affiliate, AffiliateLink, Commission, Payout
from .ai_agent import AIAgent, AgentConfig, AgentInteraction
from .analytics import AnalyticsEvent, UserBehavior, MetricSnapshot
from .marketplace import MarketplaceListing, APIKey, Usage
from .notification import Notification, EmailTemplate, SMSTemplate

__all__ = [
    # User models
    "User",
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    # Tenant models
    "Tenant",
    "TenantCreate",
    "TenantUpdate",
    # Subscription models
    "Subscription",
    "SubscriptionPlan",
    "Payment",
    # Affiliate models
    "Affiliate",
    "AffiliateLink",
    "Commission",
    "Payout",
    # AI Agent models
    "AIAgent",
    "AgentConfig",
    "AgentInteraction",
    # Analytics models
    "AnalyticsEvent",
    "UserBehavior",
    "MetricSnapshot",
    # Marketplace models
    "MarketplaceListing",
    "APIKey",
    "Usage",
    # Notification models
    "Notification",
    "EmailTemplate",
    "SMSTemplate",
]
