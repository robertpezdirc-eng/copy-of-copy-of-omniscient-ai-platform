from fastapi import APIRouter, UploadFile, File
from adapters.visual_adapter import VisualAdapter
from learning.feedback_store import FeedbackStore, MemoryStore
import time

router = APIRouter(prefix="/api/v1/visual", tags=["visual"])

@router.post("/analyze")
async def analyze(file: UploadFile = File(...), session_id: str | None = None):
    adapter = VisualAdapter()
    fb = FeedbackStore()
    mem = MemoryStore()
    started = time.time()
    result = await adapter.analyze(file)
    latency_ms = int((time.time() - started) * 1000)
    success = bool(result) and not result.get("error")
    fb.insert_event({
        "agent_type": "visual",
        "provider": result.get("provider"),
        "model": adapter.gemini_model_default if result.get("provider") == "gemini" else None,
        "task_type": "analyze",
        "success": success,
        "reward": 1.0 if success else -0.2,
        "latency_ms": latency_ms,
        "meta": {"filename": getattr(file, "filename", None)},
    })
    mem.append(session_id or "visual-session", {"result": result, "latency_ms": latency_ms, "success": success}, agent_type="visual")
    return {"ok": True, "data": result, "latency_ms": latency_ms, "success": success}

@router.get("/health")
async def visual_health():
    return {"status": "OK", "agent": "visual"}