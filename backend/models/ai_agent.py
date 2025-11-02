"""
AI Agent Models
"""

from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel
from enum import Enum


class AgentType(str, Enum):
    """AI Agent types"""
    SUPPORT = "support"
    SALES = "sales"
    ANALYTICS = "analytics"
    CONTENT = "content"
    CUSTOM = "custom"


class AgentStatus(str, Enum):
    """Agent status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRAINING = "training"
    ERROR = "error"


class AIAgent(BaseModel):
    """AI Agent model"""
    id: str
    tenant_id: str
    name: str
    agent_type: AgentType
    status: AgentStatus
    description: Optional[str] = None
    config: Dict = {}
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000
    created_at: datetime
    updated_at: datetime


class AgentConfig(BaseModel):
    """Agent configuration"""
    agent_id: str
    system_prompt: str
    context_window: int = 4096
    response_format: str = "text"
    tools: List[str] = []
    integrations: Dict = {}
    knowledge_base: List[str] = []
    fallback_behavior: str = "escalate"


class AgentInteraction(BaseModel):
    """Agent interaction log"""
    id: str
    agent_id: str
    tenant_id: str
    user_id: Optional[str] = None
    session_id: str
    input_text: str
    output_text: str
    tokens_used: int
    cost: float
    latency_ms: int
    feedback: Optional[str] = None
    metadata: Dict = {}
    created_at: datetime
