import pytest
import asyncio

from backend.services.bi.realtime_analytics import RealtimeAnalyticsService


@pytest.mark.asyncio
async def test_record_and_get_metrics():
    svc = RealtimeAnalyticsService()
    await svc.record_event("api_calls", value=1.0)
    await svc.record_event("api_calls", value=2.0)
    await svc.record_event("revenue", value=99.99, metadata={"currency": "USD"})
    
    metrics = await svc.get_metrics()
    assert metrics["api_calls"]["count"] == 2
    assert metrics["api_calls"]["sum"] == 3.0
    assert metrics["revenue"]["count"] == 1
    assert metrics["revenue"]["sum"] == 99.99
    assert metrics["revenue"]["metadata"][0]["currency"] == "USD"


@pytest.mark.asyncio
async def test_subscribe_and_notify():
    svc = RealtimeAnalyticsService()
    q = await svc.subscribe()
    
    await svc.record_event("test_metric", value=5.0)
    
    # Should receive update
    update = await asyncio.wait_for(q.get(), timeout=1.0)
    assert update["event"] == "metric_update"
    assert update["metric"] == "test_metric"
    assert update["value"] == 5.0
    
    await svc.unsubscribe(q)
