"""
KPI Routes - Provides endpoints for accessing Key Performance Indicators.
"""
from fastapi import APIRouter, Depends
from typing import Any, Dict

from backend.services.kpi_service import get_kpi_service, KPIService

router = APIRouter()

@router.get("/kpis", response_model=Dict[str, Any])
async def get_kpis(kpi_service: KPIService = Depends(get_kpi_service)):
    """
    Retrieves the latest business KPIs, generated dynamically and powered by AI insights.
    """
    return await kpi_service.get_kpis()
