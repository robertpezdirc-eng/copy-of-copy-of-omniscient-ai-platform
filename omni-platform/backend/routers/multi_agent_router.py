from fastapi import APIRouter, UploadFile, File, Form, Request
from adapters.omni_brain_adapter import OmniBrainAdapter
from adapters.audio_adapter import AudioAdapter
from adapters.visual_adapter import VisualAdapter
from adapters.net_agent_adapter import NetAgentAdapter
from adapters.meta_adapter import MetaAdapter
from learning.feedback_store import FeedbackStore
from learning.policy_manager import PolicyManager
import time
import asyncio
from urllib.parse import parse_qs

router = APIRouter(prefix="/api/v1/chat", tags=["multi-agent"])

@router.post("/")
async def multi_agent_chat(request: Request):
    """
    Unified chat endpoint:
    - Če pride text → pošlji v Omni Brain
    - Če pride image → pošlji v Visual agent
    - Če pride audio → pošlji v Audio agent
    - Če pride URL → pošlji v Net agent
    """
    try:
        content_type = request.headers.get("content-type", "").lower()
        text = None
        image: UploadFile | None = None
        audio: UploadFile | None = None
        url = None

        if "multipart/form-data" in content_type:
            form = await request.form()
            text = form.get("text")
            url = form.get("url")
            image = form.get("image")
            audio = form.get("audio")
        else:
            # Try JSON first
            try:
                data = await request.json()
                text = (data.get("text") if isinstance(data, dict) else None)
                url = (data.get("url") if isinstance(data, dict) else None)
            except Exception:
                # Fallback to x-www-form-urlencoded
                body = (await request.body()).decode("utf-8")
                parsed = parse_qs(body)
                text = (parsed.get("text", [None])[0])
                url = (parsed.get("url", [None])[0])

        if image is not None:
            visual = VisualAdapter()
            result = await visual.analyze(image, prompt=text or "Describe this image")
            return {"ok": True, "data": result}

        if audio is not None:
            audio_adapter = AudioAdapter()
            transcript = await audio_adapter.transcribe(audio)
            return {"ok": True, "data": {"text": transcript}}

        if url:
            net = NetAgentAdapter()
            result = await net.fetch(url)
            return {"ok": True, "data": result}

        # Text path with try-providers and metrics
        brain = OmniBrainAdapter()
        meta = MetaAdapter()
        fb = FeedbackStore()
        pm = PolicyManager(fb)
        prompt = (text or "").strip()

        providers_to_try = []
        # Prefer provider/model via policy manager, but tolerate errors
        try:
            prov, mod = pm.choose_provider_model(prompt, task_type="chat")
            if prov:
                providers_to_try.append((prov, mod))
        except Exception:
            pass
        # Fallback chain: openai → gemini → ollama → meta
        for default in [("openai", None), ("gemini", None), ("ollama", None), ("meta", None)]:
            if default not in providers_to_try:
                providers_to_try.append(default)

        # Circuit breaker: skip providers with low success or high latency
        summaries = {row.get("provider"): row for row in fb.summary_by_provider()}
        filtered = []
        for provider, model in providers_to_try:
            s = summaries.get(provider) or {}
            total = s.get("total") or 0
            success = s.get("success") or 0
            avg_latency = float(s.get("avg_latency") or 0.0)
            success_rate = (success / total) if total else 1.0
            if success_rate < 0.2 or avg_latency > 3000:
                continue
            filtered.append((provider, model))
        if filtered:
            providers_to_try = filtered

        last_error = None
        started = time.time()
        for provider, model in providers_to_try:
            try:
                single_start = time.time()
                if provider in ("ollama", "meta"):
                    reply = await asyncio.wait_for(meta.generate(prompt=prompt, model=model, provider=provider), timeout=15)
                else:
                    payload = {"prompt": prompt, "provider": provider}
                    if model:
                        payload["model"] = model
                    reply = await asyncio.wait_for(brain.invoke(payload), timeout=20)
                text_out = reply.get("reply") or reply.get("text") or ""
                if text_out:
                    total_latency_ms = int((time.time() - started) * 1000)
                    provider_latency_ms = int((time.time() - single_start) * 1000)
                    fb.insert_event({
                        "agent_type": "chat",
                        "provider": provider,
                        "model": model,
                        "task_type": "chat",
                        "success": True,
                        "reward": max(0.1, (len(text_out) / 200.0) - (provider_latency_ms / 10000.0)),
                        "latency_ms": total_latency_ms,
                        "meta": {"prompt": prompt, "provider_latency_ms": provider_latency_ms},
                    })
                    return {"ok": True, "provider": provider, "model": model, "latency_ms": total_latency_ms, "provider_latency_ms": provider_latency_ms, "data": reply}
            except Exception as e:
                last_error = str(e)
                continue

        total_latency_ms = int((time.time() - started) * 1000)
        fb.insert_event({
            "agent_type": "chat",
            "provider": providers_to_try[0][0] if providers_to_try else None,
            "model": providers_to_try[0][1] if providers_to_try else None,
            "task_type": "chat",
            "success": False,
            "reward": -0.5,
            "latency_ms": total_latency_ms,
            "meta": {"prompt": prompt, "error": last_error},
        })
        return {"ok": False, "error": last_error or "No provider produced output", "latency_ms": total_latency_ms}
    except Exception as e:
        return {"ok": False, "error": f"router_error: {e}"}


@router.post("/simple")
async def multi_agent_chat_simple(payload: dict):
    try:
        text = (payload.get("text") if isinstance(payload, dict) else None) or ""
        meta = MetaAdapter()
        reply = await meta.generate(prompt=text, provider="meta")
        return {"ok": True, "data": reply}
    except Exception as e:
        return {"ok": False, "error": f"router_error: {e}"}
