import os
import sys
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routers.admin_dashboard import router as admin_router

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

# Optional: add path to AI module if present
sys.path.append('../modules/omni-brain-maxi-ultra')

# Load environment variables from .env if present
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
app.include_router(admin_router)

@app.get("/api/health")
def health():
    return JSONResponse({"status": "ok"})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)