
import json
import os
from fastapi import APIRouter, HTTPException
from typing import Any

router = APIRouter()

KPI_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "business_kpis.json")

@router.get("/kpis", response_model=dict[str, Any])
async def get_kpis():
    """
    Retrieves the latest business KPIs.
    """
    if not os.path.exists(KPI_FILE_PATH):
        raise HTTPException(status_code=404, detail="KPI data not found. Please run the ingestion script.")
    
    try:
        with open(KPI_FILE_PATH, "r", encoding="utf-8") as f:
            kpis = json.load(f)
        return kpis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading KPI data: {str(e)}")
