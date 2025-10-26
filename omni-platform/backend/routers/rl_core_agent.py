import os
import json
import time
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from routers.access_controller import require_api_key

router = APIRouter(prefix="/rl", tags=["rl-core"]) 

STORE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
CATALOG_FILE = os.path.join(STORE_DIR, "billing_catalog.json")
POLICIES_FILE = os.path.join(STORE_DIR, "policies.json")


def _ensure():
    os.makedirs(STORE_DIR, exist_ok=True)
    if not os.path.exists(CATALOG_FILE):
        with open(CATALOG_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    if not os.path.exists(POLICIES_FILE):
        with open(POLICIES_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)


def _load(path: str) -> Dict[str, Any]:
    _ensure()
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _save(path: str, data: Dict[str, Any]):
    _ensure()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


@router.post("/market/process")
def process_market(payload: Dict[str, Any], _: None = Depends(require_api_key)) -> Dict[str, Any]:
    """
    Process netagent-like market data and automatically create services:
    - Input: { "trends": [ {"name": "AI-Translate", "price": 0.01, "currency": "USD"}, ... ] }
    - Creates global catalog entries (tenant_id=None) for each trend
    - Updates revenue policies history with distribution notes
    """
    trends: List[Dict[str, Any]] = payload.get("trends") or []
    if not isinstance(trends, list):
        raise HTTPException(status_code=400, detail="trends must be a list")

    catalog = _load(CATALOG_FILE)
    policies = _load(POLICIES_FILE)
    created: List[Dict[str, Any]] = []

    for t in trends:
        name = str(t.get("name") or "Unnamed Service")
        price = float(t.get("price") or 0.0)
        currency = str(t.get("currency") or "USD")
        cid = uuid.uuid4().hex
        item = {
            "id": cid,
            "name": name,
            "version": "v1",
            "price_per_call": price,
            "currency": currency,
            "path": "/api/v1/unknown",
            "tenant_id": None,  # global distribution
            "description": f"Auto service from market trend: {name}",
            "created_at": int(time.time() * 1000),
            "meta": {"source": "rl-core-market"},
        }
        catalog[cid] = item
        created.append(item)

    # Update revenue policy distribution note
    rev_state = policies.get("revenue") or {}
    note_id = uuid.uuid4().hex
    note_entry = {
        "id": note_id,
        "tenant_id": None,
        "feature_name": "market-services",
        "rollout": 100,
        "enabled": True,
        "created_at": int(time.time() * 1000),
        "notes": f"Distributed {len(created)} services globally from market data",
    }
    rev_state.setdefault("history", []).append(note_entry)
    rev_state["last"] = note_entry
    policies["revenue"] = rev_state

    _save(CATALOG_FILE, catalog)
    _save(POLICIES_FILE, policies)

    return {"ok": True, "created": len(created), "items": created}