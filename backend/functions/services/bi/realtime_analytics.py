from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RealtimeAnalyticsService:
    """Real-time analytics aggregation with in-memory store and optional Redis backup.
    
    Tracks metrics like API calls, user events, revenue, errors in sliding windows.
    Push updates to connected WebSocket clients for live BI dashboards.
    """

    def __init__(self) -> None:
        self._metrics: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"count": 0, "sum": 0.0, "last_updated": None})
        self._lock = asyncio.Lock()
        self._subscribers: List[asyncio.Queue] = []

    async def record_event(self, metric_name: str, value: float = 1.0, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record an event and update aggregate metrics."""
        async with self._lock:
            m = self._metrics[metric_name]
            m["count"] += 1
            m["sum"] += value
            m["last_updated"] = datetime.now(timezone.utc).isoformat()
            if metadata:
                m.setdefault("metadata", []).append(metadata)
                # Keep only last 100 metadata entries
                if len(m["metadata"]) > 100:
                    m["metadata"] = m["metadata"][-100:]
        
        # Notify subscribers
        await self._notify_subscribers({"event": "metric_update", "metric": metric_name, "value": value})

    async def get_metrics(self) -> Dict[str, Any]:
        """Get current aggregated metrics snapshot."""
        async with self._lock:
            return {k: dict(v) for k, v in self._metrics.items()}

    async def get_metric(self, metric_name: str) -> Dict[str, Any]:
        """Get a single metric."""
        async with self._lock:
            return dict(self._metrics.get(metric_name, {}))

    async def subscribe(self) -> asyncio.Queue:
        """Subscribe to real-time metric updates. Returns a queue that receives update dicts."""
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._subscribers.append(q)
        return q

    async def unsubscribe(self, queue: asyncio.Queue) -> None:
        """Unsubscribe from updates."""
        async with self._lock:
            if queue in self._subscribers:
                self._subscribers.remove(queue)

    async def _notify_subscribers(self, update: Dict[str, Any]) -> None:
        """Push update to all subscribers (non-blocking)."""
        dead_queues = []
        for q in self._subscribers:
            try:
                q.put_nowait(update)
            except asyncio.QueueFull:
                logger.warning("Subscriber queue full, dropping update")
            except Exception:
                dead_queues.append(q)
        
        if dead_queues:
            async with self._lock:
                for dq in dead_queues:
                    if dq in self._subscribers:
                        self._subscribers.remove(dq)


_analytics_singleton: Optional[RealtimeAnalyticsService] = None


def get_realtime_analytics() -> RealtimeAnalyticsService:
    global _analytics_singleton
    if _analytics_singleton is None:
        _analytics_singleton = RealtimeAnalyticsService()
    return _analytics_singleton
