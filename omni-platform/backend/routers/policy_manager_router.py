import os
import json
import time
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from routers.access_controller import require_api_key

router = APIRouter(prefix="/policy", tags=["policy-manager"]) 

STORE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
POLICIES_FILE = os.path.join(STORE_DIR, "policies.json")
# Task queue storage for OmniBrain
TASKS_FILE = os.path.join(STORE_DIR, "omni_brain_tasks.json")


def _ensure():
    os.makedirs(STORE_DIR, exist_ok=True)
    if not os.path.exists(POLICIES_FILE):
        with open(POLICIES_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    if not os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump({"tasks": []}, f)


def _load() -> Dict[str, Any]:
    _ensure()
    with open(POLICIES_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _save(data: Dict[str, Any]):
    _ensure()
    with open(POLICIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# Task helpers

def _load_tasks() -> Dict[str, Any]:
    _ensure()
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"tasks": []}


def _save_tasks(data: Dict[str, Any]):
    _ensure()
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class RevenueEnableBody(BaseModel):
    tenant_id: str
    feature_name: Optional[str] = "auto-generated-api"
    rollout: Optional[int] = 100
    notes: Optional[str] = None


@router.post("/revenue/enable")
async def revenue_enable(body: RevenueEnableBody, _: None = Depends(require_api_key)):
    payload = body.dict()
    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    policies = _load()
    rev_state = policies.get("revenue") or {}
    entry_id = uuid.uuid4().hex
    entry = {
        "id": entry_id,
        "tenant_id": tenant_id,
        "feature_name": payload.get("feature_name") or "auto-generated-api",
        "rollout": int(payload.get("rollout") or 100),
        "enabled": True,
        "created_at": int(time.time() * 1000),
        "notes": payload.get("notes") or "",
    }
    if "history" not in rev_state:
        rev_state["history"] = []
    rev_state["history"].append(entry)
    rev_state["last"] = entry
    policies["revenue"] = rev_state
    _save(policies)

    # Queue a real OmniBrain task to generate API or integrate billing
    tasks = _load_tasks()
    task_id = uuid.uuid4().hex
    task = {
        "id": task_id,
        "type": "api_generate",
        "tenant_id": tenant_id,
        "payload": {
            "feature_name": entry["feature_name"],
            "rollout": entry["rollout"],
        },
        "status": "queued",
        "created_at": int(time.time() * 1000),
        "meta": {
            "policy_entry_id": entry_id
        }
    }
    tasks.setdefault("tasks", []).append(task)
    _save_tasks(tasks)
    return {"ok": True, "policy": "revenue", "state": rev_state, "queued_task_id": task_id}


@router.get("/revenue/status")
async def revenue_status(_: None = Depends(require_api_key)):
    policies = _load()
    rev = policies.get("revenue") or {}
    return {"ok": True, "policy": "revenue", "state": rev}


@router.get("/revenue/history")
async def revenue_history(_: None = Depends(require_api_key)):
    policies = _load()
    rev = policies.get("revenue") or {}
    history = rev.get("history", [])
    return {"ok": True, "policy": "revenue", "count": len(history), "history": history}