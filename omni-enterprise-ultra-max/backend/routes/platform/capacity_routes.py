"""
Capacity Planning & Cost Optimization Routes
"""

from fastapi import APIRouter
from datetime import datetime, timezone
import random

router = APIRouter()


@router.get("/capacity/forecast")
async def get_capacity_forecast():
    """Get capacity forecast"""
    
    return {
        "current_capacity": {
            "cpu": round(random.uniform(40, 70), 2),
            "memory": round(random.uniform(50, 80), 2),
            "storage": round(random.uniform(30, 60), 2)
        },
        "forecast_30d": {
            "cpu": round(random.uniform(60, 90), 2),
            "memory": round(random.uniform(70, 95), 2),
            "storage": round(random.uniform(50, 80), 2)
        },
        "recommendations": [
            "Consider scaling up CPU resources in 2 weeks",
            "Memory usage is stable",
            "Storage growth is normal"
        ]
    }


@router.get("/cost/optimization")
async def get_cost_optimization():
    """Get cost optimization recommendations"""
    
    return {
        "current_monthly_cost": round(random.uniform(1000, 5000), 2),
        "potential_savings": round(random.uniform(100, 800), 2),
        "recommendations": [
            {
                "category": "compute",
                "recommendation": "Right-size instances",
                "potential_saving": round(random.uniform(50, 300), 2)
            },
            {
                "category": "storage",
                "recommendation": "Use lifecycle policies",
                "potential_saving": round(random.uniform(30, 200), 2)
            }
        ]
    }


@router.get("/capacity/alerts")
async def get_capacity_alerts():
    """Get capacity-related alerts"""
    
    return {
        "alerts": [
            {
                "severity": "warning",
                "message": "CPU usage approaching 80%",
                "triggered_at": datetime.now(timezone.utc).isoformat()
            }
        ]
    }
