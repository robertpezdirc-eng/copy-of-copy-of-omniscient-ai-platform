from __future__ import annotations

import time
from typing import Callable

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST, make_asgi_app
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
    labelnames=["method", "path", "status"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        start = time.perf_counter()
        response: Response | None = None
        try:
            response = await call_next(request)
        finally:
            duration = time.perf_counter() - start
            route = request.scope.get("route")
            path_tmpl = getattr(route, "path", request.url.path)
            status_code = str(response.status_code if response is not None else 500)
            labels = {"method": request.method, "path": path_tmpl, "status": status_code}
            REQUEST_COUNT.labels(**labels).inc()
            REQUEST_LATENCY.labels(**labels).observe(duration)
        # Ensure Response is returned
        if response is None:
            response = Response(status_code=500)
        return response

def metrics_asgi_app():
    return make_asgi_app()
