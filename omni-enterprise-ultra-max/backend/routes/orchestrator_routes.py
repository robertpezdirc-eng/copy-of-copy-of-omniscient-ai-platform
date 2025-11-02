"""
Lightweight Orchestrator API

This router provides a minimal "AI Router/Orchestrator" facade inspired by
OMNIBOT12's orchestrator patterns, adapted to the existing backend.

Endpoints:
- POST /api/orchestrate: Routes a free-form query to the platform's AI chat
  (prefers Ollama when enabled; otherwise uses OmniBrainAdapter) and wraps
  the result with metadata (module, execution_time, tenant_id, timestamp).
- GET  /api/orchestrator/health: Simple health for the orchestrator layer.
- GET  /api/orchestrator/stats: Basic in-memory stats.

No additional heavy dependencies; safe to load in OMNI_MINIMAL mode.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict, Optional
from datetime import datetime, timezone
import os
import time

orchestrator_router = APIRouter()


# Optional integrations aligned with existing ai_routes
USE_OLLAMA = os.getenv("USE_OLLAMA", "false").lower() == "true"

try:
    from services.ai.ollama_service import get_ollama_service  # type: ignore
    _ollama = get_ollama_service()
except Exception:
    _ollama = None

try:
    from adapters.omni_brain_adapter import OmniBrainAdapter  # type: ignore
    _brain = OmniBrainAdapter()
except Exception:
    _brain = None


class OrchestrateRequest(BaseModel):
    query: str
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    context: Dict[str, Any] = {}
    provider: Optional[str] = None  # e.g., "ollama", "openai", "gemini"
    model: Optional[str] = None
    temperature: Optional[float] = 0.7


class OrchestrateResponse(BaseModel):
    module: str
    result: Dict[str, Any]
    execution_time: float
    tenant_id: Optional[str]
    timestamp: str


# Very small in-memory stats
_stats = {
    "requests": 0,
    "last_query_len": 0,
    "last_duration_ms": 0.0,
}


@orchestrator_router.get("/orchestrator/health")
async def orchestrator_health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "use_ollama": USE_OLLAMA,
        "ollama_available": bool(_ollama),
        "brain_available": bool(_brain),
        "version": "1.0.0",
    }


@orchestrator_router.get("/orchestrator/stats")
async def orchestrator_stats():
    return {
        **_stats,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@orchestrator_router.post("/orchestrate", response_model=OrchestrateResponse)
async def orchestrate(request: OrchestrateRequest):
    """
    Route a generic query through the platform's AI capabilities and return
    a normalized response. This is a thin facade over the existing AI chat
    stack with minimal logic to choose between Ollama and the brain adapter.
    """
    _stats["requests"] += 1
    _stats["last_query_len"] = len(request.query or "")

    start = time.time()

    # Prefer explicit provider; else use USE_OLLAMA flag as default
    provider = (request.provider or ("ollama" if USE_OLLAMA else "auto")).lower()

    result: Dict[str, Any]
    if provider == "ollama":
        if not _ollama:
            result = {
                "reply": "",
                "error": "Ollama service unavailable. Ensure Ollama is running and USE_OLLAMA is set.",
                "provider": "ollama",
                "model": request.model,
            }
        else:
            result = await _ollama.generate(
                prompt=request.query,
                model=request.model,
                temperature=request.temperature or 0.7,
            )
        module = "ai.chat"
    else:
        # Default path via OmniBrainAdapter (OpenAI/Gemini per env)
        if not _brain:
            result = {
                "reply": "",
                "error": "Brain adapter unavailable. Ensure dependencies and API keys are set.",
                "provider": provider,
                "model": request.model,
            }
        else:
            payload = {
                "prompt": request.query,
                "model": request.model,
                "provider": provider if provider != "auto" else None,
                "temperature": request.temperature,
            }
            result = await _brain.invoke(payload)
        module = "ai.chat"

    duration = time.time() - start
    _stats["last_duration_ms"] = round(duration * 1000.0, 2)

    return OrchestrateResponse(
        module=module,
        result=result,
        execution_time=round(duration, 4),
        tenant_id=request.tenant_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
