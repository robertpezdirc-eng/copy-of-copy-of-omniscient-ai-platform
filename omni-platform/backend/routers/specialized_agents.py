"""
Specialized AI Agents
Marketing, Finance, Healthcare, and other domain-specific AI agents
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import json
import os
import logging
import openai
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/specialized-agents", tags=["Specialized AI Agents"])

# Data storage paths
AGENTS_DATA_DIR = "data/specialized_agents"
CONVERSATIONS_FILE = os.path.join(AGENTS_DATA_DIR, "conversations.json")
AGENT_CONFIGS_FILE = os.path.join(AGENTS_DATA_DIR, "agent_configs.json")
KNOWLEDGE_BASE_FILE = os.path.join(AGENTS_DATA_DIR, "knowledge_base.json")

# Ensure data directory exists
os.makedirs(AGENTS_DATA_DIR, exist_ok=True)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "your-openai-api-key"))

class AgentType(str, Enum):
    MARKETING = "marketing"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    LEGAL = "legal"
    HR = "hr"
    SALES = "sales"
    CUSTOMER_SUCCESS = "customer_success"
    PRODUCT = "product"

class ConversationRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class AgentMessage(BaseModel):
    role: ConversationRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None

class AgentConversation(BaseModel):
    conversation_id: str
    user_id: str
    agent_type: AgentType
    messages: List[AgentMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: str = "active"  # active, completed, archived

class AgentConfig(BaseModel):
    agent_type: AgentType
    name: str
    description: str
    system_prompt: str
    capabilities: List[str]
    knowledge_domains: List[str]
    max_tokens: int = 2000
    temperature: float = 0.7
    model: str = "gpt-4"
    tools: List[str] = Field(default_factory=list)

class AgentRequest(BaseModel):
    agent_type: AgentType
    user_id: str
    message: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    conversation_id: str
    agent_type: AgentType
    response: str
    suggestions: List[str] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0
    processing_time_ms: int = 0

# Default agent configurations
DEFAULT_AGENT_CONFIGS = {
    AgentType.MARKETING: AgentConfig(
        agent_type=AgentType.MARKETING,
        name="Marketing Strategist AI",
        description="Expert in digital marketing, campaign optimization, and customer acquisition",
        system_prompt="""You are a senior marketing strategist AI with expertise in:
- Digital marketing campaigns and optimization
- Customer acquisition and retention strategies
- Brand positioning and messaging
- Market research and competitive analysis
- Social media marketing and content strategy
- Email marketing and automation
- SEO/SEM and performance marketing
- Marketing analytics and ROI optimization

Provide actionable, data-driven marketing advice and strategies. Always consider budget constraints, target audience, and business objectives.""",
        capabilities=[
            "Campaign Strategy Development",
            "Customer Segmentation Analysis",
            "Content Marketing Planning",
            "Social Media Strategy",
            "Email Campaign Optimization",
            "Marketing Analytics",
            "Competitive Analysis",
            "Brand Positioning"
        ],
        knowledge_domains=[
            "Digital Marketing",
            "Customer Psychology",
            "Brand Management",
            "Marketing Analytics",
            "Growth Hacking",
            "Content Strategy"
        ],
        tools=["analytics_integration", "campaign_planner", "content_generator"]
    ),
    
    AgentType.FINANCE: AgentConfig(
        agent_type=AgentType.FINANCE,
        name="Financial Advisor AI",
        description="Expert in financial planning, investment analysis, and business finance",
        system_prompt="""You are a senior financial advisor AI with expertise in:
- Financial planning and budgeting
- Investment analysis and portfolio management
- Risk assessment and management
- Business valuation and financial modeling
- Tax optimization strategies
- Cash flow management
- Financial compliance and regulations
- Corporate finance and funding strategies

Provide accurate, compliant financial advice while emphasizing risk management and regulatory considerations. Always recommend consulting with qualified financial professionals for major decisions.""",
        capabilities=[
            "Financial Planning",
            "Investment Analysis",
            "Risk Assessment",
            "Budget Optimization",
            "Cash Flow Analysis",
            "Tax Strategy",
            "Financial Modeling",
            "Compliance Monitoring"
        ],
        knowledge_domains=[
            "Corporate Finance",
            "Investment Management",
            "Financial Regulations",
            "Tax Law",
            "Risk Management",
            "Financial Markets"
        ],
        tools=["financial_calculator", "risk_analyzer", "compliance_checker"]
    ),
    
    AgentType.HEALTHCARE: AgentConfig(
        agent_type=AgentType.HEALTHCARE,
        name="Healthcare Operations AI",
        description="Expert in healthcare operations, patient care optimization, and medical administration",
        system_prompt="""You are a healthcare operations AI with expertise in:
- Healthcare operations and workflow optimization
- Patient care coordination and management
- Medical administration and compliance
- Healthcare technology integration
- Quality improvement initiatives
- Staff scheduling and resource allocation
- Healthcare analytics and reporting
- Patient satisfaction and experience

Focus on operational efficiency, patient safety, and regulatory compliance. Always emphasize that medical decisions should be made by qualified healthcare professionals.""",
        capabilities=[
            "Operations Optimization",
            "Patient Flow Management",
            "Staff Scheduling",
            "Quality Metrics Analysis",
            "Compliance Monitoring",
            "Resource Planning",
            "Patient Experience",
            "Healthcare Analytics"
        ],
        knowledge_domains=[
            "Healthcare Operations",
            "Medical Administration",
            "Healthcare Compliance",
            "Patient Care Management",
            "Healthcare Technology",
            "Quality Improvement"
        ],
        tools=["scheduling_optimizer", "compliance_tracker", "analytics_dashboard"]
    ),
    
    AgentType.LEGAL: AgentConfig(
        agent_type=AgentType.LEGAL,
        name="Legal Research AI",
        description="Expert in legal research, contract analysis, and compliance guidance",
        system_prompt="""You are a legal research AI with expertise in:
- Legal research and case law analysis
- Contract review and analysis
- Regulatory compliance guidance
- Risk assessment and mitigation
- Legal document drafting assistance
- Intellectual property matters
- Corporate law and governance
- Privacy and data protection laws

Provide legal information and research assistance while emphasizing that this is not legal advice and qualified legal counsel should be consulted for legal decisions.""",
        capabilities=[
            "Legal Research",
            "Contract Analysis",
            "Compliance Guidance",
            "Risk Assessment",
            "Document Review",
            "Regulatory Updates",
            "IP Analysis",
            "Privacy Compliance"
        ],
        knowledge_domains=[
            "Corporate Law",
            "Contract Law",
            "Regulatory Compliance",
            "Intellectual Property",
            "Privacy Law",
            "Employment Law"
        ],
        tools=["legal_database", "contract_analyzer", "compliance_monitor"]
    ),
    
    AgentType.SALES: AgentConfig(
        agent_type=AgentType.SALES,
        name="Sales Optimization AI",
        description="Expert in sales strategy, lead generation, and customer relationship management",
        system_prompt="""You are a sales optimization AI with expertise in:
- Sales strategy development and execution
- Lead generation and qualification
- Customer relationship management
- Sales process optimization
- Pipeline management and forecasting
- Sales training and coaching
- Competitive positioning
- Pricing strategy and negotiation

Provide actionable sales strategies focused on revenue growth, customer satisfaction, and long-term relationship building.""",
        capabilities=[
            "Sales Strategy",
            "Lead Generation",
            "Pipeline Management",
            "Customer Segmentation",
            "Sales Forecasting",
            "Competitive Analysis",
            "Pricing Optimization",
            "Sales Training"
        ],
        knowledge_domains=[
            "Sales Methodology",
            "Customer Psychology",
            "CRM Systems",
            "Sales Analytics",
            "Negotiation",
            "Account Management"
        ],
        tools=["crm_integration", "lead_scorer", "sales_analytics"]
    )
}

def load_agent_configs() -> Dict[AgentType, AgentConfig]:
    """Load agent configurations from file"""
    try:
        if os.path.exists(AGENT_CONFIGS_FILE):
            with open(AGENT_CONFIGS_FILE, 'r') as f:
                data = json.load(f)
                return {AgentType(k): AgentConfig(**v) for k, v in data.items()}
    except Exception as e:
        logger.error(f"Error loading agent configs: {e}")
    
    # Save defaults if file doesn't exist
    save_agent_configs(DEFAULT_AGENT_CONFIGS)
    return DEFAULT_AGENT_CONFIGS

def save_agent_configs(configs: Dict[AgentType, AgentConfig]):
    """Save agent configurations to file"""
    try:
        data = {k.value: v.dict() for k, v in configs.items()}
        with open(AGENT_CONFIGS_FILE, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving agent configs: {e}")

def load_conversations() -> List[AgentConversation]:
    """Load conversations from file"""
    try:
        if os.path.exists(CONVERSATIONS_FILE):
            with open(CONVERSATIONS_FILE, 'r') as f:
                data = json.load(f)
                return [AgentConversation(**conv) for conv in data]
    except Exception as e:
        logger.error(f"Error loading conversations: {e}")
    return []

def save_conversations(conversations: List[AgentConversation]):
    """Save conversations to file"""
    try:
        data = [conv.dict() for conv in conversations]
        with open(CONVERSATIONS_FILE, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving conversations: {e}")

async def generate_ai_response(agent_config: AgentConfig, messages: List[AgentMessage]) -> str:
    """Generate AI response using OpenAI"""
    try:
        # Convert messages to OpenAI format
        openai_messages = [
            {"role": "system", "content": agent_config.system_prompt}
        ]
        
        for msg in messages[-10:]:  # Keep last 10 messages for context
            openai_messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
        
        # Generate response
        response = client.chat.completions.create(
            model=agent_config.model,
            messages=openai_messages,
            max_tokens=agent_config.max_tokens,
            temperature=agent_config.temperature
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        return f"I apologize, but I'm experiencing technical difficulties. Please try again later. Error: {str(e)}"

@router.get("/agents", response_model=Dict[str, AgentConfig])
async def get_available_agents():
    """Get all available specialized agents"""
    configs = load_agent_configs()
    return {agent_type.value: config for agent_type, config in configs.items()}

@router.get("/agents/{agent_type}", response_model=AgentConfig)
async def get_agent_config(agent_type: AgentType):
    """Get specific agent configuration"""
    configs = load_agent_configs()
    if agent_type not in configs:
        raise HTTPException(status_code=404, detail="Agent type not found")
    return configs[agent_type]

@router.post("/chat", response_model=AgentResponse)
async def chat_with_agent(request: AgentRequest):
    """Start or continue conversation with specialized agent"""
    start_time = datetime.now()
    
    # Load configurations and conversations
    configs = load_agent_configs()
    conversations = load_conversations()
    
    if request.agent_type not in configs:
        raise HTTPException(status_code=404, detail="Agent type not found")
    
    agent_config = configs[request.agent_type]
    
    # Find or create conversation
    conversation = None
    if request.conversation_id:
        for conv in conversations:
            if conv.conversation_id == request.conversation_id:
                conversation = conv
                break
    
    if not conversation:
        conversation = AgentConversation(
            conversation_id=f"{request.agent_type.value}_{request.user_id}_{int(datetime.now().timestamp())}",
            user_id=request.user_id,
            agent_type=request.agent_type
        )
        conversations.append(conversation)
    
    # Add user message
    user_message = AgentMessage(
        role=ConversationRole.USER,
        content=request.message,
        metadata=request.context
    )
    conversation.messages.append(user_message)
    
    # Generate AI response
    ai_response_content = await generate_ai_response(agent_config, conversation.messages)
    
    # Add AI response
    ai_message = AgentMessage(
        role=ConversationRole.ASSISTANT,
        content=ai_response_content
    )
    conversation.messages.append(ai_message)
    
    # Update conversation
    conversation.updated_at = datetime.now()
    save_conversations(conversations)
    
    # Calculate processing time
    processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
    
    # Generate suggestions based on agent type
    suggestions = []
    if request.agent_type == AgentType.MARKETING:
        suggestions = [
            "Analyze competitor strategies",
            "Create content calendar",
            "Optimize ad campaigns",
            "Review customer segments"
        ]
    elif request.agent_type == AgentType.FINANCE:
        suggestions = [
            "Review budget allocation",
            "Analyze cash flow",
            "Assess investment options",
            "Calculate ROI metrics"
        ]
    elif request.agent_type == AgentType.HEALTHCARE:
        suggestions = [
            "Optimize patient flow",
            "Review quality metrics",
            "Analyze staff efficiency",
            "Check compliance status"
        ]
    
    return AgentResponse(
        conversation_id=conversation.conversation_id,
        agent_type=request.agent_type,
        response=ai_response_content,
        suggestions=suggestions,
        confidence=0.85,  # Mock confidence score
        processing_time_ms=processing_time
    )

@router.get("/conversations/{user_id}")
async def get_user_conversations(user_id: str, agent_type: Optional[AgentType] = None):
    """Get user's conversation history"""
    conversations = load_conversations()
    
    user_conversations = [
        conv for conv in conversations
        if conv.user_id == user_id and (not agent_type or conv.agent_type == agent_type)
    ]
    
    # Sort by updated_at descending
    user_conversations.sort(key=lambda x: x.updated_at, reverse=True)
    
    return {"conversations": user_conversations}

@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str):
    """Get messages from specific conversation"""
    conversations = load_conversations()
    
    for conv in conversations:
        if conv.conversation_id == conversation_id:
            return {"messages": conv.messages}
    
    raise HTTPException(status_code=404, detail="Conversation not found")

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, user_id: str):
    """Delete conversation"""
    conversations = load_conversations()
    
    for i, conv in enumerate(conversations):
        if conv.conversation_id == conversation_id and conv.user_id == user_id:
            conversations.pop(i)
            save_conversations(conversations)
            return {"message": "Conversation deleted successfully"}
    
    raise HTTPException(status_code=404, detail="Conversation not found")

@router.post("/agents/{agent_type}/train")
async def train_agent(agent_type: AgentType, training_data: Dict[str, Any]):
    """Train agent with custom data (placeholder for future ML training)"""
    # This is a placeholder for future machine learning training capabilities
    # Currently just logs the training request
    
    logger.info(f"Training request for {agent_type.value} agent with data: {training_data}")
    
    return {
        "message": f"Training initiated for {agent_type.value} agent",
        "status": "queued",
        "training_id": f"train_{agent_type.value}_{int(datetime.now().timestamp())}"
    }

@router.get("/analytics/usage")
async def get_agent_usage_analytics():
    """Get usage analytics for specialized agents"""
    conversations = load_conversations()
    
    analytics = {
        "total_conversations": len(conversations),
        "conversations_by_agent": {},
        "messages_by_agent": {},
        "active_users": set(),
        "daily_usage": {}
    }
    
    for agent_type in AgentType:
        analytics["conversations_by_agent"][agent_type.value] = 0
        analytics["messages_by_agent"][agent_type.value] = 0
    
    for conv in conversations:
        analytics["conversations_by_agent"][conv.agent_type.value] += 1
        analytics["messages_by_agent"][conv.agent_type.value] += len(conv.messages)
        analytics["active_users"].add(conv.user_id)
        
        # Daily usage
        day_key = conv.created_at.strftime("%Y-%m-%d")
        if day_key not in analytics["daily_usage"]:
            analytics["daily_usage"][day_key] = 0
        analytics["daily_usage"][day_key] += 1
    
    analytics["active_users"] = len(analytics["active_users"])
    
    return analytics