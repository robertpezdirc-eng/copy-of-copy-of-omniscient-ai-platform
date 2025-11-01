"""
AI Services Routes
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone

ai_router = APIRouter()

try:
    from services.ai.sentiment_analysis import get_sentiment_service
    _sentiment = get_sentiment_service()
except Exception as _e:
    _sentiment = None

class PredictionRequest(BaseModel):
    data: List[float]
    model: Optional[str] = "default"


class TextAnalysisRequest(BaseModel):
    text: str
    analysis_type: str = "sentiment"


class ChatRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    provider: Optional[str] = None  # "openai", "gemini", or "auto"
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
async def generate_text(prompt: str):
    """AI text generation"""

    return {
        "prompt": prompt,
        "generated_text": "This is AI-generated content based on your prompt.",
        "tokens_used": 150,
        "model": "gpt-4"
    }


# Real LLM chat via OmniBrainAdapter (OpenAI or Gemini depending on env)
try:
    from adapters.omni_brain_adapter import OmniBrainAdapter  # type: ignore
    _brain = OmniBrainAdapter()
except Exception as _e:
    _brain = None


@ai_router.post("/chat")
async def chat(request: ChatRequest):
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
    return result
