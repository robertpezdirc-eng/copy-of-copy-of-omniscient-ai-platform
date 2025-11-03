from __future__ import annotations

import os
import importlib
from .settings import settings


def init_sentry() -> None:
    dsn = settings.sentry_dsn
    if not dsn:
        return
    try:
        sentry_sdk = importlib.import_module("sentry_sdk")
    except Exception:  # pragma: no cover - optional
        return
    sentry_sdk.init(
        dsn=dsn,
        environment=settings.environment,
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.01")),
    )


def sentry_middleware(app):
    # Wrap app with Sentry if DSN present
    if not settings.sentry_dsn:
        return app
    try:
        asgi_mod = importlib.import_module("sentry_sdk.integrations.asgi")
        sentry_asgi_mw = getattr(asgi_mod, "SentryAsgiMiddleware", None)
    except Exception:  # pragma: no cover - optional
        return app
    if sentry_asgi_mw is None:
        return app
    return sentry_asgi_mw(app)
