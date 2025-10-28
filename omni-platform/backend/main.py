import os
import sys
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from routers.admin_dashboard import router as admin_router
from routers.support import router as support_router

# Ensure local package imports work whether run as script or module
BASE_DIR = os.path.dirname(__file__)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from routers.omni_brain import router as omni_brain_router
from routers.audio import router as audio_router
from routers.visual import router as visual_router
from routers.learning import router as learning_router
from routers.net_agent import router as net_agent_router
from routers.multi_agent_router import router as multi_agent_router
from routers.agents import router as agents_router
from routers.monitor import router as monitor_router
from routers.billing_agent import router as billing_router
from routers.deployment_agent import router as deployment_router
from routers.security import router as security_router
from routers.reliability import router as reliability_router
from routers.accel_manager import router as accel_manager_router
from routers.notifications import router as notifications_router
from routers.access_controller import router as access_router
from routers.file_edit import router as file_edit_router
from routers.websocket_sensor import router as websocket_sensor_router
from routers.semantic_docs import router as semantic_docs_router
from routers.saga import router as saga_router
from routers.finops_agent import router as finops_router
from routers.model_governance import router as model_router
from routers.policy_manager_router import router as policy_router
from routers.rl_core_agent import router as rl_core_router
from routers.advertising_agent import router as advertising_router
from routers.billing_tiers import router as billing_tiers_router
from routers.api_monetization import router as api_monetization_router
from routers.specialized_agents import router as specialized_agents_router
from routers.white_label import router as white_label_router
from routers.enterprise_packages import router as enterprise_packages_router
from routers.analytics import router as analytics_router
from routers.waitlist import router as waitlist_router

# Optional: add path to AI module if present
sys.path.append('../modules/omni-brain-maxi-ultra')

# Load environment variables from .env if present
load_dotenv()

app = FastAPI()

# Prometheus metrics
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "http_status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "Request latency (seconds)", ["endpoint"])

# Resolve repo root and frontend dir
REPO_ROOT = os.path.abspath(os.path.join(BASE_DIR, os.pardir, os.pardir))
FRONTEND_DIR = os.path.join(REPO_ROOT, "frontend")
FRONTEND_DIST = os.path.join(FRONTEND_DIR, "dist")
if os.path.isdir(FRONTEND_DIST):
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIST), name="frontend")
elif os.path.isdir(FRONTEND_DIR):
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request metrics middleware
@app.middleware("http")
async def metrics_middleware(request, call_next):
    from time import perf_counter
    start = perf_counter()
    response = await call_next(request)
    latency = perf_counter() - start
    endpoint = request.url.path
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(latency)
    try:
        status = str(response.status_code)
    except Exception:
        status = "0"
    REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, http_status=status).inc()
    return response

# Routers
app.include_router(omni_brain_router)
app.include_router(audio_router)
app.include_router(visual_router)
app.include_router(learning_router)
app.include_router(net_agent_router)
app.include_router(multi_agent_router)
app.include_router(agents_router)
app.include_router(monitor_router)
app.include_router(billing_router, prefix="/api/v1")
app.include_router(deployment_router, prefix="/api/v1")
app.include_router(security_router, prefix="/api/v1")
app.include_router(reliability_router, prefix="/api/v1")
app.include_router(accel_manager_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(access_router, prefix="/api/v1")
app.include_router(file_edit_router, prefix="/api/v1")
app.include_router(websocket_sensor_router, prefix="/api/v1")
app.include_router(semantic_docs_router, prefix="/api/v1")
app.include_router(saga_router, prefix="/api/v1")
app.include_router(finops_router, prefix="/api/v1")
app.include_router(model_router, prefix="/api/v1")
app.include_router(policy_router, prefix="/api/v1")
app.include_router(rl_core_router, prefix="/api/v1")
app.include_router(advertising_router, prefix="/api/v1")
app.include_router(billing_tiers_router, prefix="/api/v1")
app.include_router(api_monetization_router, prefix="/api/v1")
app.include_router(specialized_agents_router, prefix="/api/v1")
app.include_router(white_label_router, prefix="/api/v1")
app.include_router(enterprise_packages_router, prefix="/api/v1")
app.include_router(support_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(waitlist_router, prefix="/api/v1")
app.include_router(admin_router)

@app.get("/api/health")
def health():
    return JSONResponse({"status": "ok"})

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/")
def serve_landing():
    index_candidates = [
        os.path.join(FRONTEND_DIST, "index.html"),
        os.path.join(FRONTEND_DIR, "index.html"),
    ]
    for p in index_candidates:
        if os.path.exists(p):
            return FileResponse(p)
    return JSONResponse({"error": "frontend index.html not found"}, status_code=404)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)