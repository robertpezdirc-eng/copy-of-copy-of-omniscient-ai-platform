"""
Subscription & Payment Models
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class SubscriptionStatus(str, Enum):
    """Subscription status"""
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentStatus(str, Enum):
    """Payment status"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class SubscriptionPlan(BaseModel):
    """Subscription plan"""
    id: str
    name: str
    description: str
    price: float
    currency: str = "EUR"
    interval: str = "month"  # month, year
    trial_days: int = 14
    features: dict = {}
    limits: dict = {}
    stripe_price_id: Optional[str] = None
    paypal_plan_id: Optional[str] = None


class Subscription(BaseModel):
    """Subscription model"""
    id: str
    tenant_id: str
    plan_id: str
    status: SubscriptionStatus
    current_period_start: datetime
    current_period_end: datetime
    trial_end: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    stripe_subscription_id: Optional[str] = None
    paypal_subscription_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class Payment(BaseModel):
    """Payment transaction"""
    id: str
    tenant_id: str
    subscription_id: Optional[str] = None
    amount: float
    currency: str = "EUR"
    status: PaymentStatus
    payment_method: str  # stripe, paypal, crypto
    payment_method_details: dict = {}
    invoice_id: Optional[str] = None
    receipt_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
