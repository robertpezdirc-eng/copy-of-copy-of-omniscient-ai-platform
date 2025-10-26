import os
import json
import time
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from routers.access_controller import require_api_key

router = APIRouter(prefix="/model", tags=["model-governance"])

STORE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
REGISTRY_FILE = os.path.join(STORE_DIR, "model_registry.json")

def _ensure_store():
    os.makedirs(STORE_DIR, exist_ok=True)
    if not os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)


def _load() -> Dict[str, Any]:
    _ensure_store()
    with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _save(data: Dict[str, Any]):
    _ensure_store()
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class RegisterRequest(BaseModel):
    provider: str
    model: str
    version: Optional[str] = None


class TestRequest(BaseModel):
    model_id: str


class IntegrateRequest(BaseModel):
    model_id: str


class DeprecateRequest(BaseModel):
    model_id: str


@router.get("/models")
async def list_models(_: None = Depends(require_api_key)):
    reg = _load()
    return JSONResponse({"models": list(reg.values())})


@router.post("/register")
async def register(req: RegisterRequest, _: None = Depends(require_api_key)):
    reg = _load()
    model_id = uuid.uuid4().hex
    item = {
        "id": model_id,
        "provider": req.provider,
        "model": req.model,
        "version": req.version or "v1",
        "status": "candidate",
        "active": False,
        "created_at": int(time.time() * 1000),
    }
    reg[model_id] = item
    _save(reg)
    return JSONResponse({"registered": True, "model": item})


@router.post("/test")
async def test_model(req: TestRequest, _: None = Depends(require_api_key)):
    reg = _load()
    item = reg.get(req.model_id)
    if not item:
        raise HTTPException(status_code=404, detail="model not found")
    # Simuliran test
    item["status"] = "tested"
    item["functional"] = True
    item["latency_ms"] = 100
    item["updated_at"] = int(time.time() * 1000)
    reg[item["id"]] = item
    _save(reg)
    return JSONResponse({"tested": True, "model": item})


@router.post("/integrate")
async def integrate_model(req: IntegrateRequest, _: None = Depends(require_api_key)):
    reg = _load()
    item = reg.get(req.model_id)
    if not item:
        raise HTTPException(status_code=404, detail="model not found")
    if not item.get("functional"):
        raise HTTPException(status_code=400, detail="model not functional")
    item["status"] = "active"
    item["active"] = True
    item["updated_at"] = int(time.time() * 1000)
    reg[item["id"]] = item
    _save(reg)
    return JSONResponse({"integrated": True, "model": item})


@router.post("/deprecate")
async def deprecate_model(req: DeprecateRequest, _: None = Depends(require_api_key)):
    reg = _load()
    item = reg.get(req.model_id)
    if not item:
        raise HTTPException(status_code=404, detail="model not found")
    item["status"] = "deprecated"
    item["active"] = False
    item["updated_at"] = int(time.time() * 1000)
    reg[item["id"]] = item
    _save(reg)
    return JSONResponse({"deprecated": True, "model": item})
