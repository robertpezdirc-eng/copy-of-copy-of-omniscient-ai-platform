from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .logging_utils import setup_json_logging
from .metrics import MetricsMiddleware, metrics_asgi_app
from .proxy import router as proxy_router
from .rate_limiter import RedisRateLimiter, get_redis_client
from .redis_metrics import start_redis_metrics_collection
from .response_cache import ResponseCache
from .secret_manager import load_secrets_from_manager
from .sentry_integration import init_sentry, sentry_middleware
from .settings import settings
from .tracing import init_tracing

logger = logging.getLogger(__name__)

# Global Redis client
redis_client = None

# Redis metrics collection task
redis_metrics_task = None

# Global HTTP clients for connection pooling
upstream_client: httpx.AsyncClient | None = None
openai_client: httpx.AsyncClient | None = None

# Global response cache
response_cache: ResponseCache | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global redis_client, upstream_client, openai_client, response_cache, redis_metrics_task

    # Startup
    logger.info(f"Starting {settings.service_name} in {settings.environment} mode")

    # Load secrets from Secret Manager (if enabled)
    load_secrets_from_manager()

    # Initialize Redis client for rate limiting
    redis_client = await get_redis_client()

    # Start Redis metrics collection in background
    if redis_client and settings.enable_metrics:
        redis_metrics_task = asyncio.create_task(
            start_redis_metrics_collection(redis_client, interval_seconds=30)
        )
        logger.info("Redis metrics collection started")

    # Initialize HTTP clients for connection pooling
    timeout = httpx.Timeout(
        connect=settings.connect_timeout,
        read=settings.request_timeout,
        write=settings.request_timeout,
        pool=5.0,
    )
    upstream_client = httpx.AsyncClient(
        base_url=settings.upstream_url,
        timeout=timeout,
        trust_env=True,
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
    )
    openai_client = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0),
        trust_env=True,
        limits=httpx.Limits(max_connections=50, max_keepalive_connections=10)
    )
    logger.info("HTTP clients initialized with connection pooling")

    # Initialize response cache with configurable TTL
    response_cache = ResponseCache(
        redis_client=redis_client,
        default_ttl=settings.response_cache_ttl_seconds,
    )

    # Initialize distributed tracing
    init_tracing(app)

    logger.info("Gateway startup complete")

    yield

    # Shutdown
    # Cancel Redis metrics collection task
    if redis_metrics_task:
        redis_metrics_task.cancel()
        try:
            await redis_metrics_task
        except asyncio.CancelledError:
            pass
        logger.info("Redis metrics collection stopped")

    if upstream_client:
        await upstream_client.aclose()
        logger.info("Upstream HTTP client closed")

    if openai_client:
        await openai_client.aclose()
        logger.info("OpenAI HTTP client closed")

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
            "response_cache": response_cache is not None,
            "connection_pooling": upstream_client is not None,
            "tracing": settings.enable_tracing,
            "secret_manager": settings.secret_manager_enabled,
        }
    }


# Utility functions to get clients (for use in other modules)
def get_upstream_client() -> httpx.AsyncClient | None:
    """Get the pooled upstream HTTP client."""
    return upstream_client


def get_openai_client() -> httpx.AsyncClient | None:
    """Get the pooled OpenAI HTTP client."""
    return openai_client


def get_response_cache() -> ResponseCache | None:
    """Get the response cache instance."""
    return response_cache
