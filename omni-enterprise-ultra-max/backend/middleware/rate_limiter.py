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

        # Simple rate limiting: 100 requests per minute per IP
        if client_ip in self.requests:
            if current_time - self.requests[client_ip] < 60:
                if len([t for t in self.requests if t > current_time - 60]) > 100:
                    return JSONResponse(
                        status_code=429,
                        content={"error": "Rate limit exceeded"}
                    )
        else:
            self.requests[client_ip] = []

        self.requests[client_ip].append(current_time)

        # Clean up old entries
        self.requests[client_ip] = [t for t in self.requests[client_ip] if t > current_time - 60]

        response = await call_next(request)
        return response
