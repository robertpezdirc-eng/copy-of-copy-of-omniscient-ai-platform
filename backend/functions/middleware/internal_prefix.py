from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from typing import Callable

class InternalPrefixStripper(BaseHTTPMiddleware):
    """If a path starts with /internal, strip that prefix and continue.
    Allows exposing the same routes under an /internal namespace for gateways.
    """
    def __init__(self, app, prefix: str = "/internal"):
        super().__init__(app)
        self.prefix = prefix

    async def dispatch(self, request: Request, call_next: Callable):
        path = request.scope.get("path", "")
        if path.startswith(self.prefix):
            # Mutate the ASGI scope in-place to drop the prefix
            new_path = path[len(self.prefix):] or "/"
            request.scope["path"] = new_path
        return await call_next(request)
