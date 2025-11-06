"""
Ollama Health Check Routes
Provides health and status endpoints for Ollama service.
"""

from fastapi import APIRouter

ollama_health_router = APIRouter()

try:
    from services.ai.ollama_service import get_ollama_service
    _ollama = get_ollama_service()
except Exception:
    _ollama = None


@ollama_health_router.get("/health")
async def ollama_health():
    """Check Ollama service health and availability."""
    if not _ollama:
        return {
            "status": "unavailable",
            "enabled": False,
            "error": "Ollama service not initialized",
        }

    return await _ollama.health_check()


@ollama_health_router.get("/status")
async def ollama_status():
    """Get Ollama service configuration status."""
    if not _ollama:
        return {
            "enabled": False,
            "error": "Ollama service not initialized",
        }

    return {
        "enabled": _ollama.enabled,
        "url": _ollama.url if _ollama.enabled else None,
        "default_model": _ollama.default_model if _ollama.enabled else None,
        "timeout": _ollama.timeout if _ollama.enabled else None,
    }
