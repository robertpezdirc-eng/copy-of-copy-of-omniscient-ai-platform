"""
Autonomous Agents API Routes

Self-improving AI agents with web search, self-healing, and code generation
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agents", tags=["Autonomous Agents"])


# Pydantic Models
class ExecuteTaskRequest(BaseModel):
    task: str = Field(..., description="Task description")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    max_steps: int = Field(10, ge=1, le=50, description="Maximum execution steps")


class AgentActionResponse(BaseModel):
    action_type: str
    description: str
    parameters: Dict[str, Any]
    result: Optional[Any]
    error: Optional[str]
    timestamp: str


class ExecutionResponse(BaseModel):
    execution_id: str
    task: str
    state: str
    actions: List[AgentActionResponse]
    final_result: Optional[Any]
    start_time: str
    end_time: Optional[str]
    error_count: int
    heal_count: int


class WebSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")


class GenerateCodeRequest(BaseModel):
    requirements: str = Field(..., description="Code requirements")


class ImprovementSuggestion(BaseModel):
    title: str
    category: str
    priority: str
    description: str
    implementation: str
    timestamp: str
    status: str


class AgentStatsResponse(BaseModel):
    agent_name: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    total_self_heals: int
    improvement_suggestions: int
    pending_suggestions: int
    capabilities: Dict[str, bool]


# Routes
@router.post("/execute", response_model=ExecutionResponse)
async def execute_task(request: ExecuteTaskRequest):
    """
    Execute a task autonomously using AI agent
    
    The agent will:
    1. **Plan** the task using LLM reasoning
    2. **Execute** steps with available capabilities:
       - Web search for real-time information
       - Code generation for dynamic module creation
       - Platform analysis for improvements
       - Information synthesis
    3. **Self-heal** if errors occur (up to 3 retries per step)
    4. **Synthesize** final results
    
    **Example Tasks:**
    - "Research the latest trends in AI and summarize them"
    - "Generate a Python function to calculate Fibonacci numbers"
    - "Analyze the platform and suggest performance improvements"
    - "Search for information about quantum computing and explain it"
    
    **Example:**
    ```json
    {
        "task": "Research Redis caching best practices and create a summary",
        "context": {"focus_area": "performance"},
        "max_steps": 10
    }
    ```
    """
    try:
        from services.ai.autonomous_agent import get_autonomous_agent
        
        agent = get_autonomous_agent()
        
        execution = await agent.execute_task(
            task=request.task,
            context=request.context,
            max_steps=request.max_steps
        )
        
        # Convert to response model
        actions = [
            AgentActionResponse(
                action_type=action.action_type,
                description=action.description,
                parameters=action.parameters,
                result=action.result,
                error=action.error,
                timestamp=action.timestamp
            )
            for action in execution.actions
        ]
        
        return ExecutionResponse(
            execution_id=execution.execution_id,
            task=execution.task,
            state=execution.state.value,
            actions=actions,
            final_result=execution.final_result,
            start_time=execution.start_time,
            end_time=execution.end_time,
            error_count=execution.error_count,
            heal_count=execution.heal_count
        )
        
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/web-search")
async def web_search(request: WebSearchRequest):
    """
    Search the web for information (using DuckDuckGo API)
    
    Returns:
    - Abstract summary
    - Related topics
    - Source URL
    
    **Example:**
    ```json
    {
        "query": "artificial intelligence trends 2024"
    }
    ```
    """
    try:
        from services.ai.autonomous_agent import get_autonomous_agent
        
        agent = get_autonomous_agent()
        result = await agent._web_search(request.query)
        
        return result
        
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-code")
async def generate_code(request: GenerateCodeRequest):
    """
    Generate Python code based on requirements
    
    The agent uses LLM to generate:
    - Type-hinted code
    - Docstrings
    - Error handling
    - PEP 8 compliant formatting
    
    **Example:**
    ```json
    {
        "requirements": "Create a function that calculates the factorial of a number with memoization"
    }
    ```
    """
    try:
        from services.ai.autonomous_agent import get_autonomous_agent
        
        agent = get_autonomous_agent()
        result = await agent._generate_code(request.requirements)
        
        return result
        
    except Exception as e:
        logger.error(f"Code generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-platform")
async def analyze_platform():
    """
    Analyze the platform and generate improvement suggestions
    
    The agent will:
    1. Review platform architecture
    2. Analyze current features
    3. Generate 5 specific recommendations
    4. Categorize by: performance, security, features, architecture, cost
    5. Prioritize: high, medium, low
    
    Suggestions are stored and can be retrieved via `/suggestions` endpoint.
    """
    try:
        from services.ai.autonomous_agent import get_autonomous_agent
        
        agent = get_autonomous_agent()
        result = await agent._analyze_platform({})
        
        return result
        
    except Exception as e:
        logger.error(f"Platform analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions", response_model=List[ImprovementSuggestion])
async def get_suggestions(
    category: Optional[str] = None,
    priority: Optional[str] = None,
    status: str = "pending"
):
    """
    Get platform improvement suggestions from agent analysis
    
    **Filters:**
    - category: performance, security, features, architecture, cost
    - priority: high, medium, low
    - status: pending, implemented, rejected
    
    **Example:** `/suggestions?category=performance&priority=high`
    """
    try:
        from services.ai.autonomous_agent import get_autonomous_agent
        
        agent = get_autonomous_agent()
        suggestions = agent.get_improvement_suggestions(
            category=category,
            priority=priority,
            status=status
        )
        
        return [ImprovementSuggestion(**s) for s in suggestions]
        
    except Exception as e:
        logger.error(f"Failed to get suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions")
async def get_execution_history(limit: int = 10):
    """
    Get agent execution history
    
    Returns recent task executions with:
    - Execution ID
    - Task description
    - State (completed/failed)
    - Action count
    - Error and heal counts
    - Timestamps
    """
    try:
        from services.ai.autonomous_agent import get_autonomous_agent
        
        agent = get_autonomous_agent()
        history = agent.get_execution_history(limit=limit)
        
        return {
            "executions": history,
            "count": len(history)
        }
        
    except Exception as e:
        logger.error(f"Failed to get execution history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=AgentStatsResponse)
async def get_stats():
    """
    Get agent statistics
    
    Returns:
    - Total executions
    - Success rate
    - Self-healing statistics
    - Improvement suggestions count
    - Capability status
    """
    try:
        from services.ai.autonomous_agent import get_autonomous_agent
        
        agent = get_autonomous_agent()
        stats = agent.get_stats()
        
        return AgentStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Agent health check
    
    Verifies:
    - Agent is initialized
    - Web search capability
    - LLM availability
    - Code generation capability
    """
    try:
        from services.ai.autonomous_agent import get_autonomous_agent
        
        agent = get_autonomous_agent()
        stats = agent.get_stats()
        
        return {
            "status": "healthy",
            "agent_name": stats["agent_name"],
            "capabilities": stats["capabilities"],
            "total_executions": stats["total_executions"],
            "success_rate": stats["success_rate"]
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.post("/self-improve")
async def trigger_self_improvement(background_tasks: BackgroundTasks):
    """
    Trigger agent self-improvement cycle
    
    The agent will:
    1. Analyze the platform
    2. Generate improvement suggestions
    3. Optionally implement high-priority improvements
    4. Report results
    
    Runs in background.
    """
    try:
        from services.ai.autonomous_agent import get_autonomous_agent
        
        agent = get_autonomous_agent()
        
        async def improve():
            result = await agent.execute_task(
                task="Analyze the platform and suggest improvements",
                context={"focus": "self_improvement"},
                max_steps=5
            )
            logger.info(f"Self-improvement completed: {result.execution_id}")
        
        background_tasks.add_task(improve)
        
        return {
            "status": "started",
            "message": "Self-improvement cycle started in background"
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger self-improvement: {e}")
        raise HTTPException(status_code=500, detail=str(e))
