import os
from typing import Dict, Any, List

import httpx
from .common import build_app, get_async_client


app = build_app("omni_resource_guard")

PROM_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
DOCKER_HOST = os.getenv("DOCKER_HOST", "tcp://omni-dind:2375")
RL_CORE_URL = os.getenv("RL_CORE_URL", "http://agent-rl-core:8000")


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok", "service": "omni-resource-guard"}


async def _prom_query(query: str) -> Dict[str, Any]:
    client = get_async_client()
    resp = await client.get(f"{PROM_URL}/api/v1/query", params={"query": query})
    return resp.json()


@app.post("/predict")
async def predict(body: Dict[str, Any]):
    """
    Body example:
    { "window": "5m", "services": ["backend","frontend"] }
    """
    window = body.get("window", "5m")
    services: List[str] = body.get("services", [])

    # Heuristic signals: container CPU saturation and throttling
    cpu_q = f"sum(rate(container_cpu_usage_seconds_total[{window}])) by (container)"
    throttle_q = f"sum(rate(container_cpu_cfs_throttled_seconds_total[{window}])) by (container)"
    mem_q = f"avg(container_memory_usage_bytes) by (container)"

    cpu = await _prom_query(cpu_q)
    throttle = await _prom_query(throttle_q)
    mem = await _prom_query(mem_q)

    # Very simple scoring placeholder
    conflicts = []
    for vec in (cpu.get("data", {}).get("result", []) or []):
        container = vec.get("metric", {}).get("container")
        if not container:
            continue
        try:
            value = float(vec.get("value", [0, 0])[1])
        except Exception:
            value = 0.0
        if value > 0.8:  # arbitrary threshold
            conflicts.append({"container": container, "signal": "cpu", "score": min(1.0, value)})

    result = {
        "conflicts": conflicts,
        "summary": f"Najdenih {len(conflicts)} potencialnih konfliktov virov",
    }
    return result


@app.post("/prevent")
async def prevent(body: Dict[str, Any]):
    """
    Body example:
    { "strategy": "budget-aware", "dry_run": true }
    """
    strategy = body.get("strategy", "budget-aware")
    dry_run = body.get("dry_run", True)

    # Placeholder: delegate learning to RL core (explore/exploit policy updates)
    rl_payload = {"objective": "avoid_resource_conflicts", "strategy": strategy}
    rl_response = None
    try:
        client = get_async_client()
        rr = await client.post(f"{RL_CORE_URL}/train", json=rl_payload)
        if rr.status_code < 300:
            rl_response = rr.json()
    except Exception as e:
        rl_response = {"error": str(e)}

    plan = {
        "actions": [
            {"type": "set_limit", "resource": "cpu", "target": "noisy-container", "value": "750m"},
            {"type": "set_reservation", "resource": "memory", "target": "critical-service", "value": "1Gi"},
        ],
        "dry_run": dry_run,
        "rl_core": rl_response,
    }
    return plan