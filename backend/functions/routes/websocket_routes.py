from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from services.bi import get_realtime_analytics

logger = logging.getLogger(__name__)

router = APIRouter()


class MetricRecordPayload(BaseModel):
    metric_name: str
    value: float = 1.0
    metadata: Dict[str, Any] | None = None


@router.get("/info")
def info():
    return {"ws": "on"}


@router.post("/record")
async def record_metric(payload: MetricRecordPayload):
    """Record a BI metric event (REST endpoint for convenience)."""
    analytics = get_realtime_analytics()
    await analytics.record_event(payload.metric_name, payload.value, payload.metadata)
    return {"ok": True}


@router.get("/metrics")
async def get_metrics():
    """Get current aggregated metrics snapshot."""
    analytics = get_realtime_analytics()
    return await analytics.get_metrics()


@router.websocket("/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket endpoint for streaming real-time BI dashboard updates.
    
    Clients connect and receive JSON messages whenever metrics change.
    """
    await websocket.accept()
    analytics = get_realtime_analytics()
    queue = await analytics.subscribe()
    
    try:
        # Send initial snapshot
        initial = await analytics.get_metrics()
        await websocket.send_json({"type": "snapshot", "data": initial})
        
        # Stream updates
        while True:
            try:
                update = await asyncio.wait_for(queue.get(), timeout=30.0)
                await websocket.send_json({"type": "update", "data": update})
            except asyncio.TimeoutError:
                # Send keepalive ping
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as exc:
        logger.error("WebSocket error: %s", exc)
    finally:
        await analytics.unsubscribe(queue)
