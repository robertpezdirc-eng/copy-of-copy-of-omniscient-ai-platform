from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .logging_utils import setup_json_logging
from .metrics import MetricsMiddleware, metrics_asgi_app
from .proxy import router as proxy_router
from .rate_limiter import RedisRateLimiter, get_redis_client
from .secret_manager import load_secrets_from_manager
from .sentry_integration import init_sentry, sentry_middleware
from .settings import settings
from .tracing import init_tracing

logger = logging.getLogger(__name__)

# Global Redis client
redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global redis_client
    
    # Startup
    logger.info(f"Starting {settings.service_name} in {settings.environment} mode")
    
    # Load secrets from Secret Manager (if enabled)
    load_secrets_from_manager()
    
    # Initialize Redis client for rate limiting
    redis_client = await get_redis_client()
    
    # Initialize distributed tracing
    init_tracing(app)
    
    logger.info("Gateway startup complete")
    
    yield
    
    # Shutdown
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")
    
    logger.info("Gateway shutdown complete")


# Setup logging and Sentry before app creation
setup_json_logging()
init_sentry()

app = FastAPI(
    title=settings.service_name,
    version="2.0.0",
    lifespan=lifespan
)

# CORS - permissive by default; tighten in prod via env
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis-based rate limiting (late-binding client resolver)
app.add_middleware(RedisRateLimiter, redis_getter=lambda: redis_client)

# Metrics
if settings.enable_metrics:
    app.add_middleware(MetricsMiddleware)
    app.mount("/metrics", metrics_asgi_app())  # Expose Prometheus metrics

# Proxy routes
app.include_router(proxy_router)

# Wrap with Sentry (no-op if DSN missing)
app = sentry_middleware(app)


@app.get("/")
async def root():
    return {
        "service": settings.service_name,
        "version": "2.0.0",
        "env": settings.environment,
        "features": {
            "rate_limiting": redis_client is not None,
            "tracing": settings.enable_tracing,
            "secret_manager": settings.secret_manager_enabled,
            "openai_configured": settings.openai_api_key is not None,
        }
    }
