import os
from typing import Any, Dict, Optional

import httpx


class MetaAdapter:
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        provider: str = "ollama",
    ) -> Dict[str, Any]:
        """
        Generate text using Meta/LLaMA/Ollama providers.

        - provider="ollama": POST http://localhost:11434/api/generate
          Body: { model, prompt, stream:false }
        - provider="meta": POST {META_API_URL}/generate (JSON or text)

        Env vars:
          - OLLAMA_URL (default: http://localhost:11434/api/generate)
          - OLLAMA_MODEL (default: llama3)
          - META_API_URL (default: http://localhost:8085)
          - META_MODEL (default: llama3)
        """
        if provider == "ollama":
            url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
            mdl = model or os.getenv("OLLAMA_MODEL", "llama3")
            payload = {"model": mdl, "prompt": prompt, "stream": False}
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return {
                    "provider": "ollama",
                    "model": mdl,
                    "reply": data.get("response", ""),
                    "raw": data,
                }

        elif provider == "meta":
            base = os.getenv("META_API_URL", "http://localhost:8085")
            url = f"{base.rstrip('/')}/generate"
            mdl = model or os.getenv("META_MODEL", "llama3")
            payload = {"model": mdl, "prompt": prompt}
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                ct = resp.headers.get("content-type", "")
                if "application/json" in ct:
                    data = resp.json()
                    reply = data.get("response", data.get("text", ""))
                else:
                    data = {"response": resp.text}
                    reply = resp.text
                return {
                    "provider": "meta",
                    "model": mdl,
                    "reply": reply,
                    "raw": data,
                }
        else:
            raise ValueError(f"Unknown provider: {provider}")