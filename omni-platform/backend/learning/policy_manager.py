import os
import time
from typing import Dict, Any, Optional, Tuple, List
from .feedback_store import FeedbackStore

DEFAULT_PRIORITY = ["openai", "gemini", "vertex", "ollama"]
DEFAULT_MODELS = {
    "openai": {"simple": "gpt-4o-mini", "complex": "gpt-4o"},
    "gemini": {"simple": "gemini-1.5-flash", "complex": "gemini-1.5-pro"},
    "vertex": {"simple": "gemini-1.5-flash", "complex": "gemini-1.5-pro"},
    "ollama": {"simple": "llama3", "complex": "llama3:70b"},
}

class PolicyManager:
    """
    Odloča o providerju in modelu glede na:
    - heuristiko zahtevnosti naloge
    - povprečne nagrade po providerjih
    - preferenčni modeli po task_type
    """
    def __init__(self, store: Optional[FeedbackStore] = None) -> None:
        self.store = store or FeedbackStore()

    def _task_complexity(self, prompt: str, modalities: Optional[List[str]] = None) -> str:
        if modalities:
            if any(m in ("image", "audio", "video") for m in modalities):
                return "complex"
        if len(prompt) > 600 or "code:" in prompt.lower() or "sql" in prompt.lower():
            return "complex"
        return "simple"

    def choose_provider_model(self, prompt: str, task_type: Optional[str] = None, modalities: Optional[List[str]] = None) -> Tuple[str, str]:
        state = self.store.get_policy_state()
        priostr = state.get("provider_priority") or ",".join(DEFAULT_PRIORITY)
        provider_priority = [p.strip() for p in priostr.split(",") if p.strip()]
        model_prefs = state.get("model_prefs") or {}

        complexity = self._task_complexity(prompt, modalities)
        # najprej preferenčni modeli po task_type
        if task_type and task_type in model_prefs:
            prefs = model_prefs[task_type]
            for p in provider_priority:
                if p in prefs:
                    return p, prefs[p]
        # drugače izberi po povprečni nagradi
        by_provider = self.store.summary_by_provider()
        rewarded = {row["provider"]: row["avg_reward"] for row in by_provider} if by_provider else {}
        # sort providerjev po priority, potem po nagradi
        provider_priority.sort(key=lambda p: (-float(rewarded.get(p) or 0.0), provider_priority.index(p)))
        for p in provider_priority:
            models = DEFAULT_MODELS.get(p, {})
            if complexity in models:
                return p, models[complexity]
        # fallback prva prioriteta + simple
        first = provider_priority[0] if provider_priority else DEFAULT_PRIORITY[0]
        return first, DEFAULT_MODELS.get(first, {}).get("simple", "")

    def update_reward(self, agent_type: str, provider: str, model: str, success: bool, latency_ms: Optional[int] = None, task_type: Optional[str] = None, meta: Optional[Dict[str, Any]] = None) -> None:
        ev = {
            "agent_type": agent_type,
            "provider": provider,
            "model": model,
            "task_type": task_type,
            "success": success,
            "reward": 1.0 if success else 0.0,
            "latency_ms": latency_ms or 0,
            "meta": meta or {},
        }
        self.store.insert_event(ev)

    def set_preferences(self, provider_priority: Optional[List[str]] = None, model_prefs: Optional[Dict[str, Dict[str, str]]] = None) -> None:
        priostr = ",".join(provider_priority) if provider_priority else None
        self.store.set_policy_state(priostr, model_prefs or {})