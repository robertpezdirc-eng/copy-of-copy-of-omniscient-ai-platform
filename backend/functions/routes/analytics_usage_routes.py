"""
Analytics Usage Routes
Provides endpoints for usage analytics, data export, and metrics tracking
"""

from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel

router = APIRouter()


class UsageMetrics(BaseModel):
    """Usage metrics response model"""
    total_requests: int
    api_calls: int
    data_processed_mb: float
    active_users: int
    period_start: str
    period_end: str


class ExportRequest(BaseModel):
    """Data export request model"""
    start_date: datetime
    end_date: datetime
    format: str = "csv"  # csv, json, excel
    include_details: bool = False


@router.get("/usage", response_model=UsageMetrics, tags=["Usage Analytics"])
async def get_usage_metrics(
    days: int = Query(default=7, ge=1, le=90, description="Number of days to analyze"),
    tenant_id: Optional[str] = Query(default=None, description="Filter by tenant ID")
):
    """
    Get usage metrics for the specified period
    
    - **days**: Number of days to analyze (1-90)
    - **tenant_id**: Optional tenant filter
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Mock data - would integrate with analytics_service in production
    return UsageMetrics(
        total_requests=12500 * days,
        api_calls=8400 * days,
        data_processed_mb=450.75 * days,
        active_users=245 + (days * 10),
        period_start=start_date.isoformat(),
        period_end=end_date.isoformat()
    )


@router.get("/usage/summary", tags=["Usage Analytics"])
async def get_usage_summary():
    """Get high-level usage summary"""
    return {
        "today": {
            "requests": 12500,
            "api_calls": 8400,
            "active_users": 245
        },
        "week": {
            "requests": 87500,
            "api_calls": 58800,
            "active_users": 1247
        },
        "month": {
            "requests": 375000,
            "api_calls": 252000,
            "active_users": 4893
        },
        "trends": {
            "requests_change_percent": 15.3,
            "users_change_percent": 8.7
        }
    }


@router.post("/usage/export", tags=["Usage Analytics"])
async def export_usage_data(request: ExportRequest):
    """
    Export usage data in specified format
    
    Supports CSV, JSON, and Excel formats
    """
    if request.format not in ["csv", "json", "excel"]:
        raise HTTPException(status_code=400, detail="Invalid format. Use csv, json, or excel")
    
    # Mock export response - would generate actual file in production
    return {
        "export_id": f"export_{datetime.utcnow().timestamp()}",
        "format": request.format,
        "period": {
            "start": request.start_date.isoformat(),
            "end": request.end_date.isoformat()
        },
        "status": "processing",
        "download_url": f"/api/v1/analytics/exports/download/export_{datetime.utcnow().timestamp()}"
    }
