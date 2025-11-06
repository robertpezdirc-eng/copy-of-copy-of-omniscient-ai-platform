"""
Multi-LLM Router Service

Intelligent routing between multiple LLM providers based on:
- Cost optimization
- Speed requirements
- Quality/capability needs
- Availability and fallback
"""

import os
import time
import logging
from typing import Optional, Dict, Any, List, Literal
from dataclasses import dataclass
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class RoutingStrategy(str, Enum):
    """LLM routing strategies"""
    COST_OPTIMIZED = "cost"  # Cheapest option first
    SPEED_OPTIMIZED = "speed"  # Fastest option first
    QUALITY_OPTIMIZED = "quality"  # Best quality first
    BALANCED = "balanced"  # Balance cost/speed/quality
    FAILOVER = "failover"  # Try providers in order until success


@dataclass
class LLMProvider:
    """LLM Provider configuration"""
    name: str
    cost_per_1k_tokens: float  # Input tokens
    avg_latency_ms: int  # Average response time
    quality_score: float  # 0-100 capability score
    max_tokens: int
    supports_streaming: bool
    is_available: bool = True


class MultiLLMRouter:
    """
    Intelligent router for multiple LLM providers
    
    Providers:
    - OpenAI GPT-4: Premium quality, high cost
    - Anthropic Claude: Cost-effective, good quality
    - Google Gemini: Specialist tasks, medium cost
    - Local Ollama: Fast, free, lower quality
    """
    
    def __init__(self):
        self.providers = {
            "openai": LLMProvider(
                name="OpenAI GPT-4",
                cost_per_1k_tokens=0.03,
                avg_latency_ms=2000,
                quality_score=95,
                max_tokens=8192,
                supports_streaming=True
            ),
            "anthropic": LLMProvider(
                name="Anthropic Claude",
                cost_per_1k_tokens=0.015,
                avg_latency_ms=1800,
                quality_score=92,
                max_tokens=100000,
                supports_streaming=True
            ),
            "gemini": LLMProvider(
                name="Google Gemini",
                cost_per_1k_tokens=0.0005,
                avg_latency_ms=1500,
                quality_score=88,
                max_tokens=32768,
                supports_streaming=True
            ),
            "ollama": LLMProvider(
                name="Local Ollama",
                cost_per_1k_tokens=0.0,
                avg_latency_ms=500,
                quality_score=75,
                max_tokens=4096,
                supports_streaming=True
            )
        }
        
        # Initialize clients
        self._init_clients()
        
        # Routing statistics
        self.stats = {
            "total_requests": 0,
            "provider_usage": {p: 0 for p in self.providers},
            "provider_failures": {p: 0 for p in self.providers},
            "avg_latency": {p: [] for p in self.providers}
        }
    
    def _init_clients(self):
        """Initialize LLM provider clients"""
        # OpenAI
        try:
            import openai
            self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.providers["openai"].is_available = True
        except Exception as e:
            logger.warning(f"OpenAI not available: {e}")
            self.providers["openai"].is_available = False
            self.openai_client = None
        
        # Anthropic
        try:
            import anthropic
            self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.providers["anthropic"].is_available = True
        except Exception as e:
            logger.warning(f"Anthropic not available: {e}")
            self.providers["anthropic"].is_available = False
            self.anthropic_client = None
        
        # Google Gemini
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            self.gemini_client = genai.GenerativeModel('gemini-pro')
            self.providers["gemini"].is_available = True
        except Exception as e:
            logger.warning(f"Gemini not available: {e}")
            self.providers["gemini"].is_available = False
            self.gemini_client = None
        
        # Ollama (local)
        try:
            import httpx
            # Test Ollama availability
            response = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
            if response.status_code == 200:
                self.ollama_available = True
                self.providers["ollama"].is_available = True
            else:
                self.ollama_available = False
                self.providers["ollama"].is_available = False
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            self.ollama_available = False
            self.providers["ollama"].is_available = False
    
    def select_provider(
        self,
        strategy: RoutingStrategy = RoutingStrategy.BALANCED,
        required_tokens: int = 2000,
        task_complexity: Literal["simple", "medium", "complex"] = "medium"
    ) -> str:
        """
        Select the best LLM provider based on routing strategy
        
        Args:
            strategy: Routing strategy to use
            required_tokens: Estimated tokens needed
            task_complexity: Task complexity level
            
        Returns:
            Provider name (openai, anthropic, gemini, ollama)
        """
        available_providers = {
            name: provider 
            for name, provider in self.providers.items() 
            if provider.is_available and provider.max_tokens >= required_tokens
        }
        
        if not available_providers:
            raise ValueError("No available LLM providers")
        
        # Route based on strategy
        if strategy == RoutingStrategy.COST_OPTIMIZED:
            return min(available_providers.items(), key=lambda x: x[1].cost_per_1k_tokens)[0]
        
        elif strategy == RoutingStrategy.SPEED_OPTIMIZED:
            return min(available_providers.items(), key=lambda x: x[1].avg_latency_ms)[0]
        
        elif strategy == RoutingStrategy.QUALITY_OPTIMIZED:
            return max(available_providers.items(), key=lambda x: x[1].quality_score)[0]
        
        elif strategy == RoutingStrategy.BALANCED:
            # Score based on normalized cost, speed, and quality
            def balanced_score(provider: LLMProvider) -> float:
                # Lower cost is better (invert)
                cost_score = 1 / (provider.cost_per_1k_tokens + 0.001)
                # Lower latency is better (invert)
                speed_score = 1 / (provider.avg_latency_ms / 1000)
                # Higher quality is better
                quality_score = provider.quality_score / 100
                
                # Adjust weights based on task complexity
                if task_complexity == "simple":
                    return cost_score * 0.5 + speed_score * 0.4 + quality_score * 0.1
                elif task_complexity == "complex":
                    return cost_score * 0.1 + speed_score * 0.2 + quality_score * 0.7
                else:  # medium
                    return cost_score * 0.3 + speed_score * 0.3 + quality_score * 0.4
            
            return max(available_providers.items(), key=lambda x: balanced_score(x[1]))[0]
        
        elif strategy == RoutingStrategy.FAILOVER:
            # Return first available in quality order
            return max(available_providers.items(), key=lambda x: x[1].quality_score)[0]
        
        return "openai"  # Default fallback
    
    async def complete(
        self,
        prompt: str,
        strategy: RoutingStrategy = RoutingStrategy.BALANCED,
        provider: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        task_complexity: Literal["simple", "medium", "complex"] = "medium",
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete a prompt using the selected or auto-routed LLM
        
        Args:
            prompt: User prompt
            strategy: Routing strategy (if provider not specified)
            provider: Force specific provider (openai, anthropic, gemini, ollama)
            max_tokens: Max response tokens
            temperature: Sampling temperature
            task_complexity: Task complexity for routing
            system_prompt: Optional system prompt
            
        Returns:
            Response dict with content, provider, latency, cost
        """
        self.stats["total_requests"] += 1
        
        # Select provider
        if not provider:
            provider = self.select_provider(strategy, max_tokens, task_complexity)
        
        if not self.providers[provider].is_available:
            raise ValueError(f"Provider {provider} is not available")
        
        logger.info(f"Routing request to {provider} (strategy: {strategy})")
        
        start_time = time.time()
        
        try:
            # Route to appropriate provider
            if provider == "openai":
                response = await self._complete_openai(prompt, max_tokens, temperature, system_prompt)
            elif provider == "anthropic":
                response = await self._complete_anthropic(prompt, max_tokens, temperature, system_prompt)
            elif provider == "gemini":
                response = await self._complete_gemini(prompt, max_tokens, temperature, system_prompt)
            elif provider == "ollama":
                response = await self._complete_ollama(prompt, max_tokens, temperature, system_prompt)
            else:
                raise ValueError(f"Unknown provider: {provider}")
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Update stats
            self.stats["provider_usage"][provider] += 1
            self.stats["avg_latency"][provider].append(latency_ms)
            
            # Estimate cost
            estimated_tokens = len(prompt.split()) * 1.3 + len(response.split()) * 1.3
            estimated_cost = (estimated_tokens / 1000) * self.providers[provider].cost_per_1k_tokens
            
            return {
                "content": response,
                "provider": provider,
                "latency_ms": latency_ms,
                "estimated_cost": round(estimated_cost, 6),
                "strategy_used": strategy.value,
                "tokens_estimated": int(estimated_tokens)
            }
            
        except Exception as e:
            self.stats["provider_failures"][provider] += 1
            logger.error(f"Provider {provider} failed: {e}")
            
            # Try failover if using failover strategy
            if strategy == RoutingStrategy.FAILOVER:
                available = [p for p in self.providers if p != provider and self.providers[p].is_available]
                if available:
                    logger.info(f"Failing over to next provider...")
                    return await self.complete(
                        prompt=prompt,
                        strategy=strategy,
                        provider=available[0],
                        max_tokens=max_tokens,
                        temperature=temperature,
                        task_complexity=task_complexity,
                        system_prompt=system_prompt
                    )
            
            raise
    
    async def _complete_openai(
        self, 
        prompt: str, 
        max_tokens: int, 
        temperature: float,
        system_prompt: Optional[str]
    ) -> str:
        """Complete using OpenAI"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content
    
    async def _complete_anthropic(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str]
    ) -> str:
        """Complete using Anthropic Claude"""
        message = self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    
    async def _complete_gemini(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str]
    ) -> str:
        """Complete using Google Gemini"""
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        response = self.gemini_client.generate_content(
            full_prompt,
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": temperature
            }
        )
        return response.text
    
    async def _complete_ollama(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str]
    ) -> str:
        """Complete using local Ollama"""
        import httpx
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "model": "llama2",
                "prompt": f"{system_prompt}\n\n{prompt}" if system_prompt else prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature
                }
            }
            
            response = await client.post(
                "http://localhost:11434/api/generate",
                json=payload
            )
            response.raise_for_status()
            return response.json()["response"]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        return {
            "total_requests": self.stats["total_requests"],
            "provider_usage": self.stats["provider_usage"],
            "provider_failures": self.stats["provider_failures"],
            "avg_latency_ms": {
                provider: int(sum(latencies) / len(latencies)) if latencies else 0
                for provider, latencies in self.stats["avg_latency"].items()
            },
            "provider_availability": {
                name: provider.is_available
                for name, provider in self.providers.items()
            }
        }
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about available providers"""
        return {
            name: {
                "name": provider.name,
                "cost_per_1k_tokens": provider.cost_per_1k_tokens,
                "avg_latency_ms": provider.avg_latency_ms,
                "quality_score": provider.quality_score,
                "max_tokens": provider.max_tokens,
                "supports_streaming": provider.supports_streaming,
                "is_available": provider.is_available
            }
            for name, provider in self.providers.items()
        }


# Singleton instance
_router_instance: Optional[MultiLLMRouter] = None


def get_multi_llm_router() -> MultiLLMRouter:
    """Get or create the Multi-LLM Router instance"""
    global _router_instance
    if _router_instance is None:
        _router_instance = MultiLLMRouter()
    return _router_instance
