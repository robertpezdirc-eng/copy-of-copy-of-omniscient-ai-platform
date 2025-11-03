"""
Observability & SLA Monitoring Routes
Provides metrics, health checks, and SLA status
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from database import get_redis
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class MetricRecord(BaseModel):
    """Record a metric"""
    service_name: str = Field(..., min_length=1)
    latency_ms: float = Field(..., gt=0)
    is_error: bool = False
    tenant_id: Optional[str] = None


@router.post("/metrics/record", tags=["Observability"])
async def record_metric(
    metric: MetricRecord,
    redis=Depends(get_redis)
):
    """Record a service metric"""
    try:
        from services.observability_service import get_observability_service
        
        obs_service = get_observability_service(redis)
        await obs_service.record_request(
            service_name=metric.service_name,
            latency_ms=metric.latency_ms,
            is_error=metric.is_error,
            tenant_id=metric.tenant_id
        )
        
        return {
            "success": True,
            "message": "Metric recorded"
        }
    except Exception as e:
        logger.error(f"Failed to record metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", tags=["Observability"])
async def get_system_health(redis=Depends(get_redis)):
    """Get overall system health"""
    try:
        from services.observability_service import get_observability_service
        
        obs_service = get_observability_service(redis)
        health = await obs_service.get_system_health()
        
        return health
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/{service_name}", tags=["Observability"])
async def get_service_health(
    service_name: str,
    redis=Depends(get_redis)
):
    """Get health status of a specific service"""
    try:
        from services.observability_service import get_observability_service
        
        obs_service = get_observability_service(redis)
        status = await obs_service.check_health(service_name)
        
        return {
            "service": service_name,
            "status": status.value,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get service health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", tags=["Observability"])
async def get_all_metrics(redis=Depends(get_redis)):
    """Get metrics for all services"""
    try:
        from services.observability_service import get_observability_service
        
        obs_service = get_observability_service(redis)
        metrics = await obs_service.get_all_metrics()
        
        return {
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sla/{service_name}", tags=["Observability"])
async def get_sla_status(
    service_name: str,
    redis=Depends(get_redis)
):
    """Get SLA status for a service"""
    try:
        from services.observability_service import get_observability_service
        
        obs_service = get_observability_service(redis)
        sla = await obs_service.get_sla_status(service_name)
        
        return sla
    except Exception as e:
        logger.error(f"Failed to get SLA status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sla/report", tags=["Observability"])
async def get_sla_report(
    start_date: Optional[str] = Query(None, description="ISO format date"),
    end_date: Optional[str] = Query(None, description="ISO format date"),
    redis=Depends(get_redis)
):
    """Generate SLA compliance report"""
    try:
        from services.observability_service import get_observability_service
        
        obs_service = get_observability_service(redis)
        
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        report = await obs_service.generate_sla_report(start, end)
        
        return report
    except Exception as e:
        logger.error(f"Failed to generate SLA report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/tenant/{tenant_id}", tags=["Observability"])
async def get_tenant_metrics(
    tenant_id: str,
    service_name: Optional[str] = None,
    redis=Depends(get_redis)
):
    """Get metrics for a specific tenant"""
    try:
        from services.observability_service import get_observability_service
        
        obs_service = get_observability_service(redis)
        metrics = await obs_service.get_tenant_metrics(tenant_id, service_name)
        
        return metrics
    except Exception as e:
        logger.error(f"Failed to get tenant metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard", tags=["Observability"])
async def get_observability_dashboard(redis=Depends(get_redis)):
    """Get comprehensive observability dashboard data"""
    try:
        from services.observability_service import get_observability_service
        
        obs_service = get_observability_service(redis)
        
        # Get all relevant data
        health = await obs_service.get_system_health()
        metrics = await obs_service.get_all_metrics()
        
        return {
            "dashboard": {
                "health": health,
                "metrics": metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
