"""
Analytics & Reports API Routes
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from backend.services.analytics_service import AnalyticsService, ReportType, ReportFormat

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics & Reports"])
analytics_service = AnalyticsService()


class ReportRequest(BaseModel):
    tenant_id: str
    report_type: ReportType
    start_date: datetime
    end_date: datetime
    format: ReportFormat = ReportFormat.JSON
    filters: Optional[dict] = None


class ScheduleReportRequest(BaseModel):
    tenant_id: str
    report_type: ReportType
    schedule_cron: str
    format: ReportFormat
    recipients: List[str]
    filters: Optional[dict] = None


@router.post("/generate-report")
async def generate_report(request: ReportRequest):
    """Generate analytics report"""
    try:
        report = await analytics_service.generate_report(
            tenant_id=request.tenant_id,
            report_type=request.report_type,
            start_date=request.start_date,
            end_date=request.end_date,
            format=request.format,
            filters=request.filters
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule-report")
async def schedule_report(request: ScheduleReportRequest):
    """Schedule recurring report generation"""
    try:
        schedule = await analytics_service.schedule_report(
            tenant_id=request.tenant_id,
            report_type=request.report_type,
            schedule_cron=request.schedule_cron,
            format=request.format,
            recipients=request.recipients,
            filters=request.filters
        )
        return schedule
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/{tenant_id}")
async def get_analytics_dashboard(tenant_id: str):
    """Get comprehensive analytics dashboard"""
    try:
        dashboard = await analytics_service.get_analytics_dashboard(tenant_id)
        return dashboard
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
