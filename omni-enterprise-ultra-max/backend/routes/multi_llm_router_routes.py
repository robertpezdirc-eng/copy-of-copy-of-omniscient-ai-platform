"""
Multi-LLM Router API Routes

Intelligent routing between OpenAI, Anthropic, Gemini, and Ollama
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/llm", tags=["Multi-LLM Router"])


# Pydantic Models
class LLMCompletionRequest(BaseModel):
    prompt: str = Field(..., description="User prompt")
    strategy: Optional[Literal["cost", "speed", "quality", "balanced", "failover"]] = Field(
        "balanced",
        description="Routing strategy"
    )
    provider: Optional[Literal["openai", "anthropic", "gemini", "ollama"]] = Field(
        None,
        description="Force specific provider (overrides strategy)"
    )
    max_tokens: int = Field(2000, ge=1, le=100000, description="Max response tokens")
    temperature: float = Field(0.7, ge=0, le=2, description="Sampling temperature")
    task_complexity: Literal["simple", "medium", "complex"] = Field(
        "medium",
        description="Task complexity for routing"
    )
    system_prompt: Optional[str] = Field(None, description="System prompt")


class LLMCompletionResponse(BaseModel):
    content: str
    provider: str
    latency_ms: int
    estimated_cost: float
    strategy_used: str
    tokens_estimated: int


class ProviderInfoResponse(BaseModel):
    name: str
    cost_per_1k_tokens: float
    avg_latency_ms: int
    quality_score: float
    max_tokens: int
    supports_streaming: bool
    is_available: bool


class RouterStatsResponse(BaseModel):
    total_requests: int
    provider_usage: Dict[str, int]
    provider_failures: Dict[str, int]
    avg_latency_ms: Dict[str, int]
    provider_availability: Dict[str, bool]


# Routes
@router.post("/complete", response_model=LLMCompletionResponse)
async def complete(request: LLMCompletionRequest):
    """
    Complete a prompt using intelligent LLM routing
    
    The router automatically selects the best LLM provider based on:
    - **cost**: Cheapest option (Ollama -> Gemini -> Anthropic -> OpenAI)
    - **speed**: Fastest option (Ollama -> Gemini -> Anthropic -> OpenAI)
    - **quality**: Best quality (OpenAI -> Anthropic -> Gemini -> Ollama)
    - **balanced**: Balance cost/speed/quality based on task complexity
    - **failover**: Try providers in quality order until success
    
    **Providers:**
    - OpenAI GPT-4: Premium quality, high cost ($0.03/1K tokens)
    - Anthropic Claude: Cost-effective, good quality ($0.015/1K tokens)
    - Google Gemini: Specialist tasks, medium cost ($0.0005/1K tokens)
    - Local Ollama: Fast, free, lower quality ($0/1K tokens)
    """
    try:
        from services.ai.multi_llm_router import get_multi_llm_router, RoutingStrategy
        
        router_service = get_multi_llm_router()
        
        # Map string strategy to enum
        strategy_map = {
            "cost": RoutingStrategy.COST_OPTIMIZED,
            "speed": RoutingStrategy.SPEED_OPTIMIZED,
            "quality": RoutingStrategy.QUALITY_OPTIMIZED,
            "balanced": RoutingStrategy.BALANCED,
            "failover": RoutingStrategy.FAILOVER
        }
        
        strategy_enum = strategy_map.get(request.strategy, RoutingStrategy.BALANCED)
        
        result = await router_service.complete(
            prompt=request.prompt,
            strategy=strategy_enum,
            provider=request.provider,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            task_complexity=request.task_complexity,
            system_prompt=request.system_prompt
        )
        
        return LLMCompletionResponse(**result)
        
    except Exception as e:
        logger.error(f"LLM completion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers", response_model=Dict[str, ProviderInfoResponse])
async def get_providers():
    """
    Get information about all LLM providers
    
    Returns availability, costs, performance, and capabilities for each provider.
    """
    try:
        from services.ai.multi_llm_router import get_multi_llm_router
        
        router_service = get_multi_llm_router()
        provider_info = router_service.get_provider_info()
        
        return {
            name: ProviderInfoResponse(**info)
            for name, info in provider_info.items()
        }
        
    except Exception as e:
        logger.error(f"Failed to get providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=RouterStatsResponse)
async def get_stats():
    """
    Get routing statistics
    
    Returns usage metrics, performance data, and provider health status.
    """
    try:
        from services.ai.multi_llm_router import get_multi_llm_router
        
        router_service = get_multi_llm_router()
        stats = router_service.get_stats()
        
        return RouterStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare_providers(
    prompt: str = Field(..., description="Prompt to test"),
    providers: list[str] = Field(
        ["openai", "anthropic", "gemini", "ollama"],
        description="Providers to compare"
    ),
    max_tokens: int = Field(500, description="Max tokens per response")
):
    """
    Compare responses from multiple LLM providers
    
    Useful for:
    - Benchmarking provider quality
    - Cost comparison
    - Performance testing
    - Finding the best provider for specific tasks
    """
    try:
        from services.ai.multi_llm_router import get_multi_llm_router
        
        router_service = get_multi_llm_router()
        
        results = {}
        for provider in providers:
            if provider not in ["openai", "anthropic", "gemini", "ollama"]:
                continue
            
            try:
                result = await router_service.complete(
                    prompt=prompt,
                    provider=provider,
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                results[provider] = result
            except Exception as e:
                results[provider] = {
                    "error": str(e),
                    "available": False
                }
        
        return {
            "prompt": prompt,
            "comparison": results,
            "recommendation": max(
                [p for p in results.keys() if "error" not in results[p]],
                key=lambda p: results[p].get("estimated_cost", float('inf')),
                default=None
            ) if results else None
        }
        
    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
