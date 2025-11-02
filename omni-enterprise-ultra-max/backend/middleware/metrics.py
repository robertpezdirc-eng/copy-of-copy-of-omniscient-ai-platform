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


if Counter and Histogram:
    try:
        HTTP_REQUESTS_TOTAL = Counter(
            "http_requests_total",
            "Total HTTP requests",
            labelnames=("method", "path", "status"),
        )
    except ValueError:
        # Already registered; retrieve from registry
        from prometheus_client import REGISTRY
        HTTP_REQUESTS_TOTAL = [c for c in REGISTRY._collector_to_names if hasattr(c, '_name') and c._name == 'http_requests_total'][0]

    try:
        HTTP_REQUEST_DURATION = Histogram(
            "http_request_duration_seconds",
            "HTTP request latency in seconds",
            labelnames=("method", "path", "status"),
            buckets=(
                0.005,
            0.01,
            0.025,
            0.05,
            0.1,
            0.25,
            0.5,
            1.0,
            2.5,
                2.5,
                5.0,
                10.0,
            ),
        )
    except ValueError:
        # Already registered
        from prometheus_client import REGISTRY
        HTTP_REQUEST_DURATION = [c for c in REGISTRY._collector_to_names if hasattr(c, '_name') and c._name == 'http_request_duration_seconds'][0]

    HTTP_ERRORS_TOTAL = Counter(
        "http_errors_total",
        "Total HTTP requests that resulted in unhandled exceptions",
        labelnames=("method", "path"),
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
import time
import logging
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

try:
    from prometheus_client import Counter, Histogram
except Exception:  # pragma: no cover - optional dependency
    Counter = Histogram = None  # type: ignore

logger = logging.getLogger(__name__)


if Counter and Histogram:
    HTTP_REQUESTS_TOTAL = Counter(
        "http_requests_total",
        "Total HTTP requests",
        labelnames=("method", "path", "status"),
    )

    HTTP_REQUEST_DURATION = Histogram(
        "http_request_duration_seconds",
        "HTTP request latency in seconds",
        labelnames=("method", "path", "status"),
        buckets=(
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

    HTTP_ERRORS_TOTAL = Counter(
        "http_errors_total",
        "Total HTTP requests that resulted in unhandled exceptions",
        labelnames=("method", "path"),
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
                except Exception:  # pragma: no cover
                    logger.debug("Metrics error: failed to increment HTTP_ERRORS_TOTAL")
            raise
        finally:
            duration = time.perf_counter() - start
            if HTTP_REQUESTS_TOTAL and HTTP_REQUEST_DURATION:
                try:
                    HTTP_REQUESTS_TOTAL.labels(method=method, path=path_label, status=status).inc()
                    HTTP_REQUEST_DURATION.labels(method=method, path=path_label, status=status).observe(duration)
                except Exception:  # pragma: no cover
                    logger.debug("Metrics error: failed to record request metrics")
import time
import logging
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

try:
    from prometheus_client import Counter, Histogram
except Exception:  # pragma: no cover - optional dependency
    Counter = Histogram = None  # type: ignore

logger = logging.getLogger(__name__)


if Counter and Histogram:
    HTTP_REQUESTS_TOTAL = Counter(
        "http_requests_total",
        "Total HTTP requests",
        labelnames=("method", "path", "status"),
    )

    HTTP_REQUEST_DURATION = Histogram(
        "http_request_duration_seconds",
        "HTTP request latency in seconds",
        labelnames=("method", "path", "status"),
        buckets=(
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

    HTTP_ERRORS_TOTAL = Counter(
        "http_errors_total",
        "Total HTTP requests that resulted in unhandled exceptions",
        labelnames=("method", "path"),
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
                except Exception:  # pragma: no cover
                    logger.debug("Metrics error: failed to increment HTTP_ERRORS_TOTAL")
            raise
        finally:
            duration = time.perf_counter() - start
            if HTTP_REQUESTS_TOTAL and HTTP_REQUEST_DURATION:
                try:
                    HTTP_REQUESTS_TOTAL.labels(method=method, path=path_label, status=status).inc()
                    HTTP_REQUEST_DURATION.labels(method=method, path=path_label, status=status).observe(duration)
                except Exception:  # pragma: no cover
                    logger.debug("Metrics error: failed to record request metrics")
