from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

logger = logging.getLogger(__name__)

class PerformanceMonitor(BaseHTTPMiddleware):
    def __init__(self, app, slow_request_threshold=1.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold

    async def dispatch(self, request, call_next):
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time

        if duration > self.slow_request_threshold:
            logger.warning(f"Slow request detected: {request.method} {request.url.path} took {duration:.4f}s")

        # Add performance headers
        response.headers["X-Response-Time"] = f"{duration:.4f}s"

        return response
