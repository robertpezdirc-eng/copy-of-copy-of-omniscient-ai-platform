import json
import os
from datetime import datetime
from typing import Optional

from fastapi import Body
from pydantic import BaseModel, Field

from .common import build_app


app = build_app("omni-burnout")


TASKS_DB_PATH = os.getenv("TASKS_DB_PATH", "/workspace/data/tasks.json")


class Signals(BaseModel):
    weekly_hours: float = 40
    active_tasks: int = 5
    blocked_tasks: int = 0
    interruptions_per_day: float = 5
    oncall_days: int = 0
    night_shifts_per_week: int = 0
    consecutive_weeks_without_vacation: int = 4
    context_switches_per_day: float = 6


def burnout_score(s: Signals) -> float:
    # Simple weighted model for demonstration
    score = 0.0
    score += max(0, s.weekly_hours - 40) * 1.2
    score += s.active_tasks * 0.8
    score += s.blocked_tasks * 2.5
    score += s.interruptions_per_day * 0.9
    score += s.oncall_days * 1.5
    score += s.night_shifts_per_week * 2.0
    score += s.consecutive_weeks_without_vacation * 0.7
    score += s.context_switches_per_day * 0.6
    # normalize to 0-100 (roughly)
    return min(100.0, score)


def risk_label(score: float) -> str:
    if score < 30:
        return "low"
    if score < 60:
        return "medium"
    return "high"


@app.post("/predict")
async def predict(signals: Signals = Body(...)):
    score = burnout_score(signals)
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "score": round(score, 1),
        "risk": risk_label(score),
        "recommendations": [
            "Set WIP limits and reduce context switching.",
            "Schedule focus blocks and mute non-urgent notifications.",
            "Plan time-off; avoid > 6 consecutive weeks without vacation.",
            "Escalate blocked tasks early; assign pair or unblock owner.",
        ],
    }


def _read_tasks_db():
    try:
        if os.path.exists(TASKS_DB_PATH):
            with open(TASKS_DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        return None
    return None


@app.get("/from-tasks")
async def from_tasks():
    data = _read_tasks_db() or {"projects": []}
    active = 0
    blocked = 0
    for p in data.get("projects", []):
        for t in p.get("tasks", []):
            if t.get("status") in {"todo", "in_progress"}:
                active += 1
            if t.get("status") == "blocked" or t.get("blocked", False):
                blocked += 1
    signals = Signals(active_tasks=active, blocked_tasks=blocked)
    score = burnout_score(signals)
    return {
        "derived_from": TASKS_DB_PATH,
        "active_tasks": active,
        "blocked_tasks": blocked,
        "score": round(score, 1),
        "risk": risk_label(score),
    }