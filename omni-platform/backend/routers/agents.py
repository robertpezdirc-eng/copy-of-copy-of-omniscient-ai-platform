import threading
import time
import uuid
from typing import Any, Dict, List, Optional
import asyncio

from fastapi import APIRouter, HTTPException

from learning.feedback_store import FeedbackStore, MemoryStore
from learning.policy_manager import PolicyManager
from learning.self_optimizer import SelfOptimizer
from adapters.omni_brain_adapter import OmniBrainAdapter
from adapters.meta_adapter import MetaAdapter

router = APIRouter(prefix="/agents", tags=["agents"])

# In-memory task queue and state
_TASK_QUEUE: List[Dict[str, Any]] = []
_TASKS: Dict[str, Dict[str, Any]] = {}
_WORKER_THREAD: Optional[threading.Thread] = None
_WORKER_RUNNING: bool = False
_METRICS: Dict[str, Any] = {
    "avg_queue_wait_ms": 0.0,
    "avg_task_run_ms": 0.0,
    "samples": 0,
    "worker_count": 0,
    "saturation": 0.0,  # queue length / workers
    "history": [],      # last 50 observations
}
_HYSTERESIS_CFG: Dict[str, Any] = {"epsilon": 1, "scale_out_n": 3, "scale_in_n": 4}
_HYSTERESIS_STATE: Dict[str, Any] = {"out_counter": 0, "in_counter": 0}

_fb = FeedbackStore()
_mem = MemoryStore()
_policy = PolicyManager(_fb)
_selfopt = SelfOptimizer()
_brain = OmniBrainAdapter()
_meta = MetaAdapter()


def _process_task(task: Dict[str, Any]) -> Dict[str, Any]:
    task_id = task["id"]
    desc = task["description"]
    task_type = task.get("task_type", "build")
    agent_type = task.get("agent_type", "builder")

    # Choose provider/model and parameters adaptively
    prov, mod = _policy.choose_provider_model(desc, task_type=task_type)
    provider = task.get("provider") or prov
    model = task.get("model") or mod

    sprov = _fb.summary_by_provider()
    total = sum((row.get("total") or 0) for row in sprov)
    success = sum((row.get("success") or 0) for row in sprov)
    avg_latency = sum((row.get("avg_latency") or 0.0) * (row.get("total") or 0) for row in sprov)
    avg_latency = (avg_latency / total) if total else 0.0
    success_rate = (success / total) if total else 0.0
    params = _selfopt.recommend(task_type=task_type, success_rate=success_rate, avg_latency_ms=avg_latency)

    prompt = (
        "You are a proactive Builder AI agent working inside a monorepo. "
        "Goal: propose precise code changes (files, exact patches) to implement: "
        f"{desc}.\n"
        "Constraints:\n"
        "- Keep changes minimal and consistent with repo style.\n"
        "- Prefer FastAPI endpoints and adapters already present.\n"
        "- If dependencies or services are missing, suggest the smallest viable alternative.\n"
        "Output: A concise plan and 1-3 concrete patch blocks using unified diff or explicit file edits."
    )

    started = time.time()
    _mem.append(task.get("session_id", task_id), {
        "type": "task_start", "id": task_id, "desc": desc, "provider": provider, "model": model, "params": params,
    }, agent_type=agent_type)

    reply: Dict[str, Any]
    try:
        # Prefer local Meta/Ollama if available, otherwise OmniBrain (OpenAI/Gemini)
        if provider in ("ollama", "meta"):
            reply = asyncio.run(_meta.generate(prompt=prompt, model=model, provider=provider))
        else:
            reply = asyncio.run(_brain.invoke({"prompt": prompt, "provider": provider, "model": model, **params}))
        text = reply.get("reply") or reply.get("error") or ""
        success = bool(text)
        reward = len(text) / 100.0 if success else -1.0
        latency_ms = int((time.time() - started) * 1000)
    except Exception as e:
        text = f"error: {e}"
        success = False
        reward = -1.0
        latency_ms = int((time.time() - started) * 1000)

    _fb.insert_event({
        "agent_type": agent_type,
        "provider": provider,
        "model": model,
        "task_type": task_type,
        "success": success,
        "reward": reward,
        "latency_ms": latency_ms,
        "meta": {"desc": desc, "params": params},
    })
    _mem.append(task.get("session_id", task_id), {
        "type": "task_result", "id": task_id, "success": success, "latency_ms": latency_ms, "snippet": text[:1000],
    }, agent_type=agent_type)

    return {
        "id": task_id,
        "success": success,
        "latency_ms": latency_ms,
        "provider": provider,
        "model": model,
        "reply": text,
    }


_WORKER_POOL: List[threading.Thread] = []
_WORKER_FLAGS: Dict[int, bool] = {}
_MIN_WORKERS: int = 1
_MAX_WORKERS: int = 4
_TARGET_Q_PER_WORKER: int = 2
def _update_metrics(queue_wait_ms: float, run_ms: float):
    _METRICS["samples"] += 1
    # online moving average
    n = _METRICS["samples"]
    _METRICS["avg_queue_wait_ms"] += (queue_wait_ms - _METRICS["avg_queue_wait_ms"]) / n
    _METRICS["avg_task_run_ms"] += (run_ms - _METRICS["avg_task_run_ms"]) / n
    _METRICS["worker_count"] = sum(1 for t in _WORKER_POOL if t.is_alive())
    _METRICS["saturation"] = (len(_TASK_QUEUE) / max(1, _METRICS["worker_count"]))
    _METRICS["history"].append({"ts": int(time.time()*1000), "queue_wait_ms": queue_wait_ms, "run_ms": run_ms, "workers": _METRICS["worker_count"], "queue": len(_TASK_QUEUE)})
    if len(_METRICS["history"]) > 50:
        _METRICS["history"] = _METRICS["history"][-50:]

def _worker_loop(worker_id: int):
    while _WORKER_RUNNING and _WORKER_FLAGS.get(worker_id, False):
        if not _TASK_QUEUE:
            time.sleep(0.25)
            continue
        task = _TASK_QUEUE.pop(0)
        start_ts = int(time.time()*1000)
        tid = task["id"]
        _TASKS[tid]["status"] = "running"
        queue_wait = start_ts - int(_TASKS[tid]["task"].get("enqueued_ts", start_ts))
        result = _process_task(task)
        end_ts = int(time.time()*1000)
        run_ms = end_ts - start_ts
        _TASKS[tid]["status"] = "done"
        _TASKS[tid]["result"] = result
        _update_metrics(queue_wait_ms=queue_wait, run_ms=run_ms)


def _spawn_worker():
    worker_id = len(_WORKER_POOL)
    _WORKER_FLAGS[worker_id] = True
    t = threading.Thread(target=_worker_loop, args=(worker_id,), daemon=True)
    _WORKER_POOL.append(t)
    t.start()


def _clean_dead_workers():
    alive_pool = []
    for idx, t in enumerate(_WORKER_POOL):
        if t.is_alive():
            alive_pool.append(t)
        else:
            _WORKER_FLAGS[idx] = False
    _WORKER_POOL[:] = alive_pool


def _autoscale():
    desired_raw = max(_MIN_WORKERS, min(_MAX_WORKERS, (len(_TASK_QUEUE) + _TARGET_Q_PER_WORKER - 1) // _TARGET_Q_PER_WORKER))
    current = sum(1 for t in _WORKER_POOL if t.is_alive())
    # hysteresis logic
    epsilon = int(_HYSTERESIS_CFG.get("epsilon", 1))
    scale_out_n = int(_HYSTERESIS_CFG.get("scale_out_n", 3))
    scale_in_n = int(_HYSTERESIS_CFG.get("scale_in_n", 4))
    desired = desired_raw
    if desired_raw > current + epsilon:
        _HYSTERESIS_STATE["out_counter"] += 1
        _HYSTERESIS_STATE["in_counter"] = 0
        if _HYSTERESIS_STATE["out_counter"] >= scale_out_n:
            while _WORKER_RUNNING and current < desired:
                _spawn_worker()
                current += 1
            _HYSTERESIS_STATE["out_counter"] = 0
    elif desired_raw < max(_MIN_WORKERS, current - epsilon):
        _HYSTERESIS_STATE["in_counter"] += 1
        _HYSTERESIS_STATE["out_counter"] = 0
        if _HYSTERESIS_STATE["in_counter"] >= scale_in_n:
            stop_count = current - desired
            for idx in range(len(_WORKER_POOL) - 1, -1, -1):
                if stop_count <= 0:
                    break
                if _WORKER_FLAGS.get(idx, False):
                    _WORKER_FLAGS[idx] = False
                    stop_count -= 1
            _HYSTERESIS_STATE["in_counter"] = 0
    _clean_dead_workers()


def _ensure_worker():
    global _WORKER_THREAD, _WORKER_RUNNING
    # Initialize pool with min workers
    if not _WORKER_RUNNING:
        _WORKER_RUNNING = True
        for _ in range(_MIN_WORKERS):
            _spawn_worker()
    else:
        _autoscale()


@router.post("/builder/start")
def start_builder() -> Dict[str, Any]:
    _ensure_worker()
    return {"ok": True, "running": _WORKER_RUNNING}


@router.post("/builder/stop")
def stop_builder() -> Dict[str, Any]:
    global _WORKER_RUNNING
    _WORKER_RUNNING = False
    return {"ok": True, "running": _WORKER_RUNNING}


@router.post("/builder/task")
def submit_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    desc = payload.get("description")
    if not desc:
        raise HTTPException(status_code=400, detail="description is required")
    t = {
        "id": uuid.uuid4().hex,
        "description": desc,
        "task_type": payload.get("task_type", "build"),
        "agent_type": payload.get("agent_type", "builder"),
        "complexity": payload.get("complexity", "medium"),
        "provider": payload.get("provider"),
        "model": payload.get("model"),
        "session_id": payload.get("session_id"),
        "enqueued_ts": int(time.time()*1000),
    }
    _TASKS[t["id"]] = {"status": "queued", "task": t}
    _TASK_QUEUE.append(t)
    _ensure_worker()
    _autoscale()
    return {"enqueued": True, "id": t["id"], "status": "queued"}


@router.post("/builder/scale/config")
def set_scale_config(payload: Dict[str, Any]) -> Dict[str, Any]:
    global _MIN_WORKERS, _MAX_WORKERS, _TARGET_Q_PER_WORKER
    _MIN_WORKERS = int(payload.get("min_workers", _MIN_WORKERS))
    _MAX_WORKERS = int(payload.get("max_workers", _MAX_WORKERS))
    _TARGET_Q_PER_WORKER = int(payload.get("target_q_per_worker", _TARGET_Q_PER_WORKER))
    _autoscale()
    return {"ok": True, "min_workers": _MIN_WORKERS, "max_workers": _MAX_WORKERS, "target_q_per_worker": _TARGET_Q_PER_WORKER}

@router.get("/builder/scale/status")
def scale_status() -> Dict[str, Any]:
    return {
        "min_workers": _MIN_WORKERS,
        "max_workers": _MAX_WORKERS,
        "target_q_per_worker": _TARGET_Q_PER_WORKER,
        "current_workers": sum(1 for t in _WORKER_POOL if t.is_alive()),
        "queue": len(_TASK_QUEUE),
    }


@router.get("/builder/status")
def builder_status() -> Dict[str, Any]:
    return {
        "running": _WORKER_RUNNING,
        "queued": len(_TASK_QUEUE),
        "tasks": [
            {"id": tid, "status": info["status"], "task": info.get("task"), "result": info.get("result")}
            for tid, info in list(_TASKS.items())[-50:]
        ],
    }


@router.get("/builder/health")
def builder_health() -> Dict[str, Any]:
    return {"ok": True, "running": _WORKER_RUNNING, "queue": len(_TASK_QUEUE), "workers": sum(1 for t in _WORKER_POOL if t.is_alive())}

@router.get("/builder/metrics")
def builder_metrics() -> Dict[str, Any]:
    return {
        "avg_queue_wait_ms": _METRICS["avg_queue_wait_ms"],
        "avg_task_run_ms": _METRICS["avg_task_run_ms"],
        "samples": _METRICS["samples"],
        "worker_count": sum(1 for t in _WORKER_POOL if t.is_alive()),
        "saturation": _METRICS["saturation"],
        "history": _METRICS["history"],
    }

@router.post("/builder/scale/hysteresis")
def set_hysteresis(payload: Dict[str, Any]) -> Dict[str, Any]:
    _HYSTERESIS_CFG["epsilon"] = int(payload.get("epsilon", _HYSTERESIS_CFG["epsilon"]))
    _HYSTERESIS_CFG["scale_out_n"] = int(payload.get("scale_out_n", _HYSTERESIS_CFG["scale_out_n"]))
    _HYSTERESIS_CFG["scale_in_n"] = int(payload.get("scale_in_n", _HYSTERESIS_CFG["scale_in_n"]))
    return {"ok": True, "hysteresis": _HYSTERESIS_CFG}