"""
Domain-Specific AI Assistants
Specialized AI assistants for different business domains
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timezone
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class AssistantMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class AssistantRequest(BaseModel):
    domain: str = Field(..., description="Domain: finance, legal, technical, marketing, hr, sales, support")
    messages: List[AssistantMessage]
    context: Optional[Dict] = {}
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(500, ge=10, le=4000)


class AssistantResponse(BaseModel):
    domain: str
    response: str
    confidence: float
    suggestions: List[str] = []
    metadata: Dict = {}


# Domain-specific system prompts
DOMAIN_PROMPTS = {
    "finance": """You are a financial expert AI assistant. You provide insights on:
- Financial analysis and forecasting
- Budget planning and cost optimization
- Investment strategies and ROI calculations
- Revenue optimization and pricing strategies
- Financial compliance and reporting
Always provide data-driven, actionable financial advice.""",
    
    "legal": """You are a legal expert AI assistant specializing in:
- Contract analysis and review
- Compliance requirements (GDPR, CCPA, SOC2)
- Terms of service and privacy policies
- Intellectual property guidance
- Risk assessment and mitigation
Provide clear legal guidance while noting you're not a substitute for legal counsel.""",
    
    "technical": """You are a senior technical architect AI assistant. You help with:
- System architecture and design patterns
- Technology stack recommendations
- Performance optimization strategies
- Security best practices
- Technical troubleshooting and debugging
- API design and integration patterns
Provide clear, implementable technical solutions.""",
    
    "marketing": """You are a marketing strategist AI assistant. You excel at:
- Marketing campaign planning and optimization
- Content strategy and SEO optimization
- Customer acquisition and retention strategies
- Brand positioning and messaging
- Social media strategy and analytics
- Conversion rate optimization
Provide creative, data-driven marketing insights.""",
    
    "hr": """You are an HR expert AI assistant. You assist with:
- Talent acquisition and recruitment strategies
- Employee onboarding and training programs
- Performance management and reviews
- Employee engagement and retention
- HR compliance and policies
- Compensation and benefits planning
Provide empathetic, people-focused HR guidance.""",
    
    "sales": """You are a sales expert AI assistant. You help with:
- Sales strategy and pipeline management
- Lead qualification and scoring
- Sales forecasting and quota planning
- Customer relationship management
- Proposal and pitch development
- Negotiation strategies and objection handling
Provide actionable sales insights to close more deals.""",
    
    "support": """You are a customer support expert AI assistant. You specialize in:
- Customer issue resolution and troubleshooting
- Knowledge base content creation
- Support ticket triage and prioritization
- Customer communication best practices
- Support metrics and SLA management
- Escalation procedures
Provide helpful, empathetic customer support guidance.""",
}


def _generate_mock_response(domain: str, messages: List[AssistantMessage]) -> str:
    """Generate mock AI response (replace with actual AI model in production)"""
    
    user_message = next((m.content for m in messages if m.role == "user"), "")
    
    # Simple keyword-based responses for demo
    responses = {
        "finance": f"Based on financial analysis, here's my recommendation for '{user_message}': Focus on improving your key financial metrics. Consider implementing cost optimization strategies while maintaining revenue growth. I recommend analyzing your current burn rate and extending your runway by at least 6 months.",
        
        "legal": f"Regarding '{user_message}', from a legal perspective: Ensure you have proper documentation and compliance measures in place. Review your contracts for liability limitations and include appropriate indemnification clauses. Consider consulting with legal counsel for specific jurisdiction requirements.",
        
        "technical": f"For the technical challenge '{user_message}': I recommend implementing a microservices architecture with proper service isolation. Use containerization (Docker/Kubernetes) for scalability. Implement API gateways for request routing and rate limiting. Consider using Redis for caching to improve performance by 150%.",
        
        "marketing": f"For your marketing question '{user_message}': Focus on customer acquisition through multi-channel campaigns. Implement A/B testing for all marketing materials. Use data analytics to identify high-performing channels. Consider personalization strategies to improve conversion rates by 200-400%.",
        
        "hr": f"Regarding the HR matter '{user_message}': Prioritize employee engagement and clear communication. Implement structured onboarding processes and regular feedback cycles. Consider employee development programs to improve retention. Ensure all policies comply with current labor laws.",
        
        "sales": f"For the sales challenge '{user_message}': Focus on qualifying leads early in the pipeline. Implement a consultative selling approach. Use CRM analytics to identify patterns in successful deals. Consider offering value-based pricing aligned with customer outcomes.",
        
        "support": f"For the support issue '{user_message}': Prioritize quick response times and clear communication. Implement a tiered support system for efficient escalation. Create comprehensive documentation to enable self-service. Track customer satisfaction metrics and iterate on processes.",
    }
    
    return responses.get(domain, f"I can help you with {domain} domain. Please provide more details about your specific question or challenge.")


def _generate_suggestions(domain: str) -> List[str]:
    """Generate domain-specific suggestions"""
    
    suggestions = {
        "finance": [
            "Analyze cash flow trends",
            "Review budget allocations",
            "Optimize pricing strategy",
            "Calculate customer lifetime value"
        ],
        "legal": [
            "Review terms of service",
            "Audit compliance requirements",
            "Update privacy policy",
            "Assess legal risks"
        ],
        "technical": [
            "Review system architecture",
            "Optimize database queries",
            "Implement caching layer",
            "Conduct security audit"
        ],
        "marketing": [
            "Create content calendar",
            "Analyze campaign performance",
            "Optimize landing pages",
            "Develop email sequences"
        ],
        "hr": [
            "Create onboarding checklist",
            "Design performance review process",
            "Develop training program",
            "Improve employee engagement"
        ],
        "sales": [
            "Qualify leads systematically",
            "Create sales playbook",
            "Optimize pricing proposals",
            "Improve follow-up process"
        ],
        "support": [
            "Create FAQ documentation",
            "Implement ticket automation",
            "Improve response times",
            "Gather customer feedback"
        ],
    }
    
    return suggestions.get(domain, [])


@router.post("/assistants/chat", response_model=AssistantResponse)
async def chat_with_assistant(request: AssistantRequest):
    """Chat with a domain-specific AI assistant"""
    
    if request.domain not in DOMAIN_PROMPTS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid domain. Supported domains: {', '.join(DOMAIN_PROMPTS.keys())}"
        )
    
    try:
        # In production, integrate with actual AI model (OpenAI, Anthropic, etc.)
        # messages_with_system = [
        #     {"role": "system", "content": DOMAIN_PROMPTS[request.domain]},
        #     *[{"role": m.role, "content": m.content} for m in request.messages]
        # ]
        # 
        # response = openai.ChatCompletion.create(
        #     model="gpt-4",
        #     messages=messages_with_system,
        #     temperature=request.temperature,
        #     max_tokens=request.max_tokens
        # )
        # 
        # ai_response = response.choices[0].message.content
        
        # Mock response for now
        ai_response = _generate_mock_response(request.domain, request.messages)
        
        return AssistantResponse(
            domain=request.domain,
            response=ai_response,
            confidence=0.85,
            suggestions=_generate_suggestions(request.domain),
            metadata={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "model": "mock-assistant-v1",
                "context_included": bool(request.context)
            }
        )
    
    except Exception as e:
        logger.error(f"Error in AI assistant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assistants/domains")
async def list_assistant_domains():
    """List all available assistant domains with descriptions"""
    
    return {
        "domains": [
            {
                "id": "finance",
                "name": "Finance Assistant",
                "description": "Financial analysis, budgeting, forecasting, and optimization",
                "capabilities": ["Financial analysis", "Budget planning", "ROI calculations", "Cost optimization"]
            },
            {
                "id": "legal",
                "name": "Legal Assistant",
                "description": "Legal compliance, contracts, and risk assessment",
                "capabilities": ["Contract review", "Compliance guidance", "Risk assessment", "Policy creation"]
            },
            {
                "id": "technical",
                "name": "Technical Assistant",
                "description": "Architecture, development, and technical problem-solving",
                "capabilities": ["System design", "Performance optimization", "Security best practices", "Troubleshooting"]
            },
            {
                "id": "marketing",
                "name": "Marketing Assistant",
                "description": "Marketing strategy, campaigns, and growth tactics",
                "capabilities": ["Campaign planning", "Content strategy", "SEO optimization", "Conversion optimization"]
            },
            {
                "id": "hr",
                "name": "HR Assistant",
                "description": "Human resources, recruitment, and employee management",
                "capabilities": ["Recruitment", "Employee engagement", "Performance management", "Policy development"]
            },
            {
                "id": "sales",
                "name": "Sales Assistant",
                "description": "Sales strategy, pipeline management, and closing deals",
                "capabilities": ["Pipeline management", "Lead qualification", "Sales forecasting", "Negotiation tactics"]
            },
            {
                "id": "support",
                "name": "Support Assistant",
                "description": "Customer support, troubleshooting, and issue resolution",
                "capabilities": ["Issue resolution", "Knowledge base", "Ticket management", "Customer communication"]
            }
        ]
    }


@router.get("/assistants/{domain}/capabilities")
async def get_assistant_capabilities(domain: str):
    """Get detailed capabilities of a specific assistant domain"""
    
    if domain not in DOMAIN_PROMPTS:
        raise HTTPException(
            status_code=404,
            detail=f"Domain not found. Available domains: {', '.join(DOMAIN_PROMPTS.keys())}"
        )
    
    capabilities = {
        "finance": {
            "analysis": ["Cash flow", "P&L", "Balance sheet", "ROI", "Customer LTV"],
            "planning": ["Budgets", "Forecasts", "Scenarios", "Cost optimization"],
            "reporting": ["Financial statements", "KPI dashboards", "Variance analysis"],
            "compliance": ["Tax regulations", "Audit preparation", "Financial controls"]
        },
        "legal": {
            "contracts": ["Review", "Drafting", "Negotiation support", "Amendment tracking"],
            "compliance": ["GDPR", "CCPA", "SOC2", "ISO standards"],
            "risk": ["Assessment", "Mitigation", "Documentation", "Audit trails"],
            "ip": ["Trademarks", "Patents", "Copyrights", "Trade secrets"]
        },
        "technical": {
            "architecture": ["System design", "Scalability", "Microservices", "Cloud infrastructure"],
            "development": ["Best practices", "Code review", "Testing strategies", "CI/CD"],
            "security": ["Vulnerability assessment", "Penetration testing", "Secure coding", "Compliance"],
            "operations": ["Monitoring", "Incident response", "Performance tuning", "Disaster recovery"]
        },
        "marketing": {
            "strategy": ["Market research", "Positioning", "Segmentation", "Brand strategy"],
            "campaigns": ["Planning", "Execution", "A/B testing", "Performance analysis"],
            "content": ["SEO", "Copywriting", "Social media", "Email marketing"],
            "analytics": ["Campaign metrics", "Attribution", "Funnel analysis", "ROI tracking"]
        },
        "hr": {
            "recruitment": ["Job descriptions", "Candidate sourcing", "Interview processes", "Offer letters"],
            "onboarding": ["Programs", "Documentation", "Training schedules", "Culture integration"],
            "development": ["Performance reviews", "Career paths", "Training programs", "Succession planning"],
            "compliance": ["Labor laws", "Benefits administration", "Policy documentation", "Harassment prevention"]
        },
        "sales": {
            "pipeline": ["Lead management", "Opportunity tracking", "Forecast accuracy", "Pipeline health"],
            "methodology": ["Consultative selling", "Solution selling", "Value-based selling", "Account-based selling"],
            "enablement": ["Sales playbooks", "Battle cards", "Proposal templates", "Training materials"],
            "analytics": ["Win/loss analysis", "Deal velocity", "Conversion rates", "Sales cycle length"]
        },
        "support": {
            "channels": ["Email", "Chat", "Phone", "Self-service portal"],
            "processes": ["Ticket routing", "Escalation", "SLA management", "Quality assurance"],
            "knowledge": ["FAQ creation", "Documentation", "Video tutorials", "Troubleshooting guides"],
            "metrics": ["Response time", "Resolution time", "CSAT", "First contact resolution"]
        }
    }
    
    return {
        "domain": domain,
        "prompt": DOMAIN_PROMPTS[domain],
        "capabilities": capabilities.get(domain, {}),
        "use_cases": _generate_suggestions(domain)
    }
