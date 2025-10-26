from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
import time

from routers.access_controller import require_api_key
from learning.policy_manager import PolicyManager
from learning.feedback_store import FeedbackStore
from adapters.message_broker import get_broker
from adapters.price_feed import PriceFeed

router = APIRouter(prefix="/finops", tags=["finops"])

class EvaluateRequest(BaseModel):
    window: str = "weekly"
    override_prices: Optional[Dict[str, Dict[str, float]]] = None

class PreferencesRequest(BaseModel):
    provider_priority: Optional[List[str]] = None
    model_prefs: Optional[Dict[str, Dict[str, str]]] = None

class MonitorStartRequest(BaseModel):
    window: str = "realtime"

class MonitorTickRequest(BaseModel):
    monitor_id: str
    override_prices: Optional[Dict[str, Dict[str, float]]] = None

class FinOpsAgent:
    def __init__(self) -> None:
        self.store = FeedbackStore()
        self.policy = PolicyManager(self.store)
        self.feed = PriceFeed()
        self.monitors: Dict[str, Any] = {}

    async def evaluate_market(self, window: str = "weekly", override_prices: Optional[Dict[str, Dict[str, float]]] = None) -> Dict[str, Any]:
        data = self.feed.get_current_prices(window)
        prices = data["providers"]
        if override_prices:
            for prov, models in override_prices.items():
                prices.setdefault(prov, {}).update(models)
        # Primerjava GPT-4 vs Gemini Ultra
        gpt4 = prices.get("openai", {}).get("gpt-4")
        gem_ultra = prices.get("gemini", {}).get("ultra")
        action = None
        provider_priority = None
        if gpt4 is not None and gem_ultra is not None:
            if gpt4 > gem_ultra:
                provider_priority = ["gemini", "openai", "vertex", "ollama"]
                action = "switch_to_gemini"
            else:
                provider_priority = ["openai", "gemini", "vertex", "ollama"]
                action = "stick_with_openai"
        else:
            provider_priority = ["openai", "gemini", "vertex", "ollama"]
            action = "default_openai"
        # Apply preferences
        self.policy.set_preferences(provider_priority=provider_priority)
        # Publish event
        broker = await get_broker()
        await broker.publish("finops.events", {
            "type": "policy_update",
            "provider_priority": provider_priority,
            "prices": prices,
            "action": action,
            "window": window,
        })
        # Log to feedback
        self.store.insert_event({
            "agent_type": "finops",
            "provider": provider_priority[0],
            "model": "policy",
            "task_type": "cost_optimization",
            "success": True,
            "reward": 1.0,
            "latency_ms": 0,
            "meta": {"action": action, "window": window, "prices": prices},
        })
        return {"action": action, "provider_priority": provider_priority, "prices": prices}

agent = FinOpsAgent()

@router.get("/health")
async def health(_: None = Depends(require_api_key)):
    try:
        broker = await get_broker()
        await broker.publish("finops.health", {"ping": True})
        state = agent.store.get_policy_state()
        return JSONResponse({"status": "ok", "provider_priority": state.get("provider_priority")})
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)}, status_code=500)

@router.get("/preferences")
async def get_preferences(_: None = Depends(require_api_key)):
    state = agent.store.get_policy_state()
    return JSONResponse({"provider_priority": state.get("provider_priority"), "model_prefs": state.get("model_prefs")})

@router.post("/preferences")
async def set_preferences(req: PreferencesRequest, _: None = Depends(require_api_key)):
    agent.policy.set_preferences(provider_priority=req.provider_priority, model_prefs=req.model_prefs)
    state = agent.store.get_policy_state()
    return JSONResponse({"status": "updated", "provider_priority": state.get("provider_priority"), "model_prefs": state.get("model_prefs")})

@router.post("/evaluate")
async def evaluate(req: EvaluateRequest, _: None = Depends(require_api_key)):
    result = await agent.evaluate_market(window=req.window, override_prices=req.override_prices)
    return JSONResponse(result)

@router.post("/monitor/start")
async def monitor_start(req: MonitorStartRequest, _: None = Depends(require_api_key)):
    mid = uuid.uuid4().hex
    agent.monitors[mid] = {"id": mid, "window": req.window, "status": "running", "started_at": int(time.time() * 1000)}
    return JSONResponse({"monitor_id": mid, "status": "running"})

@router.get("/monitor/status/{monitor_id}")
async def monitor_status(monitor_id: str, _: None = Depends(require_api_key)):
    mon = agent.monitors.get(monitor_id)
    if not mon:
        raise HTTPException(status_code=404, detail="monitor not found")
    return JSONResponse(mon)

@router.post("/monitor/tick")
async def monitor_tick(req: MonitorTickRequest, _: None = Depends(require_api_key)):
    mon = agent.monitors.get(req.monitor_id)
    if not mon:
        raise HTTPException(status_code=404, detail="monitor not found")
    result = await agent.evaluate_market(window=mon.get("window", "realtime"), override_prices=req.override_prices)
    mon["last_action"] = result.get("action")
    mon["last_provider_priority"] = result.get("provider_priority")
    mon["last_tick"] = int(time.time() * 1000)
    agent.monitors[req.monitor_id] = mon
    return JSONResponse({"monitor": mon, "result": result})