"""
Notification Models
"""

from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, EmailStr
from enum import Enum


class NotificationType(str, Enum):
    """Notification types"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationStatus(str, Enum):
    """Notification status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


class Notification(BaseModel):
    """Notification"""
    id: str
    tenant_id: str
    user_id: str
    type: NotificationType
    title: str
    body: str
    status: NotificationStatus
    data: Dict = {}
    created_at: datetime
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None


class EmailTemplate(BaseModel):
    """Email template"""
    id: str
    tenant_id: Optional[str] = None  # None = global template
    name: str
    subject: str
    html_body: str
    text_body: Optional[str] = None
    variables: List[str] = []
    created_at: datetime
    updated_at: datetime


class SMSTemplate(BaseModel):
    """SMS template"""
    id: str
    tenant_id: Optional[str] = None
    name: str
    body: str
    variables: List[str] = []
    created_at: datetime
    updated_at: datetime
