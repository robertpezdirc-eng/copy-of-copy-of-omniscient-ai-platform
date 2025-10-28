import os
import json
from datetime import datetime
from typing import List, Dict, Any

from fastapi import Body
from pydantic import BaseModel, Field

from .common import build_app


app = build_app("omni-autolearn")


PATCH_DIR = os.getenv("AUTOLEARN_PATCH_DIR", "/workspace/patches")
STATE_PATH = os.getenv("AUTOLEARN_STATE_PATH", "/workspace/data/autolearn.json")


class ProposePatchRequest(BaseModel):
    error_log: str = Field(..., description="Error output or stack trace to analyze")
    context_files: List[str] = Field(default_factory=list, description="Important file paths for context")
    strategy: str = Field(
        default="minimal",
        description="Patch strategy: minimal|robust|refactor",
    )


class LearnEvent(BaseModel):
    kind: str = Field(..., description="event type, e.g. test_failure, deploy_issue, success")
    message: str
    meta: Dict[str, Any] = Field(default_factory=dict)


def _read_state() -> Dict[str, Any]:
    try:
        if os.path.exists(STATE_PATH):
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        return {"events": []}
    return {"events": []}


def _write_state(data: Dict[str, Any]):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


@app.post("/propose-patch")
async def propose_patch(req: ProposePatchRequest = Body(...)):
    os.makedirs(PATCH_DIR, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    patch_name = f"suggested_{req.strategy}_{ts}.patch"

    # Heuristic suggestion: capture symptom and propose guarded fix
    header = "*** Begin Patch\n"
    footer = "*** End Patch\n"
    body_lines = [
        "# This is a suggested patch. Review before applying.",
        f"# Strategy: {req.strategy}",
        f"# Context files: {', '.join(req.context_files) if req.context_files else 'n/a'}",
        "# Symptom excerpt:",
    ]
    excerpt = "\n".join(req.error_log.splitlines()[:12])
    body_lines.append(excerpt)
    body_lines.append("# Suggested actions:")
    if "ImportError" in req.error_log or "ModuleNotFoundError" in req.error_log:
        body_lines.append("- Add missing import or dependency; verify requirements.txt/pyproject.toml")
    if "KeyError" in req.error_log:
        body_lines.append("- Add safe dict access with .get(...) and sensible default")
    if "TypeError" in req.error_log:
        body_lines.append("- Add type guard and input validation at function boundary")
    if "ValueError" in req.error_log:
        body_lines.append("- Validate inputs; handle invalid values with clear error message")
    if "AttributeError" in req.error_log:
        body_lines.append("- Guard optional attributes and check None before access")
    if "ConnectionRefused" in req.error_log or "ECONNREFUSED" in req.error_log:
        body_lines.append("- Add retry/backoff and health check for upstream service")
    if not any(s.startswith("-") for s in body_lines[-6:]):
        body_lines.append("- Add logging and unit test for failing path")

    content = header + "".join(l + "\n" for l in body_lines) + footer
    with open(os.path.join(PATCH_DIR, patch_name), "w", encoding="utf-8") as f:
        f.write(content)

    return {
        "patch_file": os.path.join(PATCH_DIR, patch_name),
        "summary": "Suggested patch generated. Review and apply manually.",
    }


@app.post("/learn")
async def learn(event: LearnEvent = Body(...)):
    state = _read_state()
    rec = event.dict()
    rec["ts"] = datetime.utcnow().isoformat() + "Z"
    state.setdefault("events", []).append(rec)
    _write_state(state)
    # Simple heuristic memory: last 100 events only
    if len(state["events"]) > 100:
        state["events"] = state["events"][-100:]
        _write_state(state)
    return {"ok": True, "stored": len(state["events"]) }


@app.get("/learn/history")
async def history(limit: int = 20):
    state = _read_state()
    return {"events": state.get("events", [])[-max(1, min(limit, 50)):]}