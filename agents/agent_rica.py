import os
import httpx
from datetime import datetime, timedelta
from .common import build_app
from pydantic import BaseModel

app = build_app("omni_rica")


class CorrelateSpec(BaseModel):
    query: str = "rate(http_requests_total[5m])"
    loki_query: str = "{app=\"omni-backend\"}"
    since_minutes: int = 30


def _ts_range(minutes: int):
    now = datetime.utcnow()
    start = now - timedelta(minutes=minutes)
    return int(start.timestamp()), int(now.timestamp())


@app.post("/correlate")
async def correlate(spec: CorrelateSpec):
    prom = os.getenv("PROMETHEUS_URL", "http://omni-prometheus:9090")
    loki = os.getenv("LOKI_URL", "http://omni-loki:3100")
    start, end = _ts_range(spec.since_minutes)

    async with httpx.AsyncClient(timeout=10.0) as client:
        prom_resp = await client.get(f"{prom}/api/v1/query_range", params={
            "query": spec.query,
            "start": start,
            "end": end,
            "step": 30,
        })
        loki_resp = await client.get(f"{loki}/loki/api/v1/query_range", params={
            "query": spec.loki_query,
            "start": start * 1_000_000_000,  # ns
            "end": end * 1_000_000_000,
            "step": 30,
        })

    return {
        "prometheus": prom_resp.json(),
        "loki": loki_resp.json(),
        "window": {"start": start, "end": end},
    }


@app.get("/incidents")
async def incidents():
    # Stub: povezava z JIRA (ali GitHub Issues) – osnutek
    return {"incidents": [], "source": "jira/github", "note": "configure JIRA_URL/JIRA_API_TOKEN/GITHUB_TOKEN"}