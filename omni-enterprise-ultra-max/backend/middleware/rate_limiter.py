from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time

class RateLimiter(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.requests = {}

    async def dispatch(self, request, call_next):
        client_ip = request.client.host
        current_time = time.time()

        # Initialize if not exists
        if client_ip not in self.requests:
            self.requests[client_ip] = []

        # Clean up old entries
        self.requests[client_ip] = [t for t in self.requests[client_ip] if t > current_time - 60]

        # Simple rate limiting: 100 requests per minute per IP
        if len(self.requests[client_ip]) >= 100:
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded"}
            )

        self.requests[client_ip].append(current_time)

        response = await call_next(request)
        return response
