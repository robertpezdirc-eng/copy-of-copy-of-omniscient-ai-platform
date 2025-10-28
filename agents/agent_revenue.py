from typing import List, Dict, Any
from fastapi import Body
from pydantic import BaseModel, Field

from .common import build_app


app = build_app("omni-revenue")


class Product(BaseModel):
    id: str
    name: str
    price: float
    cost: float
    ctr: float = Field(0.02, description="click-through rate")
    conv: float = Field(0.05, description="conversion rate")
    demand_elasticity: float = Field(-1.2, description="% change in demand / % price change")


class OptimizeRequest(BaseModel):
    products: List[Product]
    avg_traffic: int = 10000
    target_margin: float = 0.25


@app.post("/optimize")
async def optimize(req: OptimizeRequest = Body(...)):
    recs = []
    uplift_total = 0.0
    for p in req.products:
        # Simple rule: nudge price toward target margin while respecting elasticity
        current_margin = (p.price - p.cost) / max(1e-6, p.price)
        delta_margin = req.target_margin - current_margin
        # translate margin delta to price change with small step and elasticity dampening
        adj = p.price * 0.1 * delta_margin
        adj /= max(0.5, abs(p.demand_elasticity))
        new_price = max(p.cost * 1.02, round(p.price + adj, 2))

        # estimate revenue uplift
        visits = req.avg_traffic * p.ctr
        base_sales = visits * p.conv
        price_change_pct = (new_price - p.price) / max(1e-6, p.price)
        new_conv = max(0.005, p.conv * (1.0 + p.demand_elasticity * price_change_pct))
        new_sales = visits * new_conv
        base_rev = base_sales * p.price
        new_rev = new_sales * new_price
        uplift = new_rev - base_rev
        uplift_total += uplift

        recs.append({
            "product_id": p.id,
            "name": p.name,
            "current_price": p.price,
            "recommended_price": new_price,
            "estimated_uplift": round(uplift, 2),
            "assumptions": {
                "visits": round(visits),
                "base_conv": p.conv,
                "new_conv": round(new_conv, 4),
                "elasticity": p.demand_elasticity,
            },
        })
    return {"recommendations": recs, "total_estimated_uplift": round(uplift_total, 2)}


class PlaybookRequest(BaseModel):
    objective: str = Field("increase_revenue", description="increase_revenue|increase_aov|reduce_churn")


@app.post("/playbook")
async def playbook(req: PlaybookRequest = Body(...)):
    base: Dict[str, Any] = {
        "increase_revenue": [
            "Dynamic pricing with AB guardrails",
            "Personalized bundles and cross-sell",
            "Cart recovery and exit-intent offers",
            "Promote high-margin SKUs with targeted placements",
        ],
        "increase_aov": [
            "Tiered free shipping thresholds",
            "Bundle recommendations at checkout",
            "Volume discounts with margin floor",
            "Upsell accessories and warranties",
        ],
        "reduce_churn": [
            "Proactive outreach to at-risk cohorts",
            "Win-back campaigns with limited-time incentives",
            "Improve onboarding and aha-moment time",
            "Loyalty and referral loop",
        ],
    }
    steps = base.get(req.objective, base["increase_revenue"])[:4]
    kpis = ["Revenue", "AOV", "Conversion Rate", "Gross Margin"]
    return {"objective": req.objective, "steps": steps, "kpis": kpis}