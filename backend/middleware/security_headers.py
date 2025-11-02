from __future__ import annotations

from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add common security headers to all responses.

    Note: Tune policies for your app needs (CSP not included here to avoid
    breaking existing frontend; add when ready).
    """

    def __init__(self, app: ASGIApp, *, hsts_max_age: int = 31536000, include_subdomains: bool = True) -> None:
        super().__init__(app)
        self.hsts_value = f"max-age={hsts_max_age}{'; includeSubDomains' if include_subdomains else ''}"

    async def dispatch(self, request, call_next: Callable):
        resp: Response = await call_next(request)
        # HSTS (only applies over HTTPS)
        resp.headers.setdefault("Strict-Transport-Security", self.hsts_value)
        # MIME sniffing protection
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        # Clickjacking protection
        resp.headers.setdefault("X-Frame-Options", "DENY")
        # Referrer policy
        resp.headers.setdefault("Referrer-Policy", "no-referrer")
        # Permissions policy (restrict powerful features)
        resp.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        # Cross-Origin Opener Policy for isolation
        resp.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        # Cross-Origin Resource Policy
        resp.headers.setdefault("Cross-Origin-Resource-Policy", "same-site")
        # Content-Security-Policy (report-only mode for gradual rollout)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' wss: https:; "
            "font-src 'self' data:; "
            "frame-ancestors 'none'"
        )
        resp.headers.setdefault("Content-Security-Policy-Report-Only", csp)
        return resp
