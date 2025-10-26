from typing import Dict, Any, Optional
from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime
import os, asyncio, json

from .planner_agent import generate_plan, Plan
from .dispatcher import dispatch_steps
from .tools_registry import execute_tool

router = APIRouter(prefix="/api/flows", tags=["orchestration"])

# Simple in-memory state (MVP). For production, use Firestore/Cloud SQL.
WORKFLOWS: Dict[str, Dict[str, Any]] = {}
EVENTS: Dict[str, list] = {}


class StartFlowRequest(BaseModel):
    goal: str
    context: Optional[Dict[str, Any]] = None
    tools: Optional[list] = None
    constraints: Optional[Dict[str, Any]] = None


@router.post("/start")
def start_flow(payload: StartFlowRequest = Body(...)):
    if os.environ.get("ORCHESTRATION_ENABLED", "1") not in ("1", "true", "True"):
        raise HTTPException(status_code=403, detail="Orchestration disabled")
    try:
        plan: Plan = generate_plan(
            goal=payload.goal,
            context=payload.context,
            tools=payload.tools,
            caps=(payload.constraints or {}),
        )
        # Persist minimal state
        WORKFLOWS[plan.workflow_id] = {
            "workflow_id": plan.workflow_id,
            "goal": plan.goal,
            "status": "running",
            "created_at": plan.created_at.isoformat(),
            "plan": plan.dict(),
            "results": [],
        }
        EVENTS.setdefault(plan.workflow_id, []).append({
            "ts": datetime.utcnow().isoformat(),
            "event": "planned",
            "detail": {"steps": [s.id for s in plan.steps]},
        })
        # Dispatch steps (MVP: publish to Pub/Sub or Cloud Tasks)
        dispatch_results = dispatch_steps(plan.workflow_id, [s.dict() for s in plan.steps])
        EVENTS[plan.workflow_id].append({
            "ts": datetime.utcnow().isoformat(),
            "event": "dispatched",
            "detail": [r.dict() for r in dispatch_results],
        })
        return {
            "ok": True,
            "workflow_id": plan.workflow_id,
            "status": WORKFLOWS[plan.workflow_id]["status"],
            "plan": plan.dict(),
            "dispatch": [r.dict() for r in dispatch_results],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{workflow_id}")
def get_flow(workflow_id: str):
    wf = WORKFLOWS.get(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


@router.get("/{workflow_id}/events")
def get_flow_events(workflow_id: str):
    ev = EVENTS.get(workflow_id, [])
    return {"events": ev}


@router.post("/{workflow_id}/step")
def execute_step(workflow_id: str, step: Dict[str, Any] = Body(...)):
    """HTTP handler compatible with Cloud Tasks: executes a step locally.
    In production, worker services would consume Pub/Sub or Tasks asynchronously.
    """
    if workflow_id not in WORKFLOWS:
        raise HTTPException(status_code=404, detail="Workflow not found")
    try:
        res = execute_tool(step.get("tool"), step.get("inputs", {}))
        WORKFLOWS[workflow_id]["results"].append({
            "step_id": step.get("id"),
            "status": "succeeded" if res.get("ok") else "failed",
            "output": res,
            "ts": datetime.utcnow().isoformat(),
        })
        # If all steps completed, mark workflow succeeded (MVP)
        planned_ids = [s["id"] for s in WORKFLOWS[workflow_id]["plan"]["steps"]]
        done_ids = [r["step_id"] for r in WORKFLOWS[workflow_id]["results"] if r["status"] == "succeeded"]
        if set(planned_ids).issubset(set(done_ids)):
            WORKFLOWS[workflow_id]["status"] = "succeeded"
        EVENTS.setdefault(workflow_id, []).append({
            "ts": datetime.utcnow().isoformat(),
            "event": "step_executed",
            "detail": {"step_id": step.get("id"), "status": res.get("ok")},
        })
        return {"ok": True, "workflow_id": workflow_id, "result": res}
    except Exception as e:
        EVENTS.setdefault(workflow_id, []).append({
            "ts": datetime.utcnow().isoformat(),
            "event": "step_failed",
            "detail": {"step_id": step.get("id"), "error": str(e)},
        })
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
def list_flows():
    """List all workflows (MVP in-memory)."""
    return {"workflows": list(WORKFLOWS.values())}

@router.get("/{workflow_id}/events/stream")
def stream_flow_events(workflow_id: str):
    """Server-Sent Events (SSE) stream for real-time workflow updates.
    Emits events appended to EVENTS[workflow_id] as JSON lines with media type text/event-stream.
    """
    if workflow_id not in WORKFLOWS:
        raise HTTPException(status_code=404, detail="Workflow not found")

    async def event_generator():
        last_index = 0
        # Initial hello event to confirm connection
        yield f"data: {json.dumps({'event':'connected','workflow_id':workflow_id})}\n\n"
        while True:
            evs = EVENTS.get(workflow_id, [])
            while last_index < len(evs):
                e = evs[last_index]
                payload = {
                    "ts": e.get("ts"),
                    "event": e.get("event"),
                    "detail": e.get("detail"),
                }
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                last_index += 1
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")