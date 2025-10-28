from fastapi import FastAPI, Request
from prometheus_client import Counter, Gauge, Histogram, generate_latest, REGISTRY
from prometheus_client import CONTENT_TYPE_LATEST
from starlette.responses import Response
import os, time, re
import httpx
from typing import Optional


def build_app(agent_name: str) -> FastAPI:
    app = FastAPI(title=agent_name)

    # Prometheus metric names must match [a-zA-Z_:][a-zA-Z0-9_:]* (no hyphens)
    metric_prefix = re.sub(r"[^a-zA-Z0-9_:]", "_", agent_name)

    req_counter = Counter(f"{metric_prefix}_requests_total", "Total HTTP requests", ["path", "method", "status"])
    latency_hist = Histogram(f"{metric_prefix}_request_latency_seconds", "Request latency", ["path", "method"])
    healthy = Gauge(f"{metric_prefix}_healthy", "Health status (1=up,0=down)")

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start = time.time()
        try:
            response = await call_next(request)
            status = getattr(response, 'status_code', 500)
        except Exception:
            status = 500
            raise
        finally:
            elapsed = time.time() - start
            path = request.url.path
            method = request.method
            latency_hist.labels(path=path, method=method).observe(elapsed)
            req_counter.labels(path=path, method=method, status=str(status)).inc()
        return response

    @app.get("/health")
    async def health():
        healthy.set(1)
        return {"status": "ok", "agent": agent_name}

    @app.get("/metrics")
    async def metrics():
        data = generate_latest(REGISTRY)
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)

    return app


_async_client: Optional[httpx.AsyncClient] = None


def get_async_client() -> httpx.AsyncClient:
    global _async_client
    if _async_client is None:
        _async_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            headers={"User-Agent": "omni-agents"},
        )
    return _async_client


def getenv_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return str(v).lower() in ["1", "true", "yes", "on"]