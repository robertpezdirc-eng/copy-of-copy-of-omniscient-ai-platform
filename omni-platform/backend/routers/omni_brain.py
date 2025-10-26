from fastapi import APIRouter, WebSocket, Request
from pydantic import BaseModel
from typing import Optional, Any, Dict
from adapters.omni_brain_adapter import OmniBrainAdapter
import json
from fastapi.responses import StreamingResponse
from learning.feedback_store import FeedbackStore
from learning.policy_manager import PolicyManager
import time

router = APIRouter(prefix="/api/v1/omni-brain", tags=["omni-brain"])

class ChatRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    temperature: Optional[float] = None
    options: Optional[Dict[str, Any]] = None
    provider: Optional[str] = None

@router.post("/chat")
async def chat(req: ChatRequest):
    adapter = OmniBrainAdapter()
    fb = FeedbackStore()
    pm = PolicyManager(fb)
    prov, mod = pm.choose_provider_model(req.prompt, task_type="chat")
    provider = (req.provider or prov)
    model = (req.model or mod)
    started = time.time()
    result = await adapter.invoke({
        "prompt": req.prompt,
        "model": model,
        "temperature": req.temperature,
        "provider": provider,
        "options": req.options or {},
    })
    latency_ms = int((time.time() - started) * 1000)
    success = bool(result.get("reply"))
    fb.insert_event({
        "agent_type": "omni-brain",
        "provider": result.get("provider") or provider,
        "model": result.get("model") or model,
        "task_type": "chat",
        "success": success,
        "reward": max(0.1, (len(result.get("reply", "")) / 200.0) - (latency_ms / 10000.0)) if success else -0.5,
        "latency_ms": latency_ms,
        "meta": {"temperature": req.temperature},
    })
    return {"ok": True, "latency_ms": latency_ms, "data": result}

@router.websocket("/ws")
async def chat_ws(ws: WebSocket):
    await ws.accept()
    try:
        raw = await ws.receive_text()
        data = json.loads(raw)
        adapter = OmniBrainAdapter()
        fb = FeedbackStore()
        pm = PolicyManager(fb)
        prompt = data.get("prompt", "")
        prov, mod = pm.choose_provider_model(prompt, task_type="chat")
        provider = data.get("provider") or prov
        model = data.get("model") or mod
        payload = {
            "prompt": prompt,
            "model": model,
            "temperature": data.get("temperature"),
            "provider": provider,
            "options": data.get("options") or {},
        }
        started = time.time()
        buf = ""
        async for chunk in adapter.stream(payload):
            buf += chunk
            await ws.send_text(json.dumps({"type": "delta", "data": chunk}))
        latency_ms = int((time.time() - started) * 1000)
        fb.insert_event({
            "agent_type": "omni-brain",
            "provider": provider,
            "model": model,
            "task_type": "chat",
            "success": bool(buf),
            "reward": max(0.1, (len(buf) / 200.0) - (latency_ms / 10000.0)) if buf else -0.5,
            "latency_ms": latency_ms,
            "meta": {"stream": True},
        })
        await ws.send_text(json.dumps({"type": "final", "data": buf}))
        await ws.close()
    except Exception as e:
        await ws.send_text(json.dumps({"type": "error", "message": str(e)}))
        await ws.close()

@router.get("/stream")
async def chat_sse(request: Request, prompt: str = "", model: Optional[str] = None, temperature: Optional[float] = None, provider: Optional[str] = None):
    adapter = OmniBrainAdapter()
    fb = FeedbackStore()
    pm = PolicyManager(fb)
    prov, mod = pm.choose_provider_model(prompt or "", task_type="chat")
    provider_use = provider or prov
    model_use = model or mod

    async def event_gen():
        started = time.time()
        payload = {
            "prompt": prompt or "",
            "model": model_use,
            "temperature": temperature,
            "provider": provider_use,
            "options": {},
        }
        buf = ""
        async for chunk in adapter.stream(payload):
            buf += chunk
            yield f"data: {chunk}\n\n"
            try:
                if await request.is_disconnected():
                    break
            except Exception:
                pass
        latency_ms = int((time.time() - started) * 1000)
        fb.insert_event({
            "agent_type": "omni-brain",
            "provider": provider_use,
            "model": model_use,
            "task_type": "chat",
            "success": bool(buf),
            "reward": max(0.1, (len(buf) / 200.0) - (latency_ms / 10000.0)) if buf else -0.5,
            "latency_ms": latency_ms,
            "meta": {"sse": True},
        })

    return StreamingResponse(event_gen(), media_type="text/event-stream")