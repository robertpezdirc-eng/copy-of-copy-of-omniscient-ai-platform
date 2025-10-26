from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from learning.feedback_store import FeedbackStore, MemoryStore
from learning.policy_manager import PolicyManager
from learning.self_optimizer import SelfOptimizer
from learning.knowledge_base import KnowledgeBase

router = APIRouter(prefix="/api/v1/learning", tags=["learning"])

store = FeedbackStore()
mem = MemoryStore()
policy = PolicyManager(store=store)
optimizer = SelfOptimizer()
kb = KnowledgeBase()

class FeedbackEvent(BaseModel):
    agent_type: str
    provider: Optional[str] = None
    model: Optional[str] = None
    task_type: Optional[str] = None
    success: bool
    reward: Optional[float] = None
    latency_ms: Optional[int] = None
    meta: Optional[Dict[str, Any]] = None

@router.post("/feedback")
async def submit_feedback(ev: FeedbackEvent):
    ev_dict = ev.model_dump()
    store.insert_event(ev_dict)
    # posodobimo tudi policy reward
    if ev.provider and ev.model:
        policy.update_reward(
            agent_type=ev.agent_type,
            provider=ev.provider,
            model=ev.model,
            success=ev.success,
            latency_ms=ev.latency_ms,
            task_type=ev.task_type,
            meta=ev.meta,
        )
    return {"ok": True}

@router.get("/summary/providers")
async def summary_providers():
    return {"ok": True, "summary": store.summary_by_provider()}

@router.get("/summary/agents")
async def summary_agents():
    return {"ok": True, "summary": store.summary_by_agent()}

class PolicySetRequest(BaseModel):
    provider_priority: Optional[List[str]] = None
    model_prefs: Optional[Dict[str, Dict[str, str]]] = None

@router.post("/policy")
async def set_policy(req: PolicySetRequest):
    policy.set_preferences(provider_priority=req.provider_priority, model_prefs=req.model_prefs or {})
    return {"ok": True}

class ChooseRequest(BaseModel):
    prompt: str
    task_type: Optional[str] = None
    modalities: Optional[List[str]] = None

@router.post("/choose")
async def choose_provider_model(req: ChooseRequest):
    provider, model = policy.choose_provider_model(req.prompt, task_type=req.task_type, modalities=req.modalities)
    return {"ok": True, "provider": provider, "model": model}

class MemoryAppendRequest(BaseModel):
    session_id: str
    event: Dict[str, Any]
    agent_type: Optional[str] = None

@router.post("/memory")
async def memory_append(req: MemoryAppendRequest):
    mem.append(req.session_id, req.event, agent_type=req.agent_type)
    return {"ok": True}

@router.get("/memory/{session_id}")
async def memory_history(session_id: str, limit: int = 50):
    return {"ok": True, "history": mem.history(session_id, limit=limit)}

@router.get("/recommend")
async def recommend(task_type: Optional[str] = None):
    # oceni uspešnost in latenco iz feedbacka (preprosto povprečje)
    sprov = store.summary_by_provider()
    # globalni približek
    total = sum((row.get("total") or 0) for row in sprov)
    success = sum((row.get("success") or 0) for row in sprov)
    avg_latency = sum((row.get("avg_latency") or 0.0) * (row.get("total") or 0) for row in sprov)
    avg_latency = (avg_latency / total) if total else 0.0
    success_rate = (success / total) if total else 0.0
    params = optimizer.recommend(task_type=task_type, success_rate=success_rate, avg_latency_ms=avg_latency)
    return {"ok": True, "params": params, "success_rate": success_rate, "avg_latency_ms": avg_latency}

# Knowledge base wiki endpoints
class WikiPage(BaseModel):
    title: str
    content: str
    tags: Optional[List[str]] = None

@router.post("/wiki/page")
async def wiki_put(page: WikiPage):
    saved = kb.put_page(title=page.title, content=page.content, tags=page.tags)
    return {"ok": True, "page": saved}

@router.get("/wiki/page/{title}")
async def wiki_get(title: str):
    page = kb.get_page(title)
    return {"ok": bool(page), "page": page}

@router.get("/wiki/list")
async def wiki_list():
    return {"ok": True, "pages": kb.list_pages()}

@router.get("/wiki/search")
async def wiki_search(q: str):
    return {"ok": True, "results": kb.search(q)}

# Learning activation endpoint
class LearningActivation(BaseModel):
    enabled: bool
    notes: Optional[str] = None

_LEARNING_ACTIVE = False

@router.post("/activate")
async def activate_learning(cfg: LearningActivation):
    global _LEARNING_ACTIVE
    _LEARNING_ACTIVE = bool(cfg.enabled)
    return {"ok": True, "learning_active": _LEARNING_ACTIVE, "notes": cfg.notes}