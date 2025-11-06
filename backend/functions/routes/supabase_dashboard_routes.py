"""
Supabase Dashboard API Routes
Endpoints for serving data from Supabase to the new dashboard.
"""
from fastapi import APIRouter, HTTPException, Depends
from services.supabase_service import get_supabase_client
from supabase_async import AsyncClient
import logging
from datetime import datetime, timedelta
from collections import Counter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/dashboards/supabase", tags=["Supabase Dashboard"])


@router.get("/revenue/summary")
async def get_revenue_summary(supabase: AsyncClient = Depends(get_supabase_client)):
    """
    Calculates revenue summary for different time periods.
    Assumes a 'transactions' table with 'amount' and 'created_at' columns.
    """
    try:
        # Get the timestamp for 24 hours ago
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        # Fetch transactions from the last 24 hours
        response = await supabase.table("transactions") \
            .select("amount") \
            .gte("created_at", yesterday.isoformat()) \
            .execute()

        if not response.data:
            return {"revenue_24h": 0}

        # Calculate the sum of amounts
        total_revenue = sum(item['amount'] for item in response.data)
        
        return {"revenue_24h": total_revenue}

    except Exception as e:
        logger.error(f"Could not fetch or process revenue data: {e}")
        # Check for specific PostgREST errors, e.g., table not found
        if "relation \"public.transactions\" does not exist" in str(e):
             raise HTTPException(status_code=404, detail="'transactions' table not found in Supabase.")
        raise HTTPException(status_code=500, detail=f"Failed to process revenue data: {str(e)}")


@router.get("/users/growth")
async def get_user_growth_data(supabase: AsyncClient = Depends(get_supabase_client)):
    """
    Fetches user registration data and aggregates it by day for a growth chart.
    """
    try:
        response = await supabase.table("users").select("created_at").execute()
        if not response.data:
            return []
        dates = [datetime.fromisoformat(item['created_at']).date() for item in response.data]
        daily_counts = Counter(dates)
        sorted_items = sorted(daily_counts.items())
        chart_data = [{"date": date.isoformat(), "count": count} for date, count in sorted_items]
        return chart_data
    except Exception as e:
        logger.error(f"Could not fetch or process user growth data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process user growth data: {str(e)}")


@router.get("/{table_name}")
async def get_table_data(table_name: str, supabase: AsyncClient = Depends(get_supabase_client)):
    """
    Fetches all records from a specified Supabase table.
    """
    try:
        response = await supabase.table(table_name).select("*").execute()
        return response.data
    except Exception as e:
        logger.error(f"Could not fetch data from table '{table_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch data from Supabase: {str(e)}")
