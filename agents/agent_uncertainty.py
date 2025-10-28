from typing import List, Optional, Dict, Any

from fastapi import Body
from pydantic import BaseModel, Field

from .common import build_app


app = build_app("omni-uncertainty")


class ResolveRequest(BaseModel):
    question: str
    constraints: List[str] = Field(default_factory=list)
    budget_steps: int = 5
    hints: List[str] = Field(default_factory=list)
    prefer_docs: bool = True


@app.post("/resolve")
async def resolve(req: ResolveRequest = Body(...)):
    steps: List[Dict[str, Any]] = []
    if req.prefer_docs:
        steps.append({
            "action": "generate_docs",
            "service": "omni-docgen",
            "endpoint": "/generate",
            "reason": "Create/refresh technical docs to reduce ambiguity.",
        })
    steps.append({
        "action": "summarize_context",
        "service": "omni-minctx",
        "endpoint": "/summarize",
        "payload": {"topic": req.question, "hints": req.hints[-5:]},
        "reason": "Minimize repository context to just what matters.",
    })
    steps.append({
        "action": "qualify_value",
        "service": "omni-value",
        "endpoint": "/qualify",
        "payload": {"product": req.question, "market": "internal"},
        "reason": "Estimate value-of-information and prioritize probes.",
    })
    while len(steps) < max(2, req.budget_steps):
        steps.append({
            "action": "ask_stakeholders",
            "service": "omni-pov",
            "endpoint": "/challenge/register",
            "payload": {"name": f"clarify-{len(steps)}", "contact": "n/a"},
            "reason": "De-risk by capturing assumptions and explicit acceptance.",
        })
    result = {
        "question": req.question,
        "constraints": req.constraints,
        "plan": steps,
        "predicted_confidence_delta": 0.25 + 0.1 * min(3, len(steps) - 2),
        "next_actions": [
            "Execute first two steps and reassess remaining uncertainty.",
            "Track assumptions explicitly; convert to tests where feasible.",
        ],
    }
    return result