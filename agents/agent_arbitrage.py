import os
from typing import List, Dict, Any

from fastapi import Body
from pydantic import BaseModel, Field

from .common import build_app


app = build_app("omni-arbitrage")


class Workload(BaseModel):
    name: str
    cpu_hours: float = 0.0
    mem_gb_hours: float = 0.0
    storage_gb_month: float = 0.0
    egress_gb: float = 0.0


class ArbitrageRequest(BaseModel):
    current_provider: str = Field("aws", description="aws|gcp|azure")
    region: str = Field("us-east-1")
    workloads: List[Workload] = Field(default_factory=list)


PRICE: Dict[str, Dict[str, float]] = {
    # very rough normalized unit prices for demo purposes
    "aws": {"cpu_hour": 0.032, "mem_gb_hour": 0.0042, "storage_gb_month": 0.021, "egress_gb": 0.085},
    "gcp": {"cpu_hour": 0.030, "mem_gb_hour": 0.0040, "storage_gb_month": 0.020, "egress_gb": 0.080},
    "azure": {"cpu_hour": 0.034, "mem_gb_hour": 0.0044, "storage_gb_month": 0.022, "egress_gb": 0.087},
}


def cost_for(provider: str, wl: Workload) -> float:
    p = PRICE.get(provider, PRICE["aws"])
    return (
        wl.cpu_hours * p["cpu_hour"]
        + wl.mem_gb_hours * p["mem_gb_hour"]
        + wl.storage_gb_month * p["storage_gb_month"]
        + wl.egress_gb * p["egress_gb"]
    )


@app.post("/predict")
async def predict(req: ArbitrageRequest):
    providers = list(PRICE.keys())
    totals: Dict[str, float] = {pv: 0.0 for pv in providers}
    breakdown: Dict[str, Dict[str, float]] = {pv: {} for pv in providers}
    for wl in req.workloads:
        for pv in providers:
            c = cost_for(pv, wl)
            totals[pv] += c
            breakdown[pv][wl.name] = c
    current_total = totals.get(req.current_provider, 0.0)
    best = min(totals.items(), key=lambda x: x[1]) if totals else (req.current_provider, current_total)
    savings = max(0.0, current_total - best[1])
    saving_pct = (savings / current_total) * 100.0 if current_total > 0 else 0.0
    return {
        "current_provider": req.current_provider,
        "costs": totals,
        "breakdown": breakdown,
        "best_provider": best[0],
        "predicted_savings": round(savings, 2),
        "predicted_savings_pct": round(saving_pct, 2),
        "notes": [
            "Prices are illustrative; plug in real SKU pricing for accuracy.",
            "Consider egress locality and committed use discounts.",
        ],
    }