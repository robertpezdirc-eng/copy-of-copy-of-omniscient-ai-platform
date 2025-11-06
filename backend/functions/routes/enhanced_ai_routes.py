"""
Enhanced AI capabilities routes: Recommendations, Real-time Insights, Gamification.

Provides endpoints for:
- AI-powered recommendations (products, processes, decisions, resources)
- Real-time AI insights and alerts
- KPI tracking and visualization
- Gamification features (points, badges, achievements)
- Personalized AI dashboard
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# Import services
try:
    from services.advanced_ai.recommendation_engine_v2 import get_recommendation_engine
    from services.advanced_ai.ai_insights import get_ai_insights_service
    
    _recommendation_engine = get_recommendation_engine()
    _insights_service = get_ai_insights_service()
except Exception as exc:
    logger.warning(f"Enhanced AI services unavailable: {exc}")
    _recommendation_engine = None
    _insights_service = None


def _require_recommendation_engine():
    if not _recommendation_engine:
        raise HTTPException(status_code=503, detail="Recommendation engine unavailable")
    return _recommendation_engine


def _require_insights_service():
    if not _insights_service:
        raise HTTPException(status_code=503, detail="AI insights service unavailable")
    return _insights_service


# Request Models

class ProductRecommendationRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    limit: int = Field(default=5, ge=1, le=20, description="Max recommendations")


class ProcessOptimizationRequest(BaseModel):
    process_data: Dict[str, Any] = Field(..., description="Process information")
    current_metrics: Dict[str, float] = Field(..., description="Current performance metrics")


class DecisionSupportRequest(BaseModel):
    decision_context: Dict[str, Any] = Field(..., description="Decision context")
    options: List[Dict[str, Any]] = Field(..., description="Options to analyze")


class ResourceAllocationRequest(BaseModel):
    available_resources: Dict[str, Any] = Field(..., description="Available resources")
    tasks: List[Dict[str, Any]] = Field(..., description="Tasks requiring resources")


class PerformanceImprovementRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    current_metrics: Dict[str, float] = Field(..., description="Current metrics")
    goals: Optional[Dict[str, float]] = Field(default=None, description="Target metrics")


class KPITrackingRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    kpi_name: str = Field(..., description="KPI name")
    value: float = Field(..., description="KPI value")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class AlertRequest(BaseModel):
    user_id: str = Field(..., description="User to alert")
    alert_type: str = Field(..., description="Alert type")
    message: str = Field(..., description="Alert message")
    severity: str = Field(default="info", description="Severity level")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Additional data")


# Recommendation Engine Endpoints

@router.post("/recommendations/products", tags=["AI Recommendations"])
async def get_product_recommendations(request: ProductRecommendationRequest) -> Dict[str, Any]:
    """
    Get personalized product/content recommendations.
    
    Example:
    ```json
    {
      "user_id": "user_123",
      "context": {
        "current_page": "analytics",
        "recent_views": ["dashboard", "reports"]
      },
      "limit": 5
    }
    ```
    """
    engine = _require_recommendation_engine()
    try:
        return await engine.get_product_recommendations(
            user_id=request.user_id,
            context=request.context,
            limit=request.limit
        )
    except Exception as exc:
        logger.error(f"Product recommendations failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/recommendations/process-optimization", tags=["AI Recommendations"])
async def get_process_optimization(request: ProcessOptimizationRequest) -> Dict[str, Any]:
    """
    Get AI-powered process optimization suggestions.
    
    Analyzes current metrics and provides actionable suggestions with expected impact.
    """
    engine = _require_recommendation_engine()
    try:
        return await engine.get_process_optimization_suggestions(
            process_data=request.process_data,
            current_metrics=request.current_metrics
        )
    except Exception as exc:
        logger.error(f"Process optimization failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/recommendations/decision-support", tags=["AI Recommendations"])
async def get_decision_support(request: DecisionSupportRequest) -> Dict[str, Any]:
    """
    Get AI-powered decision support.
    
    Analyzes multiple options and provides recommendations with pros/cons.
    """
    engine = _require_recommendation_engine()
    try:
        return await engine.get_decision_support(
            decision_context=request.decision_context,
            options=request.options
        )
    except Exception as exc:
        logger.error(f"Decision support failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/recommendations/resource-allocation", tags=["AI Recommendations"])
async def get_resource_allocation(request: ResourceAllocationRequest) -> Dict[str, Any]:
    """
    Get optimal resource allocation recommendations.
    
    Analyzes tasks and resources to provide optimal allocation plan.
    """
    engine = _require_recommendation_engine()
    try:
        return await engine.get_resource_allocation_recommendations(
            available_resources=request.available_resources,
            tasks=request.tasks
        )
    except Exception as exc:
        logger.error(f"Resource allocation failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/recommendations/performance-improvement", tags=["AI Recommendations"])
async def get_performance_improvement(request: PerformanceImprovementRequest) -> Dict[str, Any]:
    """
    Get personalized performance improvement suggestions.
    
    Includes gamification features with points and achievements.
    """
    engine = _require_recommendation_engine()
    try:
        return await engine.get_performance_improvement_suggestions(
            user_id=request.user_id,
            current_metrics=request.current_metrics,
            goals=request.goals
        )
    except Exception as exc:
        logger.error(f"Performance improvement failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# AI Insights Endpoints

@router.get("/insights/realtime/{user_id}", tags=["AI Insights"])
async def get_realtime_insights(
    user_id: str,
    data_sources: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get real-time AI insights for a user.
    
    Query params:
    - data_sources: Comma-separated list (e.g., "usage,performance,engagement")
    """
    service = _require_insights_service()
    try:
        sources = data_sources.split(",") if data_sources else None
        return await service.get_realtime_insights(user_id, sources)
    except Exception as exc:
        logger.error(f"Realtime insights failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/insights/recommendations/{user_id}", tags=["AI Insights"])
async def get_personalized_recommendations(
    user_id: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get personalized AI recommendations for a user.
    """
    service = _require_insights_service()
    try:
        return await service.get_personalized_recommendations(user_id, context)
    except Exception as exc:
        logger.error(f"Personalized recommendations failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/insights/alerts", tags=["AI Insights"])
async def create_alert(request: AlertRequest) -> Dict[str, Any]:
    """
    Create a proactive AI alert for a user.
    """
    service = _require_insights_service()
    try:
        return await service.create_alert(
            user_id=request.user_id,
            alert_type=request.alert_type,
            message=request.message,
            severity=request.severity,
            data=request.data
        )
    except Exception as exc:
        logger.error(f"Alert creation failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/insights/alerts/{user_id}", tags=["AI Insights"])
async def get_user_alerts(
    user_id: str,
    unread_only: bool = False
) -> Dict[str, Any]:
    """
    Get alerts for a user.
    
    Query params:
    - unread_only: Return only unread alerts (default: false)
    """
    service = _require_insights_service()
    try:
        return await service.get_user_alerts(user_id, unread_only)
    except Exception as exc:
        logger.error(f"Get alerts failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/insights/kpi", tags=["AI Insights", "KPI Tracking"])
async def track_kpi(request: KPITrackingRequest) -> Dict[str, Any]:
    """
    Track a KPI for real-time monitoring.
    
    Returns trend analysis and insights.
    """
    service = _require_insights_service()
    try:
        return await service.track_kpi(
            user_id=request.user_id,
            kpi_name=request.kpi_name,
            value=request.value,
            metadata=request.metadata
        )
    except Exception as exc:
        logger.error(f"KPI tracking failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/insights/gamification/{user_id}", tags=["AI Insights", "Gamification"])
async def get_gamification_status(user_id: str) -> Dict[str, Any]:
    """
    Get gamification status for a user.
    
    Returns:
    - Points and level
    - Badges and achievements
    - Leaderboard rank
    - Streak and engagement score
    """
    service = _require_insights_service()
    try:
        return await service.get_gamification_status(user_id)
    except Exception as exc:
        logger.error(f"Gamification status failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/insights/dashboard/{user_id}", tags=["AI Insights", "Dashboard"])
async def get_dashboard_summary(user_id: str) -> Dict[str, Any]:
    """
    Get comprehensive AI-powered dashboard summary.
    
    Includes:
    - Real-time insights
    - Unread alerts
    - Top KPIs with trends
    - Gamification status
    - Personalized recommendations
    """
    service = _require_insights_service()
    try:
        return await service.get_dashboard_summary(user_id)
    except Exception as exc:
        logger.error(f"Dashboard summary failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/status", tags=["Enhanced AI"])
async def enhanced_ai_status() -> Dict[str, Any]:
    """
    Get status of enhanced AI services.
    """
    return {
        "recommendation_engine": bool(_recommendation_engine),
        "ai_insights": bool(_insights_service),
        "features": {
            "product_recommendations": True,
            "process_optimization": True,
            "decision_support": True,
            "resource_allocation": True,
            "performance_improvement": True,
            "realtime_insights": True,
            "proactive_alerts": True,
            "kpi_tracking": True,
            "gamification": True,
            "personalized_dashboard": True,
        },
    }
