"""
Analytics Routes
"""

from fastapi import APIRouter, Query
from datetime import datetime, timezone, timedelta
import random

# Import caching utility
from utils.cache import cache_response

analytics_router = APIRouter()


@analytics_router.get("/dashboard")
@cache_response(ttl=300)  # Cache for 5 minutes
async def get_analytics_dashboard(
    period: str = Query("30d", description="Period: 7d, 30d, 90d")
):
    """Get analytics dashboard data - cached for 5 min"""
    
    return {
        "period": period,
        "total_users": random.randint(1000, 10000),
        "active_users": random.randint(500, 5000),
        "total_revenue": round(random.uniform(10000, 100000), 2),
        "api_calls": random.randint(100000, 1000000),
        "conversion_rate": round(random.uniform(2, 10), 2),
        "charts": {
            "daily_users": [random.randint(100, 500) for _ in range(30)],
            "daily_revenue": [round(random.uniform(1000, 5000), 2) for _ in range(30)]
        }
    }


@analytics_router.get("/metrics")
@cache_response(ttl=60)  # Cache for 1 minute
async def get_metrics():
    """Get real-time metrics - cached for 1 min"""
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": {
            "requests_per_second": round(random.uniform(100, 500), 2),
            "average_response_time": round(random.uniform(50, 200), 2),
            "error_rate": round(random.uniform(0.1, 2.0), 2),
            "active_connections": random.randint(100, 1000)
        }
    }
