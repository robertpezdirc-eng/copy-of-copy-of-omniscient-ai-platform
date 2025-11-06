from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

logger = logging.getLogger(__name__)

class UsageTracker(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.request_count = 0
        self.start_time = time.time()

    async def dispatch(self, request, call_next):
        self.request_count += 1

        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        # Log usage metrics
        logger.info(f"Request: {request.method} {request.url.path} - Duration: {duration:.4f}s - Status: {response.status_code}")

        return response
