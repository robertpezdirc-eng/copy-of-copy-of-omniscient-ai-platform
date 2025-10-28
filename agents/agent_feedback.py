import os
import time
from typing import Optional

from fastapi import Body
from pydantic import BaseModel, Field

from .common import build_app, get_async_client


app = build_app("omni-feedback")


DOCGEN_URL = os.getenv("DOCGEN_URL", "http://omni-docgen:8000")
RELOAD_FLAG = os.getenv("RELOAD_FLAG_PATH", "/workspace/.reload.flag")


class FeedbackReport(BaseModel):
    error: str
    context: Optional[str] = None
    force_reload: bool = True
    regenerate_docs: bool = True


def touch_reload_flag() -> float:
    os.makedirs(os.path.dirname(RELOAD_FLAG), exist_ok=True)
    ts = time.time()
    with open(RELOAD_FLAG, "w", encoding="utf-8") as f:
        f.write(str(ts))
    return ts


@app.post("/feedback/report")
async def report(feedback: FeedbackReport):
    suggestions = [
        "Reproduce with minimal steps",
        "Check recent changes and metrics",
        "Regenerate docs and retry",
    ]
    doc_status = None
    if feedback.regenerate_docs:
        try:
            client = get_async_client()
            r = await client.post(f"{DOCGEN_URL}/generate", json={"title": "Omni Platform – API Overview"}, timeout=30.0)
            doc_status = r.json() if r.status_code == 200 else {"error": r.status_code}
        except Exception:
            doc_status = {"error": "docgen-failed"}
    reload_ts = None
    if feedback.force_reload:
        reload_ts = touch_reload_flag()
    return {"ack": True, "suggestions": suggestions, "reload_ts": reload_ts, "doc_status": doc_status}


@app.get("/reload/status")
async def reload_status():
    try:
        with open(RELOAD_FLAG, "r", encoding="utf-8") as f:
            ts = float(f.read().strip())
        return {"reload": True, "ts": ts}
    except Exception:
        return {"reload": False}