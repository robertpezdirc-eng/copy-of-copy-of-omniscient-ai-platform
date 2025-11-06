"""
Ollama AI Service
Provides local LLM inference as an alternative to cloud AI providers.
"""
import os
import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)


class OllamaService:
    """Service for interacting with Ollama local LLM server."""

    def __init__(self):
        self.enabled = os.getenv("USE_OLLAMA", "false").lower() == "true"
        self.url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.default_model = os.getenv("OLLAMA_MODEL", "llama3")
        self.timeout = float(os.getenv("OLLAMA_TIMEOUT", "60"))

        if self.enabled:
            logger.info(f"✅ Ollama service enabled: {self.url} (model: {self.default_model})")
        else:
            logger.info("ℹ️  Ollama service disabled (set USE_OLLAMA=true to enable)")

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate text using Ollama.

        Args:
            prompt: Input prompt for generation
            model: Model name (defaults to OLLAMA_MODEL env var)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate

        Returns:
            Dict with 'reply', 'model', 'provider', and 'raw' fields
        """
        if not self.enabled:
            raise RuntimeError("Ollama service is not enabled. Set USE_OLLAMA=true")

        model_name = model or self.default_model
        endpoint = f"{self.url.rstrip('/')}/api/generate"

        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.debug(f"Ollama request: {endpoint} with model={model_name}")
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                data = response.json()

                return {
                    "reply": data.get("response", ""),
                    "model": model_name,
                    "provider": "ollama",
                    "raw": data,
                }
        except httpx.HTTPError as e:
            logger.error(f"Ollama HTTP error: {e}")
            raise RuntimeError(f"Ollama service error: {e}") from e
        except Exception as e:
            logger.error(f"Ollama service error: {e}")
            raise RuntimeError(f"Failed to generate with Ollama: {e}") from e

    async def health_check(self) -> Dict[str, Any]:
        """Check if Ollama service is healthy and responsive."""
        if not self.enabled:
            return {"status": "disabled", "enabled": False}

        try:
            endpoint = f"{self.url.rstrip('/')}/api/tags"
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(endpoint)
                response.raise_for_status()
                data = response.json()
                models = [m.get("name") for m in data.get("models", [])]
                return {
                    "status": "healthy",
                    "enabled": True,
                    "url": self.url,
                    "models": models,
                }
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return {
                "status": "unhealthy",
                "enabled": True,
                "url": self.url,
                "error": str(e),
            }


# Singleton instance
_ollama_service: Optional[OllamaService] = None


def get_ollama_service() -> OllamaService:
    """Get or create Ollama service singleton."""
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
    return _ollama_service
