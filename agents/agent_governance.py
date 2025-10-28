import os
import json
from datetime import datetime
from typing import List, Dict, Any

from fastapi import Body
from pydantic import BaseModel, Field

from .common import build_app


app = build_app("omni-governance")


GOV_DB_PATH = os.getenv("GOV_DB_PATH", "/workspace/data/governance.json")


class FundInfo(BaseModel):
    name: str
    domicile: str
    manager: str
    aum_musd: float = Field(0.0, description="Assets under management in millions USD")


class PolicyCheck(BaseModel):
    policy: str
    passed: bool
    notes: str | None = None


class CertificationRequest(BaseModel):
    fund: FundInfo
    policies: List[PolicyCheck] = Field(default_factory=list)
    evidence_urls: List[str] = Field(default_factory=list)


DEFAULT_POLICIES = [
    "KYC/AML controls",
    "Investment mandate adherence",
    "Risk limits and VaR reporting",
    "Liquidity management policy",
    "Best execution and broker review",
    "Cybersecurity baseline and incident response",
    "Operational resilience and BCP/DR",
]


def _read_db() -> Dict[str, Any]:
    try:
        if os.path.exists(GOV_DB_PATH):
            with open(GOV_DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        return {"certifications": []}
    return {"certifications": []}


def _write_db(data: Dict[str, Any]):
    os.makedirs(os.path.dirname(GOV_DB_PATH), exist_ok=True)
    with open(GOV_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


@app.get("/policies")
async def policies():
    return {"baseline_policies": DEFAULT_POLICIES}


@app.post("/certify/fund")
async def certify(req: CertificationRequest = Body(...)):
    total = max(1, len(req.policies) or len(DEFAULT_POLICIES))
    passed = sum(1 for p in req.policies if p.passed) if req.policies else int(0.6 * len(DEFAULT_POLICIES))
    score = round(100.0 * passed / total, 1)
    risk = "low" if score >= 80 else "medium" if score >= 60 else "high"
    cert = {
        "id": f"cert-{int(datetime.utcnow().timestamp())}",
        "fund": req.fund.dict(),
        "score": score,
        "risk": risk,
        "policies": [p.dict() for p in req.policies] if req.policies else DEFAULT_POLICIES,
        "evidence_urls": req.evidence_urls,
        "issued_at": datetime.utcnow().isoformat() + "Z",
    }
    db = _read_db()
    db.setdefault("certifications", []).append(cert)
    _write_db(db)
    return {"certificate": cert}


@app.get("/audit/report")
async def audit_report():
    db = _read_db()
    certs = db.get("certifications", [])
    summary = {
        "total": len(certs),
        "avg_score": round(sum(c.get("score", 0) for c in certs) / max(1, len(certs)), 1) if certs else 0,
        "by_risk": {
            "low": sum(1 for c in certs if c.get("risk") == "low"),
            "medium": sum(1 for c in certs if c.get("risk") == "medium"),
            "high": sum(1 for c in certs if c.get("risk") == "high"),
        },
    }
    return {"summary": summary, "entries": certs[-25:]}