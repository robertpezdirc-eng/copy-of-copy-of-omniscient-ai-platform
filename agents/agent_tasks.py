import os
import json
from typing import List, Dict, Optional

from fastapi import Body
from pydantic import BaseModel, Field

from .common import build_app


app = build_app("omni-tasks")


DB_PATH = os.getenv("TASKS_DB_PATH", "/workspace/data/tasks.json")


def ensure_parent(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def load_db() -> Dict:
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"projects": {}, "tasks": []}


def save_db(db: Dict) -> None:
    ensure_parent(DB_PATH)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)


class Task(BaseModel):
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    priority: str = Field("medium", description="low|medium|high|critical")
    status: str = Field("todo", description="todo|in_progress|blocked|done")
    labels: List[str] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)
    project: Optional[str] = None


class AutoPlanRequest(BaseModel):
    goal: str
    constraints: List[str] = Field(default_factory=list)
    prefer_fast_delivery: bool = True


@app.get("/projects")
async def list_projects():
    db = load_db()
    return {"projects": list(db.get("projects", {}).keys())}


@app.get("/tasks")
async def list_tasks(project: Optional[str] = None, status: Optional[str] = None):
    db = load_db()
    tasks = db.get("tasks", [])
    if project:
        tasks = [t for t in tasks if t.get("project") == project]
    if status:
        tasks = [t for t in tasks if t.get("status") == status]
    return {"count": len(tasks), "tasks": tasks}


@app.post("/tasks")
async def create_task(task: Task = Body(...)):
    db = load_db()
    task.id = task.id or f"t{len(db.get('tasks', []))+1}"
    db.setdefault("tasks", []).append(task.model_dump())
    if task.project:
        db.setdefault("projects", {}).setdefault(task.project, {})
    save_db(db)
    return task


@app.post("/tasks/{task_id}/status")
async def update_status(task_id: str, status: str = Body(..., embed=True)):
    db = load_db()
    for t in db.get("tasks", []):
        if t.get("id") == task_id:
            t["status"] = status
            save_db(db)
            return {"updated": True, "task": t}
    return {"updated": False, "error": "not-found"}


@app.post("/tasks/auto-plan")
async def auto_plan(req: AutoPlanRequest):
    steps: List[Dict[str, str]] = []
    steps.append({"step": "clarify", "desc": f"Clarify goal: {req.goal}"})
    steps.append({"step": "design", "desc": "Draft minimal design and acceptance criteria"})
    steps.append({"step": "implement", "desc": "Implement smallest slice end-to-end"})
    steps.append({"step": "verify", "desc": "Run self-test and generate docs"})
    if req.prefer_fast_delivery:
        steps.append({"step": "ship", "desc": "Release as feature flag, observe metrics"})
    else:
        steps.append({"step": "harden", "desc": "Add tests, resilience, optimize costs"})
    return {"plan": steps, "constraints": req.constraints}