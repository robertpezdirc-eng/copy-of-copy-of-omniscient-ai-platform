import time
import logging
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

try:
    from prometheus_client import Counter, Histogram
except Exception:  # optional dependency; allow running without it
    Counter = Histogram = None  # type: ignore

logger = logging.getLogger(__name__)


def _create_counter(name: str, desc: str, labels: tuple[str, ...]):
    if not Counter:
        return None
    try:
        return Counter(name, desc, labelnames=labels)
    except Exception:
        logger.warning(f"Prometheus metric {name} already registered; skipping")
        return None


def _create_histogram(name: str, desc: str, labels: tuple[str, ...], buckets: tuple[float, ...]):
    if not Histogram:
        return None
    try:
        return Histogram(name, desc, labelnames=labels, buckets=buckets)
    except Exception:
        logger.warning(f"Prometheus metric {name} already registered; skipping")
        return None


if Counter and Histogram:
    HTTP_REQUESTS_TOTAL = _create_counter(
        "http_requests_total",
        "Total HTTP requests",
        ("method", "path", "status"),
    )

    HTTP_REQUEST_DURATION = _create_histogram(
        "http_request_duration_seconds",
        "HTTP request latency in seconds",
        ("method", "path", "status"),
        (
            0.005,
            0.01,
            0.025,
            0.05,
            0.1,
            0.25,
            0.5,
            1.0,
            2.5,
            5.0,
            10.0,
        ),
    )

    HTTP_ERRORS_TOTAL = _create_counter(
        "http_errors_total",
        "Total HTTP requests that resulted in unhandled exceptions",
        ("method", "path"),
    )
else:
    HTTP_REQUESTS_TOTAL = None  # type: ignore
    HTTP_REQUEST_DURATION = None  # type: ignore
    HTTP_ERRORS_TOTAL = None  # type: ignore


class MetricsMiddleware(BaseHTTPMiddleware):
    """Prometheus metrics for HTTP requests.

    Records total requests, status codes, and duration as a histogram.
    Safe to use even if prometheus_client is not installed (no-ops).
    """

    def __init__(self, app, normalize_paths: bool = True):
        super().__init__(app)
        self.normalize_paths = normalize_paths

    def _path_label(self, path: str) -> str:
        if not self.normalize_paths:
            return path
        # Simple normalization: collapse numeric IDs to :id and long hex tokens to :token
        parts = []
        for seg in path.split("/"):
            if seg.isdigit():
                parts.append(":id")
            elif len(seg) > 24 and all(c in "0123456789abcdefABCDEF" for c in seg):
                parts.append(":token")
            else:
                parts.append(seg)
        return "/".join(parts) or "/"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        method = request.method
        path_label = self._path_label(request.url.path)
        status = "500"

        try:
            response = await call_next(request)
            status = str(response.status_code)
            return response
        except Exception:
            status = "500"
            if HTTP_ERRORS_TOTAL:
                try:
                    HTTP_ERRORS_TOTAL.labels(method=method, path=path_label).inc()
                except Exception:
                    logger.debug("Metrics error: failed to increment HTTP_ERRORS_TOTAL")
            raise
        finally:
            duration = time.perf_counter() - start
            if HTTP_REQUESTS_TOTAL and HTTP_REQUEST_DURATION:
                try:
                    HTTP_REQUESTS_TOTAL.labels(method=method, path=path_label, status=status).inc()
                    HTTP_REQUEST_DURATION.labels(method=method, path=path_label, status=status).observe(duration)
                except Exception:
                    logger.debug("Metrics error: failed to record request metrics")
