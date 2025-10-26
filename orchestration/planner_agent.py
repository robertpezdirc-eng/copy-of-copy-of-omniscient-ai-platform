from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import os

# Safe plan schemas
class PlanStep(BaseModel):
    id: str
    tool: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)
    timeout_seconds: int = 120
    max_retries: int = 2

class Plan(BaseModel):
    workflow_id: str
    goal: str
    steps: List[PlanStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    budget_seconds: int = 300
    max_cost_usd: Optional[float] = None

# Allowed tool names (expand via tools_registry.py)
ALLOWED_TOOLS = {"echo", "gemini_text"}


def _generate_workflow_id(goal: str) -> str:
    import hashlib
    return "wf-" + hashlib.sha1((goal + str(datetime.utcnow())).encode()).hexdigest()[:12]


def generate_plan(goal: str, context: Optional[Dict[str, Any]] = None,
                  tools: Optional[List[str]] = None,
                  caps: Optional[Dict[str, Any]] = None) -> Plan:
    """Basic planner: validates tools, enforces caps, returns a minimal executable plan.

    In production, replace with an LLM-based planner (Gemini/OpenAI) ensuring the output
    strictly conforms to this schema and only uses ALLOWED_TOOLS.
    """
    tools = tools or ["echo"]
    # Enforce allowed tools
    for t in tools:
        if t not in ALLOWED_TOOLS:
            raise ValueError(f"Tool '{t}' not allowed. Allowed: {sorted(ALLOWED_TOOLS)}")

    # Choose preferred tool: prioritize gemini_text when requested
    selected_tool = tools[0]
    if "gemini_text" in tools:
        selected_tool = "gemini_text"

    # Caps
    budget_seconds = int((caps or {}).get("budget_seconds", 300))
    max_cost_usd = (caps or {}).get("max_cost_usd")

    workflow_id = _generate_workflow_id(goal)

    # Minimal single-step plan using selected tool
    inputs = {"text": goal, "context": context or {}}
    # Optionally include system instruction if provided via environment for Gemini
    system_prompt = os.getenv("GEMINI_SYSTEM_PROMPT")
    if selected_tool == "gemini_text" and system_prompt:
        inputs["system"] = system_prompt

    step1 = PlanStep(
        id="step-1",
        tool=selected_tool,
        inputs=inputs,
        depends_on=[],
        timeout_seconds=min(120, budget_seconds),
        max_retries=2,
    )
    plan = Plan(
        workflow_id=workflow_id,
        goal=goal,
        steps=[step1],
        budget_seconds=budget_seconds,
        max_cost_usd=max_cost_usd,
    )
    return plan