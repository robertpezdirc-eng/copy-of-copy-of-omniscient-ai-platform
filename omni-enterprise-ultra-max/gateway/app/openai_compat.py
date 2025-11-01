from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request

from .auth import verify_api_key
from .settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_upstream_client() -> httpx.AsyncClient:
    """Get pooled upstream client or create a new one."""
    from .main import get_upstream_client
    client = get_upstream_client()
    if client:
        return client
    # Fallback if not initialized
    timeout = httpx.Timeout(
        connect=settings.connect_timeout,
        read=settings.request_timeout,
        write=settings.request_timeout,
        pool=5.0,
    )
    return httpx.AsyncClient(base_url=settings.upstream_url, timeout=timeout, trust_env=True)


def _get_openai_client() -> httpx.AsyncClient:
    """Get pooled OpenAI client or create a new one."""
    from .main import get_openai_client
    client = get_openai_client()
    if client:
        return client
    # Fallback if not initialized
    return httpx.AsyncClient(timeout=httpx.Timeout(30.0), trust_env=True)


def _client() -> httpx.AsyncClient:
    timeout = httpx.Timeout(
        connect=settings.connect_timeout,
        read=settings.request_timeout,
        write=settings.request_timeout,
        pool=5.0,
    )
    return httpx.AsyncClient(base_url=settings.upstream_url, timeout=timeout, trust_env=True)


def _extract_prompt(messages: List[Dict[str, Any]]) -> str:
    """Extract prompt from the last user message; fallback to concatenated text contents."""

    def _text_from_content(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            texts = [part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text"]
            return "\n".join(t for t in texts if t)
        return ""

    if not messages:
        return ""

    # Prefer last user message
    last_user = next((m for m in reversed(messages) if m.get("role") == "user"), None)
    if last_user is not None:
        txt = _text_from_content(last_user.get("content"))
        if txt:
            return txt

    # Fallback: concatenate any string contents
    return "\n".join(
        _text_from_content(m.get("content"))
        for m in messages
        if _text_from_content(m.get("content"))
    )


@router.post("/v1/chat/completions", dependencies=[Depends(verify_api_key)])
async def chat_completions(req: Request) -> Dict[str, Any]:
    """
    OpenAI-compatible endpoint with response caching and connection pooling.
    - Supports non-streaming requests only (stream=false/default).
    - Extracts prompt from messages and calls backend /api/v1/ai/chat.
    - Uses Redis cache for duplicate requests within TTL window.
    """
    body: Dict[str, Any] = await req.json()

    # Validate basic fields
    messages = body.get("messages")
    if not isinstance(messages, list):
        raise HTTPException(status_code=400, detail="messages must be a list of chat messages")
    stream = bool(body.get("stream", False))
    if stream:
        raise HTTPException(status_code=400, detail="stream=true not supported in local compatibility shim")

    model = body.get("model") or "gpt-4o-mini"
    temperature = float(body.get("temperature", 0.7))
    prompt = _extract_prompt(messages)

    if not prompt:
        raise HTTPException(status_code=400, detail="Unable to extract prompt from messages")

    # Check cache first
    from .main import get_response_cache
    cache = get_response_cache()
    if cache:
        cached_response = await cache.get(prompt, model, temperature)
        if cached_response:
            logger.info(f"Cache hit for model={model}")
            return cached_response

    # Call backend chat endpoint (JSON body), fallback to legacy generate/text if /chat is missing
    use_pooled = True
    client = _get_upstream_client()

    # If pooled client not available, fall back to creating a new one
    if not hasattr(client, 'is_closed') or client.is_closed:
        use_pooled = False
        client = _client()

    try:
        payload = {"prompt": prompt, "model": model, "temperature": temperature}

        if use_pooled:
            # Use pooled client (don't close it)
            upstream = await client.post("/api/v1/ai/chat", json=payload)
            # Fallback for older backends that don't have /chat yet
            if upstream.status_code == 404:
                upstream = await client.post("/api/v1/ai/generate/text", params={"prompt": prompt}, json={})
        else:
            # Use temporary client (close after use)
            async with client:
                upstream = await client.post("/api/v1/ai/chat", json=payload)
                if upstream.status_code == 404:
                    upstream = await client.post("/api/v1/ai/generate/text", params={"prompt": prompt}, json={})
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Upstream backend unavailable")

    # If backend still fails, attempt a direct OpenAI fallback when gateway has OPENAI_API_KEY
    if upstream.status_code >= 400:
        # Try direct OpenAI call only for obvious missing/unsupported routes
        if upstream.status_code in (404, 501):
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                try:
                    openai_http = _get_openai_client()
                    use_pooled_openai = hasattr(openai_http, 'is_closed') and not openai_http.is_closed

                    if use_pooled_openai:
                        oresp = await openai_http.post(
                            "https://api.openai.com/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Content-Type": "application/json",
                            },
                            json={
                                "model": model,
                                "messages": body.get("messages", []),
                                "temperature": temperature,
                                "stream": False,
                            },
                        )
                    else:
                        async with openai_http:
                            oresp = await openai_http.post(
                                "https://api.openai.com/v1/chat/completions",
                                headers={
                                    "Authorization": f"Bearer {api_key}",
                                    "Content-Type": "application/json",
                                },
                                json={
                                    "model": model,
                                    "messages": body.get("messages", []),
                                    "temperature": temperature,
                                    "stream": False,
                                },
                            )

                    if oresp.status_code < 400:
                        # Pass-through OpenAI JSON (already OpenAI-compatible)
                        response_data = oresp.json()
                        # Cache the response
                        if cache:
                            await cache.set(prompt, model, response_data, temperature)
                        logger.info(f"Direct OpenAI call successful for model={model}")
                        return response_data
                except Exception as e:
                    logger.warning(f"OpenAI fallback failed: {e}")
                    # If fallback fails, continue to raise the backend error below

        # No viable fallback; surface backend error
        raise HTTPException(status_code=upstream.status_code, detail=upstream.text)

    data = upstream.json()
    text = data.get("reply") or data.get("generated_text") or ""
    tokens_used = int(data.get("tokens_used") or 0)

    # Rough prompt token estimate if not provided by backend
    if tokens_used <= 0:
        prompt_tokens = max(1, len(prompt) // 4)
        completion_tokens = max(1, len(text) // 4)
        total_tokens = prompt_tokens + completion_tokens
    else:
        # If backend only returns total tokens (tokens_used), split roughly 50/50
        total_tokens = tokens_used
        prompt_tokens = max(1, total_tokens // 2)
        completion_tokens = max(1, total_tokens - prompt_tokens)

    # Build OpenAI-style response
    now = int(time.time())
    response_data = {
        "id": f"chatcmpl-local-{now}",
        "object": "chat.completion",
        "created": now,
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        },
    }

    # Cache the response
    if cache:
        await cache.set(prompt, model, response_data, temperature)
        logger.info(f"Backend response cached for model={model}")

    return response_data
