"""
Minimal backend entrypoint for Cloud Run deployment.
Only essential routes, no heavy imports.
"""
import os
import logging
from datetime import datetime, timezone
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Omni Backend (Minimal Mode)",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "name": "Omni Backend API (Minimal)",
        "version": "2.0.0",
        "status": "operational",
        "mode": "minimal",
        "documentation": "/api/docs",
        "health": "/api/health"
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0-minimal",
        "mode": "minimal"
    }

# Minimal AI chat endpoint
from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    prompt: str
    model: Optional[str] = "gpt-4o-mini"
    temperature: Optional[float] = 0.7

# Optional lightweight background logging
try:
    from utils.background_tasks import schedule_lightweight_task, log_api_call  # type: ignore
except Exception:
    schedule_lightweight_task = None  # type: ignore
    log_api_call = None  # type: ignore


@app.post("/api/v1/ai/chat")
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """Minimal chat endpoint - delegates to OpenAI via OmniBrainAdapter"""
    import time as _time
    _start = _time.time()
    try:
        from adapters.omni_brain_adapter import OmniBrainAdapter
        brain = OmniBrainAdapter()
        result = await brain.invoke({
            "prompt": request.prompt,
            "model": request.model,
            "temperature": request.temperature
        })
        # Log in background (best-effort)
        if schedule_lightweight_task and log_api_call:
            duration_ms = (_time.time() - _start) * 1000
            schedule_lightweight_task(
                background_tasks,
                log_api_call,
                "/api/v1/ai/chat",
                "system",
                duration_ms,
            )
        return result
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {
            "error": str(e),
            "reply": "",
            "model": request.model
        }

@app.post("/api/v1/ai/generate/text")
async def generate_text(prompt: str, background_tasks: BackgroundTasks):
    """Legacy text generation endpoint"""
    import time as _time
    _start = _time.time()
    try:
        from adapters.omni_brain_adapter import OmniBrainAdapter
        brain = OmniBrainAdapter()
        result = await brain.invoke({"prompt": prompt})
        resp = {
            "prompt": prompt,
            "generated_text": result.get("reply", ""),
            "tokens_used": 0,
            "model": "gpt-4o-mini"
        }
        # Log in background (best-effort)
        if schedule_lightweight_task and log_api_call:
            duration_ms = (_time.time() - _start) * 1000
            schedule_lightweight_task(
                background_tasks,
                log_api_call,
                "/api/v1/ai/generate/text",
                "system",
                duration_ms,
            )
        return resp
    except Exception as e:
        logger.error(f"Generate error: {e}")
        return {
            "prompt": prompt,
            "generated_text": "",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting minimal backend on port {port}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
