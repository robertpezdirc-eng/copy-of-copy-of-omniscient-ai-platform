from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request

from .auth import verify_api_key
from .settings import settings

router = APIRouter()


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
    Minimal OpenAI-compatible endpoint that maps to backend text generation.
    - Supports non-streaming requests only (stream=false/default).
    - Extracts prompt from messages and calls backend /api/v1/ai/chat.
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
    prompt = _extract_prompt(messages)

    if not prompt:
        raise HTTPException(status_code=400, detail="Unable to extract prompt from messages")

    # Call backend chat endpoint (JSON body), fallback to legacy generate/text if /chat is missing
    async with _client() as client:
        try:
            payload = {"prompt": prompt, "model": model}
            upstream = await client.post("/api/v1/ai/chat", json=payload)
            # Fallback for older backends that don't have /chat yet
            if upstream.status_code == 404:
                # Legacy endpoint expects a simple "prompt" param; use POST with query params and an empty JSON body to satisfy Content-Length
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
                    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as oc:
                        oresp = await oc.post(
                            "https://api.openai.com/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Content-Type": "application/json",
                            },
                            json={
                                "model": model,
                                "messages": body.get("messages", []),
                                "temperature": body.get("temperature", 0.7),
                                "stream": False,
                            },
                        )
                    if oresp.status_code < 400:
                        # Pass-through OpenAI JSON (already OpenAI-compatible)
                        return oresp.json()
                except Exception:
                    # If fallback fails, continue to raise the backend error below
                    pass

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
    return {
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
