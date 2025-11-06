"""
AI Services Routes
"""

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import time
import os

ai_router = APIRouter()

# Ollama integration flag
USE_OLLAMA = os.getenv("USE_OLLAMA", "false").lower() == "true"

try:
    from services.ai.sentiment_analysis import get_sentiment_service
    _sentiment = get_sentiment_service()
except Exception as _e:
    _sentiment = None

try:
    from utils.background_tasks import schedule_lightweight_task, log_api_call
except Exception:
    schedule_lightweight_task = None
    log_api_call = None

try:
    from services.ai.ollama_service import get_ollama_service
    _ollama = get_ollama_service()
except Exception as _e:
    _ollama = None

class PredictionRequest(BaseModel):
    data: List[float]
    model: Optional[str] = "default"


class TextAnalysisRequest(BaseModel):
    text: str
    analysis_type: str = "sentiment"


class ChatRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    provider: Optional[str] = None  # "openai", "gemini", "ollama", or "auto"
    temperature: Optional[float] = 0.7


@ai_router.post("/predict")
async def ai_prediction(request: PredictionRequest):
    """AI prediction endpoint"""

    return {
        "prediction": 0.87,
        "confidence": 0.92,
        "model": request.model,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@ai_router.post("/analyze/text")
async def analyze_text(request: TextAnalysisRequest):
    """Text analysis (sentiment, entities, etc.)"""
    if _sentiment and request.analysis_type == "sentiment":
        result = await _sentiment.analyze(request.text)
        return {
            **result,
            "analysis_type": request.analysis_type
        }
    # Fallback
    return {
        "text": request.text,
        "analysis_type": request.analysis_type,
        "sentiment": "positive",
        "score": 0.85,
        "entities": ["product", "service"],
        "keywords": ["excellent", "professional", "quality"]
    }


@ai_router.post("/generate/text")
async def generate_text(prompt: str, background_tasks: BackgroundTasks):
    """AI text generation"""
    start_time = time.time()

    result = {
        "prompt": prompt,
        "generated_text": "This is AI-generated content based on your prompt.",
        "tokens_used": 150,
        "model": "gpt-4"
    }

    # Log API call in background
    if schedule_lightweight_task and log_api_call:
        duration_ms = (time.time() - start_time) * 1000
        schedule_lightweight_task(
            background_tasks,
            log_api_call,
            "/api/v1/ai/generate/text",
            "system",
            duration_ms
        )

    return result


# Real LLM chat via OmniBrainAdapter (OpenAI or Gemini depending on env)
try:
    from adapters.omni_brain_adapter import OmniBrainAdapter  # type: ignore
    _brain = OmniBrainAdapter()
except Exception as _e:
    _brain = None


@ai_router.post("/chat")
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """Chat endpoint with real LLM integration and background logging."""
    start_time = time.time()

    # Route to Ollama if USE_OLLAMA=true or provider="ollama"
    if USE_OLLAMA or request.provider == "ollama":
        if not _ollama:
            return {
                "reply": "",
                "error": "Ollama service unavailable. Ensure Ollama is running and USE_OLLAMA is set.",
                "provider": "ollama",
                "model": request.model,
            }
        
        try:
            result = await _ollama.generate(
                prompt=request.prompt,
                model=request.model,
                temperature=request.temperature or 0.7,
            )
            
            # Log API call in background
            if schedule_lightweight_task and log_api_call:
                duration_ms = (time.time() - start_time) * 1000
                schedule_lightweight_task(
                    background_tasks,
                    log_api_call,
                    "/api/v1/ai/chat",
                    "system",
                    duration_ms
                )
            
            return result
        except Exception as e:
            return {
                "reply": "",
                "error": f"Ollama error: {str(e)}",
                "provider": "ollama",
                "model": request.model,
            }

    # Default: route to OmniBrainAdapter (OpenAI/Gemini)
    if not _brain:
        return {
            "reply": "",
            "error": "Brain adapter unavailable. Ensure dependencies and API keys are set.",
            "provider": request.provider or "auto",
            "model": request.model,
        }

    payload = {
        "prompt": request.prompt,
        "model": request.model,
        "provider": request.provider,
        "temperature": request.temperature,
    }
    result = await _brain.invoke(payload)

    # Log API call in background
    if schedule_lightweight_task and log_api_call:
        duration_ms = (time.time() - start_time) * 1000
        schedule_lightweight_task(
            background_tasks,
            log_api_call,
            "/api/v1/ai/chat",
            "system",
            duration_ms
        )

    return result
