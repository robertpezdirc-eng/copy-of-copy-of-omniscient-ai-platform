"""
Marketplace Models
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from enum import Enum


class ListingStatus(str, Enum):
    """Marketplace listing status"""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class MarketplaceListing(BaseModel):
    """Marketplace listing (API/Agent/Template)"""
    id: str
    tenant_id: str
    title: str
    description: str
    category: str
    price: float
    currency: str = "EUR"
    status: ListingStatus
    rating: float = 0.0
    reviews_count: int = 0
    sales_count: int = 0
    created_at: datetime
    updated_at: datetime


class APIKey(BaseModel):
    """API Key for marketplace access"""
    id: str
    tenant_id: str
    listing_id: str
    key_hash: str
    scopes: List[str]
    rate_limit: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True


class Usage(BaseModel):
    """API usage tracking"""
    id: str
    api_key_id: str
    tenant_id: str
    endpoint: str
    method: str
    status_code: int
    response_time_ms: int
    timestamp: datetime
