import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import Body, HTTPException
from pydantic import BaseModel, Field

from .common import build_app


app = build_app("omni-proliferate")


OVERRIDE_PATH = os.getenv("PROLIFERATE_OVERRIDE_PATH", "/workspace/docker-compose.local.yml")
STATE_PATH = os.getenv("PROLIFERATE_STATE_PATH", "/workspace/data/proliferate.json")


ALLOWED_PREFIXES = ["omni-", "agent-"]
MAX_REPLICAS_PER_SERVICE = int(os.getenv("PROLIFERATE_MAX_PER_SERVICE", "5"))


class ReplicateRequest(BaseModel):
    base_service: str = Field(..., description="Base service name to replicate (e.g., omni-tasks)")
    replicas: int = Field(1, ge=1, le=10, description="Number of additional replicas to create")
    expose_ports: bool = Field(False, description="If true, assign host ports sequentially")
    host_port_start: Optional[int] = Field(None, description="First host port if expose_ports=true")
    env_overrides: Dict[str, str] = Field(default_factory=dict, description="Env overrides applied to clones")


class GCRequest(BaseModel):
    base_service: Optional[str] = Field(None, description="If set, remove clones only for this base service")


def _read_state() -> Dict[str, Any]:
    try:
        if os.path.exists(STATE_PATH):
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        return {"clones": {}}
    return {"clones": {}}


def _write_state(data: Dict[str, Any]):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _guard_base(base: str):
    if not any(base.startswith(p) for p in ALLOWED_PREFIXES):
        raise HTTPException(status_code=400, detail=f"Base service '{base}' ni dovoljeno replicirati (guardrail)")


@app.post("/plan")
async def plan(req: ReplicateRequest = Body(...)):
    _guard_base(req.base_service)
    state = _read_state()
    existing = state.get("clones", {}).get(req.base_service, [])
    if len(existing) + req.replicas > MAX_REPLICAS_PER_SERVICE:
        raise HTTPException(status_code=400, detail="Presežena meja replik za storitev")

    names = [f"{req.base_service}-clone-{i+1+len(existing)}" for i in range(req.replicas)]
    ports = []
    if req.expose_ports and req.host_port_start:
        ports = [req.host_port_start + i for i in range(req.replicas)]
    return {
        "base": req.base_service,
        "replicas": req.replicas,
        "names": names,
        "host_ports": ports,
        "env_overrides": req.env_overrides,
        "guardrails": {
            "allowed_prefixes": ALLOWED_PREFIXES,
            "max_replicas_per_service": MAX_REPLICAS_PER_SERVICE,
        },
    }


def _render_override_yaml(clones: Dict[str, List[Dict[str, Any]]]) -> str:
    lines = []
    lines.append("services:")
    for base, items in clones.items():
        for item in items:
            name = item["name"]
            container = name
            lines.append(f"  {name}:")
            lines.append("    image: omni-agent:latest")
            lines.append(f"    container_name: {container}")
            lines.append("    restart: unless-stopped")
            # Clone runs same module as base is not known here; rely on base-compatible env overrides
            lines.append("    environment:")
            for k, v in item.get("env", {}).items():
                lines.append(f"      {k}: {v}")
            lines.append("    networks:")
            lines.append("      - omni-net")
            if item.get("ports"):
                lines.append("    ports:")
                for hp in item["ports"]:
                    lines.append(f"      - \"{hp}:8000\"")
            lines.append("    expose:")
            lines.append("      - \"8000\"")
    lines.append("networks:")
    lines.append("  omni-net:")
    lines.append("    external: true")
    return "\n".join(lines) + "\n"


def _persist_override(clones: Dict[str, List[Dict[str, Any]]]):
    os.makedirs(os.path.dirname(OVERRIDE_PATH), exist_ok=True)
    content = _render_override_yaml(clones)
    with open(OVERRIDE_PATH, "w", encoding="utf-8") as f:
        f.write(content)


@app.post("/materialize")
async def materialize(req: ReplicateRequest = Body(...)):
    _guard_base(req.base_service)
    state = _read_state()
    clones = state.setdefault("clones", {})
    existing = clones.setdefault(req.base_service, [])
    if len(existing) + req.replicas > MAX_REPLICAS_PER_SERVICE:
        raise HTTPException(status_code=400, detail="Presežena meja replik za storitev")

    start_idx = len(existing) + 1
    new_items = []
    for i in range(req.replicas):
        name = f"{req.base_service}-clone-{start_idx + i}"
        item: Dict[str, Any] = {"name": name, "env": {"PORT": "8000", **req.env_overrides}}
        if req.expose_ports and req.host_port_start:
            item["ports"] = [req.host_port_start + i]
        new_items.append(item)

    existing.extend(new_items)
    state["last_update"] = datetime.utcnow().isoformat() + "Z"
    _write_state(state)
    _persist_override(clones)
    return {"ok": True, "created": [n["name"] for n in new_items], "override_path": OVERRIDE_PATH}


@app.get("/status")
async def status(base: Optional[str] = None):
    state = _read_state()
    clones = state.get("clones", {})
    if base:
        return {base: clones.get(base, [])}
    return clones


@app.post("/gc")
async def garbage_collect(req: GCRequest = Body(default_factory=GCRequest)):
    state = _read_state()
    clones = state.get("clones", {})
    if req.base_service:
        clones.pop(req.base_service, None)
    else:
        clones.clear()
    state["clones"] = clones
    state["last_update"] = datetime.utcnow().isoformat() + "Z"
    _write_state(state)
    _persist_override(clones)
    return {"ok": True, "remaining": clones}