from fastapi import APIRouter, UploadFile, File
from adapters.audio_adapter import AudioAdapter
from learning.feedback_store import FeedbackStore, MemoryStore
import time

router = APIRouter(prefix="/api/v1/audio", tags=["audio"])

@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...), session_id: str | None = None):
    adapter = AudioAdapter()
    fb = FeedbackStore()
    mem = MemoryStore()
    started = time.time()
    text = await adapter.transcribe(file)
    latency_ms = int((time.time() - started) * 1000)
    success = bool(text) and not str(text).startswith("[error]")
    fb.insert_event({
        "agent_type": "audio",
        "provider": "openai" if adapter.openai else None,
        "model": "whisper-1" if adapter.openai else None,
        "task_type": "transcribe",
        "success": success,
        "reward": 1.0 if success else -0.2,
        "latency_ms": latency_ms,
        "meta": {"filename": getattr(file, "filename", None)},
    })
    mem.append(session_id or "audio-session", {"text": str(text), "latency_ms": latency_ms, "success": success}, agent_type="audio")
    return {"ok": True, "data": {"text": text, "latency_ms": latency_ms, "success": success}}

@router.get("/health")
async def audio_health():
    return {"status": "OK", "agent": "audio"}