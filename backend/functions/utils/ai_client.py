"""
AI Worker HTTP client
Calls ai-worker service if AI_WORKER_URL is configured.
"""
import os
from typing import Any, Dict, List, Optional
import httpx

AI_WORKER_URL = os.getenv("AI_WORKER_URL")

class AIWorkerClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or AI_WORKER_URL
        self.client = httpx.AsyncClient(timeout=20)

    async def close(self):
        await self.client.aclose()

    def enabled(self) -> bool:
        return bool(self.base_url)

    async def predict_revenue(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        assert self.base_url
        r = await self.client.post(f"{self.base_url}/predict/revenue", json=payload)
        r.raise_for_status()
        return r.json()

    async def predict_churn(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        assert self.base_url
        r = await self.client.post(f"{self.base_url}/predict/churn", json=payload)
        r.raise_for_status()
        return r.json()

    async def recommend_products(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        assert self.base_url
        r = await self.client.post(f"{self.base_url}/recommend/products", json=payload)
        r.raise_for_status()
        return r.json()

    async def recommend_features(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        assert self.base_url
        r = await self.client.post(f"{self.base_url}/recommend/features", json=payload)
        r.raise_for_status()
        return r.json()

    async def sentiment(self, text: str) -> Dict[str, Any]:
        assert self.base_url
        r = await self.client.post(f"{self.base_url}/sentiment/analyze", json={"text": text})
        r.raise_for_status()
        return r.json()

    async def anomalies(self) -> Dict[str, Any]:
        assert self.base_url
        r = await self.client.get(f"{self.base_url}/anomaly/detect")
        r.raise_for_status()
        return r.json()
