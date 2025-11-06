"""
AI Assistant Routes for Automation
Provides AI-powered automation capabilities
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from database import get_redis
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class AssistantTaskRequest(BaseModel):
    """Request to create an AI assistant task"""
    tenant_id: str = Field(..., min_length=1)
    action: str = Field(..., pattern="^(analyze_usage|optimize_costs|predict_churn|generate_insights|automate_support|schedule_tasks|monitor_alerts|optimize_performance)$")
    params: Optional[Dict[str, Any]] = None


@router.post("/assistant/tasks", tags=["AI Assistant"])
async def create_assistant_task(
    request: AssistantTaskRequest,
    redis=Depends(get_redis)
):
    """Create a new AI assistant task"""
    try:
        from services.ai_assistant_service import get_ai_assistant_service, AssistantAction
        from services.cache_service import get_cache_service
        from services.observability_service import get_observability_service
        
        cache_service = get_cache_service(redis) if redis else None
        obs_service = get_observability_service(redis) if redis else None
        
        assistant = get_ai_assistant_service(redis, cache_service, obs_service)
        
        action = AssistantAction(request.action)
        task = await assistant.create_task(
            tenant_id=request.tenant_id,
            action=action,
            params=request.params
        )
        
        return {
            "success": True,
            "task": task.to_dict()
        }
    except Exception as e:
        logger.error(f"Failed to create assistant task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assistant/tasks/{task_id}/execute", tags=["AI Assistant"])
async def execute_assistant_task(
    task_id: str,
    tenant_id: str,
    redis=Depends(get_redis)
):
    """Execute an AI assistant task"""
    try:
        from services.ai_assistant_service import get_ai_assistant_service
        from services.cache_service import get_cache_service
        from services.observability_service import get_observability_service
        
        cache_service = get_cache_service(redis) if redis else None
        obs_service = get_observability_service(redis) if redis else None
        
        assistant = get_ai_assistant_service(redis, cache_service, obs_service)
        
        result = await assistant.execute_task(tenant_id, task_id)
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        logger.error(f"Failed to execute assistant task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assistant/tasks/{task_id}", tags=["AI Assistant"])
async def get_assistant_task_status(
    task_id: str,
    redis=Depends(get_redis)
):
    """Get status of an AI assistant task"""
    try:
        from services.ai_assistant_service import get_ai_assistant_service
        
        assistant = get_ai_assistant_service(redis)
        
        task = await assistant.get_task_status(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "success": True,
            "task": task
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assistant/tasks", tags=["AI Assistant"])
async def list_assistant_tasks(
    tenant_id: str,
    limit: int = 50,
    redis=Depends(get_redis)
):
    """List AI assistant tasks for a tenant"""
    try:
        from services.ai_assistant_service import get_ai_assistant_service
        
        assistant = get_ai_assistant_service(redis)
        
        tasks = await assistant.list_tasks(tenant_id, limit)
        
        return {
            "success": True,
            "tasks": tasks,
            "count": len(tasks)
        }
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assistant/capabilities", tags=["AI Assistant"])
def get_assistant_capabilities():
    """Get available AI assistant capabilities"""
    return {
        "capabilities": [
            {
                "action": "analyze_usage",
                "name": "Usage Analysis",
                "description": "Analyze usage patterns and provide insights",
                "estimated_time": "2-5 seconds"
            },
            {
                "action": "optimize_costs",
                "name": "Cost Optimization",
                "description": "Identify cost savings opportunities",
                "estimated_time": "3-7 seconds"
            },
            {
                "action": "predict_churn",
                "name": "Churn Prediction",
                "description": "Predict user churn risk and provide retention strategies",
                "estimated_time": "5-10 seconds"
            },
            {
                "action": "generate_insights",
                "name": "Business Insights",
                "description": "Generate actionable business intelligence",
                "estimated_time": "3-8 seconds"
            },
            {
                "action": "automate_support",
                "name": "Support Automation",
                "description": "Automate support ticket handling",
                "estimated_time": "2-5 seconds"
            },
            {
                "action": "schedule_tasks",
                "name": "Task Scheduling",
                "description": "Schedule automated tasks",
                "estimated_time": "1-2 seconds"
            },
            {
                "action": "monitor_alerts",
                "name": "Alert Monitoring",
                "description": "Monitor and handle alerts",
                "estimated_time": "2-4 seconds"
            },
            {
                "action": "optimize_performance",
                "name": "Performance Optimization",
                "description": "Optimize system performance",
                "estimated_time": "4-8 seconds"
            }
        ]
    }


@router.post("/assistant/quick-actions/analyze", tags=["AI Assistant"])
async def quick_analyze_usage(
    tenant_id: str,
    redis=Depends(get_redis)
):
    """Quick action: Analyze usage for a tenant"""
    try:
        from services.ai_assistant_service import get_ai_assistant_service, AssistantAction
        from services.cache_service import get_cache_service
        from services.observability_service import get_observability_service
        
        cache_service = get_cache_service(redis) if redis else None
        obs_service = get_observability_service(redis) if redis else None
        
        assistant = get_ai_assistant_service(redis, cache_service, obs_service)
        
        # Create and execute task in one step
        task = await assistant.create_task(
            tenant_id=tenant_id,
            action=AssistantAction.ANALYZE_USAGE
        )
        
        result = await assistant.execute_task(tenant_id, task.task_id)
        
        return {
            "success": True,
            "analysis": result
        }
    except Exception as e:
        logger.error(f"Failed to analyze usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assistant/quick-actions/optimize-costs", tags=["AI Assistant"])
async def quick_optimize_costs(
    tenant_id: str,
    redis=Depends(get_redis)
):
    """Quick action: Optimize costs for a tenant"""
    try:
        from services.ai_assistant_service import get_ai_assistant_service, AssistantAction
        from services.cache_service import get_cache_service
        from services.observability_service import get_observability_service
        
        cache_service = get_cache_service(redis) if redis else None
        obs_service = get_observability_service(redis) if redis else None
        
        assistant = get_ai_assistant_service(redis, cache_service, obs_service)
        
        # Create and execute task in one step
        task = await assistant.create_task(
            tenant_id=tenant_id,
            action=AssistantAction.OPTIMIZE_COSTS
        )
        
        result = await assistant.execute_task(tenant_id, task.task_id)
        
        return {
            "success": True,
            "optimization": result
        }
    except Exception as e:
        logger.error(f"Failed to optimize costs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
