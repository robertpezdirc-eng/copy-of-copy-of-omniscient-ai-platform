"""
OMNI ENTERPRISE ULTRA MAX - Master Backend API
Unified backend integrating all enterprise features
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
from datetime import datetime, timezone
import logging
from utils.logging_filters import PIIRedactionFilter

# Database initialization
from database import init_databases, close_databases

# Import critical routes
from routes.ai_routes import ai_router
from routes.langchain_routes import router as langchain_router
from routes.tickets_routes import router as tickets_router # Always load tickets
from routes.kpi_routes import router as kpi_router # Always load kpis

# Import middleware components
from middleware.rate_limiter import RateLimiter
from middleware.usage_tracker import UsageTracker
from middleware.performance_monitor import PerformanceMonitor
from middleware.metrics import MetricsMiddleware
from middleware.security_headers import SecurityHeadersMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Attach simple PII redaction to root logger handlers
for handler in logging.getLogger().handlers:
    handler.addFilter(PIIRedactionFilter())


# Determine minimal startup mode
_omnimin_env = os.getenv("OMNI_MINIMAL")
if _omnimin_env is None:
    OMNI_MINIMAL = os.getenv("K_SERVICE") is not None
else:
    OMNI_MINIMAL = _omnimin_env.lower() in ("1", "true", "yes")

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources"""
    logger.info("🚀 Starting OMNI Enterprise Ultra Max API...")
    await init_databases()
    logger.info("✅ All systems operational")
    yield
    logger.info("🔄 Shutting down gracefully...")
    await close_databases()
    logger.info("✅ Shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    title="Omni Enterprise Ultra Max API",
    description="Revolutionary Enterprise Platform API - 10 Years Ahead",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Add middleware
import os as _os
from middleware.internal_prefix import InternalPrefixStripper

_run_as_internal = _os.getenv("RUN_AS_INTERNAL", "0").lower() in ("1", "true", "yes")
_slow_threshold = float(_os.getenv("PERF_SLOW_THRESHOLD_SEC", "1.0"))
_enable_response_cache = os.getenv("ENABLE_RESPONSE_CACHE", "1").lower() in ("1", "true", "yes")

if _run_as_internal:
    app.add_middleware(InternalPrefixStripper, prefix="/internal")

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(PerformanceMonitor, slow_request_threshold=_slow_threshold)

if _enable_response_cache and not _run_as_internal:
    try:
        from middleware.response_cache import ResponseCacheMiddleware
        from database import redis_client as _redis_cache
        if _redis_cache:
            app.add_middleware(ResponseCacheMiddleware, redis_client=_redis_cache, default_ttl=60)
            logger.info("Response cache middleware enabled (TTL: 60s)")
        else:
            logger.warning("Response cache disabled: Redis not available")
    except Exception as e:
        logger.warning(f"Failed to enable response cache middleware: {e}")

if not _run_as_internal:
    app.add_middleware(UsageTracker)
    app.add_middleware(RateLimiter)
else:
    logger.info("Running in INTERNAL mode: RateLimiter and UsageTracker disabled; '/internal' prefix supported")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "https://omni-ultra.com", "https://*.omni-ultra.com"],
    allow_origin_regex=r"https://.*\.run\.app|https://.*\.vercel\.app|https://.*\.loca\.lt",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    from prometheus_client import make_asgi_app as _make_asgi_app
    app.mount("/metrics", _make_asgi_app())
except Exception:
    logger.info("Prometheus client not installed; /metrics not exposed")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat(), "version": "2.0.0"}

@app.get("/api/v1/omni/summary")
async def get_system_summary():
    return {"revenue_24h": "€847,293", "active_users": 12847, "api_calls_hour": 45230, "uptime": "99.98%"}

def _register_routers(app: FastAPI) -> None:
    app.include_router(ai_router, prefix="/api/v1/ai", tags=["AI Services"])
    app.include_router(langchain_router, prefix="/api/v1/langchain", tags=["LangChain"])
    app.include_router(tickets_router, prefix="/api/v1", tags=["Tickets"])
    app.include_router(kpi_router, prefix="/api/v1", tags=["KPIs"])

    def _try_import_and_register(router_path: str, router_name: str, prefix: str = "", tags: list = []):
        try:
            module = __import__(router_path, fromlist=[router_name])
            router = getattr(module, router_name)
            app.include_router(router, prefix=prefix, tags=tags)
            logger.info(f"✅ {router_name} routes registered")
        except Exception as e:
            logger.warning(f"Skipping {router_name} routes: {e}")

    _try_import_and_register("routes.ollama_health_routes", "ollama_health_router", "/api/v1/ollama", ["Ollama Service"])
    _try_import_and_register("routes.dashboard_builder_routes", "router", tags=["Dashboard Builder"])
    _try_import_and_register("routes.realtime_dashboard_routes", "router", tags=["Real-time Dashboard"])
    _try_import_and_register("routes.supabase_dashboard_routes", "router", tags=["Supabase Dashboard"])
    _try_import_and_register("routes.rag_routes", "router", tags=["RAG"])
    _try_import_and_register("routes.gdpr_routes", "router", tags=["GDPR"])

    if OMNI_MINIMAL:
        logger.info("OMNI_MINIMAL=1 active: skipping optional routers for fast, reliable startup")
        return

    # All other optional routes
    _try_import_and_register("routes.auth_routes", "router", "/api/v1/auth", ["Authentication & Users"])
    # ... more optional routes here

_register_routers(app)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {str(exc)}")
    return JSONResponse(status_code=500, content={"error": "Internal server error", "message": str(exc)})

@app.get("/")
async def root():
    return {"name": "Omni Enterprise Ultra Max API", "version": "2.0.0", "status": "operational"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    _reload = os.getenv("UVICORN_RELOAD", "0").lower() in ("1", "true", "yes")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=_reload, log_level="info")
