from .common import build_app
from pydantic import BaseModel

app = build_app("finops_agent")


class CostEvent(BaseModel):
    service: str
    severity: str
    est_cost_usd: float
    description: str = ""


@app.post("/analyze")
async def analyze(events: list[CostEvent]):
    total = sum(e.est_cost_usd for e in events)
    by_service = {}
    for e in events:
        by_service.setdefault(e.service, 0.0)
        by_service[e.service] += e.est_cost_usd
    return {"total_cost_usd": total, "by_service": by_service, "count": len(events)}