import os
from typing import List, Dict, Any

from fastapi import Body
from pydantic import BaseModel, Field

from .common import build_app, get_async_client


app = build_app("omni-marketing")


VALUE_URL = os.getenv("VALUE_URL", "http://omni-value:8000")


class PropositionRequest(BaseModel):
    product: str
    audience: str
    category: str = Field("business")
    description: str | None = None
    metrics: List[Dict[str, Any]] = Field(default_factory=list)
    extra_signals: Dict[str, float] = Field(default_factory=dict)


class CampaignRequest(BaseModel):
    goal: str
    channels: List[str] = Field(default_factory=lambda: ["web", "email", "social"]) 
    budget: float = 0.0
    duration_days: int = 14


def craft_copy(score: float, product: str, audience: str, category: str) -> str:
    tier = "Exceptional" if score >= 0.85 else "Strong" if score >= 0.7 else "Emerging"
    return (
        f"{tier} value for {audience}: {product} demonstrates measurable {category} impact. "
        f"Composite score {score:.2f}. Act now to leverage momentum."
    )


@app.post("/propositions")
async def propositions(req: PropositionRequest):
    client = get_async_client()
    payload = {
        "title": f"{req.product} value for {req.audience}",
        "category": req.category,
        "description": req.description,
        "metrics": req.metrics,
        "extra_signals": req.extra_signals,
    }
    score = 0.0
    details = {}
    try:
        r = await client.post(f"{VALUE_URL}/values/qualify", json=payload, timeout=20.0)
        r.raise_for_status()
        js = r.json()
        score = float(js.get("score", 0.0))
        details = js.get("details", {})
    except Exception:
        pass
    copy = craft_copy(score, req.product, req.audience, req.category)
    return {"score": score, "copy": copy, "details": details}


@app.post("/campaign")
async def campaign(req: CampaignRequest):
    per_channel = max(1.0, req.budget / max(1, len(req.channels)))
    plan = []
    for ch in req.channels:
        plan.append({
            "channel": ch,
            "budget": round(per_channel, 2),
            "cadence": "3 posts/week" if ch == "social" else "1 blast/week" if ch == "email" else "landing + A/B",
        })
    return {"goal": req.goal, "duration_days": req.duration_days, "plan": plan}


@app.post("/ab")
async def ab_test(req: PropositionRequest):
    client = get_async_client()
    payload = {
        "title": f"{req.product} value for {req.audience}",
        "category": req.category,
        "description": req.description,
        "metrics": req.metrics,
        "extra_signals": req.extra_signals,
    }
    base_score = 0.0
    try:
        r = await client.post(f"{VALUE_URL}/values/qualify", json=payload, timeout=20.0)
        r.raise_for_status()
        base_score = float(r.json().get("score", 0.0))
    except Exception:
        pass

    # Variant crafting: small angle changes on tone and CTA
    a_copy = craft_copy(base_score, req.product, req.audience, req.category) + " Limited-time offer."
    b_score = min(1.0, base_score + 0.05)
    b_copy = craft_copy(b_score, req.product, req.audience, req.category) + " Book a demo today."

    experiment = {
        "hypothesis": "B with stronger CTA outperforms A in CTR and conversions",
        "kpi": ["ctr", "conversion_rate"],
        "allocation": {"A": 0.5, "B": 0.5},
        "stopping_rule": "p<0.05 or 2 weeks",
        "notes": [
            "Keep creative constant; vary tone/CTA only.",
            "Ensure equal audience segments across channels.",
        ],
    }
    return {"variants": {"A": a_copy, "B": b_copy}, "scores": {"A": base_score, "B": b_score}, "experiment": experiment}