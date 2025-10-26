import os
import json
import time
import uuid
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from routers.access_controller import require_api_key

router = APIRouter(prefix="/omni", tags=["omnibrain"]) 

STORE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
TASKS_FILE = os.path.join(STORE_DIR, "omni_brain_tasks.json")
CATALOG_FILE = os.path.join(STORE_DIR, "billing_catalog.json")


def _ensure():
    os.makedirs(STORE_DIR, exist_ok=True)
    if not os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump({"tasks": []}, f)
    if not os.path.exists(CATALOG_FILE):
        with open(CATALOG_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def _load_tasks() -> Dict[str, Any]:
    _ensure()
    try:
        return json.load(open(TASKS_FILE, "r", encoding="utf-8"))
    except Exception:
        return {"tasks": []}


def _save_tasks(data: Dict[str, Any]):
    _ensure()
    json.dump(data, open(TASKS_FILE, "w", encoding="utf-8"), indent=2)


def _load_catalog() -> list[dict]:
    _ensure()
    try:
        return json.load(open(CATALOG_FILE, "r", encoding="utf-8"))
    except Exception:
        return []


def _save_catalog(items: list[dict]):
    _ensure()
    json.dump(items, open(CATALOG_FILE, "w", encoding="utf-8"), indent=2)


@router.get("/brain/tasks")
async def list_tasks(_: None = Depends(require_api_key)):
    tasks = _load_tasks()
    return {"ok": True, "count": len(tasks.get("tasks", [])), "tasks": tasks.get("tasks", [])}


@router.post("/brain/tasks/{task_id}/run")
async def run_task(task_id: str, _: None = Depends(require_api_key)):
    tasks = _load_tasks()
    found = None
    for t in tasks.get("tasks", []):
        if t.get("id") == task_id:
            found = t
            break
    if not found:
        raise HTTPException(status_code=404, detail="task not found")

    if found.get("status") == "completed":
        return {"ok": True, "already": True, "task": found}

    ttype = found.get("type")
    if ttype == "api_generate":
        # Simulate API generation by creating a billing catalog item
        items = _load_catalog()
        item_id = uuid.uuid4().hex
        name = f"Auto API: {found.get('payload', {}).get('feature_name', 'unknown')}"
        new_item = {
            "id": item_id,
            "name": name,
            "version": "v1",
            "price_per_call": 0.0,
            "currency": "USD",
            "path": "/api/v1/unknown",
            "tenant_id": None,
            "description": "Auto-generated API from OmniBrain task",
            "created_at": int(time.time() * 1000),
            "meta": {"policy_entry_id": found.get("meta", {}).get("policy_entry_id")},
        }
        items.append(new_item)
        _save_catalog(items)
        found["status"] = "completed"
        found["result"] = {"created_catalog_item_id": item_id}
        _save_tasks(tasks)
        return {"ok": True, "task": found}
    elif ttype == "billing_integrate":
        # Simulate integration by marking completed
        found["status"] = "completed"
        found["result"] = {"integration": "stripe_stub"}
        _save_tasks(tasks)
        return {"ok": True, "task": found}
    else:
        raise HTTPException(status_code=400, detail=f"unknown task type: {ttype}")