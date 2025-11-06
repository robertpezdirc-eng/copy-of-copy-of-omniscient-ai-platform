"""
Ticket Models
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class TicketStatus(str, Enum):
    """Ticket status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    """Ticket priority"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketBase(BaseModel):
    """Base ticket model"""
    title: str
    description: str
    status: TicketStatus = TicketStatus.OPEN
    priority: TicketPriority = TicketPriority.MEDIUM
    assignee_id: Optional[str] = None


class TicketCreate(TicketBase):
    """Ticket creation model"""
    pass


class TicketUpdate(BaseModel):
    """Ticket update model"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assignee_id: Optional[str] = None


class Ticket(TicketBase):
    """Ticket response model"""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
