"""
Vertex AI helper tools for orchestration.
Provides safe wrappers for Gemini text generation to be used by tools_registry.

This module does not modify global app state and reads configuration from environment variables:
- VERTEX_PROJECT_ID / GOOGLE_CLOUD_PROJECT / PROJECT_ID
- VERTEX_LOCATION / GOOGLE_CLOUD_REGION
- VERTEX_MODEL / GEMINI_MODEL

Usage:
    from .vertex_tools import generate_text
    res = generate_text("Hello", model="gemini-2.0-flash")
"""
from typing import Optional, Dict, Any
import os

# Lazy import of Vertex AI SDK
VERTEX_AVAILABLE = False
try:
    from vertexai import init as vertex_init
    try:
        from vertexai.generative_models import GenerativeModel, GenerationConfig
    except Exception:
        from vertexai.preview.generative_models import GenerativeModel, GenerationConfig
    VERTEX_AVAILABLE = True
except Exception as e:
    # SDK not available; functions will raise descriptive errors
    _vertex_import_error = e

_VERTEX_INIT_DONE = False


def _resolve_project() -> str:
    return (
        os.getenv("VERTEX_PROJECT_ID")
        or os.getenv("GOOGLE_CLOUD_PROJECT")
        or os.getenv("GCP_PROJECT")
        or os.getenv("PROJECT_ID")
        or ""
    )


def _resolve_location() -> str:
    return (
        os.getenv("VERTEX_LOCATION")
        or os.getenv("GOOGLE_CLOUD_REGION")
        or os.getenv("GCP_REGION")
        or "us-central1"
    )


def _resolve_default_model() -> str:
    return (
        os.getenv("VERTEX_MODEL")
        or os.getenv("GEMINI_MODEL")
        or "gemini-1.5-flash"
    )


def ensure_initialized():
    """Initialize Vertex AI client once using environment hints.
    Raises a RuntimeError with helpful message if SDK is not available.
    """
    global _VERTEX_INIT_DONE
    if not VERTEX_AVAILABLE:
        raise RuntimeError(f"Vertex AI SDK not available: {_vertex_import_error}")
    if not _VERTEX_INIT_DONE:
        project = _resolve_project() or "your-gcp-project"
        location = _resolve_location()
        vertex_init(project=project, location=location)
        _VERTEX_INIT_DONE = True


def generate_text(prompt: str, model: Optional[str] = None, system_instruction: Optional[str] = None,
                  config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate text using Gemini models via Vertex AI.

    Returns a dict with keys: ok (bool), text (str), model (str), error (optional).
    """
    ensure_initialized()
    mname = model or _resolve_default_model()
    try:
        gen_model = GenerativeModel(mname)
        inputs = [prompt] if not system_instruction else [system_instruction, prompt]
        cfg_obj = None
        try:
            allowed = {"temperature", "max_output_tokens", "top_p", "top_k", "candidate_count"}
            cfg_kwargs = {k: v for k, v in (config or {}).items() if k in allowed}
            if cfg_kwargs:
                cfg_obj = GenerationConfig(**cfg_kwargs)
        except Exception:
            cfg_obj = None
        resp = gen_model.generate_content(inputs, generation_config=cfg_obj)
        text = getattr(resp, "text", None)
        return {"ok": True, "text": text, "model": mname}
    except Exception as e:
        return {"ok": False, "error": str(e), "model": mname}