"""
Analytics Models
"""

from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel


class AnalyticsEvent(BaseModel):
    """Analytics event"""
    id: str
    tenant_id: str
    user_id: Optional[str] = None
    event_type: str
    event_name: str
    properties: Dict = {}
    timestamp: datetime
    session_id: Optional[str] = None
    page_url: Optional[str] = None
    referrer: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None


class UserBehavior(BaseModel):
    """User behavior tracking"""
    id: str
    user_id: str
    tenant_id: str
    action: str
    context: Dict = {}
    timestamp: datetime


class MetricSnapshot(BaseModel):
    """Metric snapshot"""
    id: str
    tenant_id: str
    metric_name: str
    metric_value: float
    dimensions: Dict = {}
    timestamp: datetime
    period: str  # hour, day, week, month
