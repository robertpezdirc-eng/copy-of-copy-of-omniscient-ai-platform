"""
Affiliate Models
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from enum import Enum


class AffiliateTier(str, Enum):
    """Affiliate tiers"""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class AffiliateStatus(str, Enum):
    """Affiliate status"""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REJECTED = "rejected"


class Affiliate(BaseModel):
    """Affiliate model"""
    id: str
    user_id: str
    email: EmailStr
    full_name: str
    affiliate_code: str
    tier: AffiliateTier
    status: AffiliateStatus
    commission_rate: float
    total_sales: float = 0.0
    total_commission: float = 0.0
    total_referrals: int = 0
    created_at: datetime
    approved_at: Optional[datetime] = None


class AffiliateLink(BaseModel):
    """Affiliate tracking link"""
    id: str
    affiliate_id: str
    campaign_name: str
    tracking_code: str
    destination_url: str
    clicks: int = 0
    conversions: int = 0
    created_at: datetime


class Commission(BaseModel):
    """Commission record"""
    id: str
    affiliate_id: str
    referral_id: str
    order_id: str
    amount: float
    commission_amount: float
    commission_rate: float
    status: str  # pending, approved, paid
    created_at: datetime
    paid_at: Optional[datetime] = None


class Payout(BaseModel):
    """Payout record"""
    id: str
    affiliate_id: str
    amount: float
    payment_method: str
    payment_details: dict
    status: str  # pending, processing, completed, failed
    created_at: datetime
    processed_at: Optional[datetime] = None
