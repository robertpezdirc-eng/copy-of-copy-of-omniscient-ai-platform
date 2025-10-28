import os
import json
from datetime import datetime
from typing import List, Dict, Any

from fastapi import Body
from pydantic import BaseModel, Field

from .common import build_app


app = build_app("omni-knowledge")


KNOW_DB_PATH = os.getenv("KNOW_DB_PATH", "/workspace/data/knowledge.json")


class IngestItem(BaseModel):
    topic: str
    content: str
    source_url: str | None = None


class TransferRequest(BaseModel):
    topic: str
    audience: str = Field("engineers", description="target audience: engineers|sales|leadership|support")
    source_urls: List[str] = Field(default_factory=list)


def _read_db() -> Dict[str, Any]:
    try:
        if os.path.exists(KNOW_DB_PATH):
            with open(KNOW_DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        return {"docs": []}
    return {"docs": []}


def _write_db(data: Dict[str, Any]):
    os.makedirs(os.path.dirname(KNOW_DB_PATH), exist_ok=True)
    with open(KNOW_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


@app.post("/ingest")
async def ingest(item: IngestItem = Body(...)):
    db = _read_db()
    rec = item.dict()
    rec["ts"] = datetime.utcnow().isoformat() + "Z"
    db.setdefault("docs", []).append(rec)
    # keep last 500
    db["docs"] = db["docs"][-500:]
    _write_db(db)
    return {"ok": True, "count": len(db["docs"]) }


@app.post("/transfer")
async def transfer(req: TransferRequest = Body(...)):
    # Lightweight knowledge pack builder
    tone = {
        "engineers": "technical and practical",
        "sales": "value-driven and objection-handling",
        "leadership": "strategic and outcome-focused",
        "support": "procedural and customer-centric",
    }.get(req.audience, "neutral")

    summary = f"Knowledge pack for '{req.topic}' tailored for {req.audience} ({tone})."
    checklist = [
        "Understand core concepts and definitions",
        "Walk through end-to-end example",
        "Common pitfalls and how to avoid them",
        "How to measure success (KPIs)",
        "Where to ask for help and escalate",
    ]
    plan_30_60_90 = {
        "30": ["Complete fundamentals", "Shadow an expert", "Set baseline metrics"],
        "60": ["Own small initiative", "Document learnings", "Share session with team"],
        "90": ["Lead project", "Contribute improvements", "Mentor a peer"],
    }
    return {
        "summary": summary,
        "checklist": checklist,
        "plan_30_60_90": plan_30_60_90,
        "sources": req.source_urls,
    }