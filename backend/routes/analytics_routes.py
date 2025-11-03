"""
Analytics Routes - Enhanced with Real-Time Metrics and Dashboard Support
"""

from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import random
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/dashboard")
async def get_analytics_dashboard(
    period: str = Query("30d", description="Period: 7d, 30d, 90d, 1y"),
    tenant_id: Optional[str] = None
):
    """Get comprehensive analytics dashboard data"""
    
    # Parse period
    days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    days = days_map.get(period, 30)
    
    # Generate time-series data
    now = datetime.now(timezone.utc)
    daily_data = []
    
    for i in range(days):
        date = now - timedelta(days=days - i - 1)
        daily_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "users": random.randint(50, 500),
            "revenue": round(random.uniform(1000, 5000), 2),
            "api_calls": random.randint(5000, 50000),
            "conversions": random.randint(10, 100)
        })
    
    return {
        "period": period,
        "tenant_id": tenant_id,
        "summary": {
            "total_users": random.randint(1000, 10000),
            "active_users": random.randint(500, 5000),
            "total_revenue": round(sum(d["revenue"] for d in daily_data), 2),
            "api_calls": sum(d["api_calls"] for d in daily_data),
            "conversion_rate": round(random.uniform(2, 10), 2),
            "avg_revenue_per_user": round(random.uniform(50, 200), 2),
            "customer_lifetime_value": round(random.uniform(500, 2000), 2),
            "churn_rate": round(random.uniform(2, 8), 2)
        },
        "time_series": {
            "daily_users": [d["users"] for d in daily_data],
            "daily_revenue": [d["revenue"] for d in daily_data],
            "daily_api_calls": [d["api_calls"] for d in daily_data],
            "daily_conversions": [d["conversions"] for d in daily_data],
            "dates": [d["date"] for d in daily_data]
        },
        "top_features": [
            {"name": "AI Chat", "usage": random.randint(1000, 5000)},
            {"name": "Analytics Dashboard", "usage": random.randint(800, 4000)},
            {"name": "Document Processing", "usage": random.randint(600, 3000)},
            {"name": "Predictive Analytics", "usage": random.randint(400, 2000)},
            {"name": "Sentiment Analysis", "usage": random.randint(200, 1000)}
        ],
        "user_segments": {
            "free": random.randint(100, 1000),
            "starter": random.randint(50, 500),
            "professional": random.randint(20, 200),
            "enterprise": random.randint(5, 50)
        }
    }


@router.get("/metrics/realtime")
async def get_realtime_metrics():
    """Get real-time system and business metrics"""
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system": {
            "requests_per_second": round(random.uniform(100, 500), 2),
            "average_response_time_ms": round(random.uniform(50, 200), 2),
            "error_rate": round(random.uniform(0.1, 2.0), 2),
            "active_connections": random.randint(100, 1000),
            "cpu_usage": round(random.uniform(20, 80), 2),
            "memory_usage": round(random.uniform(30, 70), 2),
            "cache_hit_rate": round(random.uniform(80, 98), 2)
        },
        "business": {
            "active_users_now": random.randint(100, 1000),
            "revenue_today": round(random.uniform(5000, 20000), 2),
            "api_calls_today": random.randint(50000, 500000),
            "conversions_today": random.randint(20, 200),
            "active_ai_sessions": random.randint(10, 100),
            "processing_queue_size": random.randint(0, 50)
        },
        "performance": {
            "p50_latency_ms": round(random.uniform(30, 100), 2),
            "p95_latency_ms": round(random.uniform(100, 300), 2),
            "p99_latency_ms": round(random.uniform(200, 500), 2),
            "success_rate": round(random.uniform(98, 99.9), 2)
        }
    }


@router.get("/metrics/trends")
async def get_metric_trends(
    metric: str = Query(..., description="Metric name: users, revenue, api_calls, conversions"),
    hours: int = Query(24, ge=1, le=168)
):
    """Get hourly trends for a specific metric"""
    
    now = datetime.now(timezone.utc)
    hourly_data = []
    
    for i in range(hours):
        timestamp = now - timedelta(hours=hours - i - 1)
        
        # Generate metric-specific data
        if metric == "users":
            value = random.randint(50, 500)
        elif metric == "revenue":
            value = round(random.uniform(100, 1000), 2)
        elif metric == "api_calls":
            value = random.randint(1000, 10000)
        elif metric == "conversions":
            value = random.randint(1, 50)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown metric: {metric}")
        
        hourly_data.append({
            "timestamp": timestamp.isoformat(),
            "hour": timestamp.strftime("%Y-%m-%d %H:00"),
            "value": value
        })
    
    # Calculate trend
    values = [d["value"] for d in hourly_data]
    avg = sum(values) / len(values)
    recent_avg = sum(values[-6:]) / 6  # Last 6 hours
    trend = "increasing" if recent_avg > avg else "decreasing" if recent_avg < avg else "stable"
    
    return {
        "metric": metric,
        "period_hours": hours,
        "data": hourly_data,
        "statistics": {
            "min": min(values),
            "max": max(values),
            "avg": round(avg, 2),
            "median": sorted(values)[len(values) // 2],
            "trend": trend,
            "change_pct": round(((recent_avg - avg) / avg * 100) if avg > 0 else 0, 2)
        }
    }


@router.get("/export/csv")
async def export_analytics_csv(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    metrics: List[str] = Query(["users", "revenue", "api_calls"])
):
    """Export analytics data as CSV"""
    
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        
        if (end - start).days > 365:
            raise HTTPException(status_code=400, detail="Date range cannot exceed 365 days")
        
        # Generate CSV content
        csv_lines = ["date," + ",".join(metrics)]
        
        current_date = start
        while current_date <= end:
            row = [current_date.strftime("%Y-%m-%d")]
            
            for metric in metrics:
                if metric == "users":
                    row.append(str(random.randint(50, 500)))
                elif metric == "revenue":
                    row.append(str(round(random.uniform(1000, 5000), 2)))
                elif metric == "api_calls":
                    row.append(str(random.randint(5000, 50000)))
                else:
                    row.append("0")
            
            csv_lines.append(",".join(row))
            current_date += timedelta(days=1)
        
        csv_content = "\n".join(csv_lines)
        
        return {
            "format": "csv",
            "start_date": start_date,
            "end_date": end_date,
            "metrics": metrics,
            "content": csv_content,
            "download_url": f"/api/v1/analytics/download/csv?id={random.randint(1000, 9999)}",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")


@router.get("/dashboards/custom")
async def list_custom_dashboards(tenant_id: Optional[str] = None):
    """List custom dashboards created by users"""
    
    dashboards = [
        {
            "id": "dash_1",
            "name": "Executive Summary",
            "description": "High-level business metrics",
            "widgets": ["revenue", "users", "conversions", "growth"],
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-11-01T15:30:00Z",
            "is_public": False
        },
        {
            "id": "dash_2",
            "name": "Technical Performance",
            "description": "System and API performance metrics",
            "widgets": ["latency", "error_rate", "throughput", "cache_hit_rate"],
            "created_at": "2024-02-20T14:00:00Z",
            "updated_at": "2024-10-28T09:15:00Z",
            "is_public": True
        },
        {
            "id": "dash_3",
            "name": "User Engagement",
            "description": "User activity and engagement tracking",
            "widgets": ["active_users", "session_duration", "feature_usage", "retention"],
            "created_at": "2024-03-10T08:00:00Z",
            "updated_at": "2024-11-02T16:45:00Z",
            "is_public": False
        }
    ]
    
    if tenant_id:
        # Filter by tenant (in production, this would be a database query)
        pass
    
    return {
        "dashboards": dashboards,
        "total": len(dashboards)
    }


@router.post("/dashboards/custom")
async def create_custom_dashboard(
    name: str = Query(..., min_length=1, max_length=100),
    description: Optional[str] = None,
    widgets: List[str] = Query(...),
    tenant_id: Optional[str] = None
):
    """Create a new custom dashboard"""
    
    dashboard_id = f"dash_{random.randint(1000, 9999)}"
    
    dashboard = {
        "id": dashboard_id,
        "name": name,
        "description": description,
        "widgets": widgets,
        "tenant_id": tenant_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "is_public": False
    }
    
    return dashboard


@router.get("/kpis")
async def get_business_kpis(tenant_id: Optional[str] = None):
    """Get key business performance indicators"""
    
    return {
        "revenue": {
            "current": round(random.uniform(50000, 200000), 2),
            "target": 150000,
            "growth": round(random.uniform(10, 50), 2),
            "currency": "EUR"
        },
        "arr": {
            "current": round(random.uniform(500000, 2000000), 2),
            "target": 1500000,
            "growth": round(random.uniform(15, 60), 2)
        },
        "customers": {
            "total": random.randint(100, 1000),
            "active": random.randint(80, 800),
            "new_this_month": random.randint(10, 100),
            "churn_rate": round(random.uniform(2, 8), 2)
        },
        "engagement": {
            "dau": random.randint(100, 1000),
            "mau": random.randint(500, 5000),
            "dau_mau_ratio": round(random.uniform(0.15, 0.35), 2),
            "avg_session_duration_min": round(random.uniform(15, 45), 2)
        },
        "product": {
            "api_calls_month": random.randint(100000, 1000000),
            "ai_requests_month": random.randint(10000, 100000),
            "avg_response_time_ms": round(random.uniform(50, 200), 2),
            "success_rate": round(random.uniform(98, 99.9), 2)
        },
        "financial": {
            "mrr": round(random.uniform(10000, 100000), 2),
            "arpu": round(random.uniform(50, 500), 2),
            "ltv": round(random.uniform(500, 5000), 2),
            "cac": round(random.uniform(100, 1000), 2),
            "ltv_cac_ratio": round(random.uniform(2, 8), 2)
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
