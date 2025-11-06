"""
KPI Service - Generates and analyzes Key Performance Indicators.
"""
import json
from datetime import datetime, timedelta
import logging
from typing import Any, Dict, Optional

from backend.database import CacheManager
from backend.services.ai.ollama_service import get_ollama_service

logger = logging.getLogger(__name__)

class KPIService:
    """Service for generating and analyzing business KPIs."""

    def __init__(self):
        self.ollama_service = get_ollama_service()

    async def get_kpis(self) -> Dict[str, Any]:
        """Get KPIs from cache or generate them if not present."""
        cache_key = "business_kpis"
        cached_kpis = await CacheManager.get(cache_key)
        if cached_kpis:
            return json.loads(cached_kpis)

        kpis = await self._generate_kpis()
        await CacheManager.set(cache_key, json.dumps(kpis, default=str), ttl=3600)  # Cache for 1 hour
        return kpis

    async def _generate_kpis(self) -> Dict[str, Any]:
        """Generate KPIs using internal data and AI insights."""
        # In a real scenario, you would fetch this from a database
        raw_data = self._get_mock_data()

        # Use Ollama to generate insights
        prompt = f"Analyze the following sales data and provide a summary of key trends and insights: {json.dumps(raw_data)}"
        ai_summary = await self.ollama_service.generate(prompt)

        # Combine raw data with AI summary
        kpis = {
            "generated_at": datetime.utcnow(),
            "revenue_last_30d": sum(d['revenue'] for d in raw_data['sales_data']),
            "new_users_last_30d": sum(d['new_users'] for d in raw_data['user_metrics']),
            "ai_powered_summary": ai_summary.get("reply", ""),
            "raw_data_summary": raw_data # For context
        }

        return kpis

    def _get_mock_data(self) -> Dict[str, Any]:
        """Generate mock data for KPI generation."""
        today = datetime.utcnow().date()
        return {
            "sales_data": [
                {"date": str(today - timedelta(days=i)), "revenue": 1000 + i * 100, "transactions": 50 + i * 2} for i in range(30)
            ],
            "user_metrics": [
                {"date": str(today - timedelta(days=i)), "new_users": 50 + i * 5, "active_users": 500 + i * 20} for i in range(30)
            ]
        }

# Singleton instance
_kpi_service: Optional[KPIService] = None

def get_kpi_service() -> KPIService:
    """Get or create KPIService singleton."""
    global _kpi_service
    if _kpi_service is None:
        _kpi_service = KPIService()
    return _kpi_service
