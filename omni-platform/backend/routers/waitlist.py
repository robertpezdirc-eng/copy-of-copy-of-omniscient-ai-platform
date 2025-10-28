from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import os
import json

from utils.ga4 import send_event

router = APIRouter(prefix="/waitlist", tags=["waitlist"])

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
WAITLIST_FILE = os.path.join(DATA_DIR, "waitlist.json")
os.makedirs(DATA_DIR, exist_ok=True)


class WaitlistRequest(BaseModel):
    email: EmailStr
    source: Optional[str] = "grafana"


@router.post("")
async def join_waitlist(req: WaitlistRequest):
    try:
        items = []
        if os.path.exists(WAITLIST_FILE):
            with open(WAITLIST_FILE, "r", encoding="utf-8") as f:
                items = json.load(f)
        record = {
            "email": req.email,
            "source": req.source,
            "created_at": datetime.utcnow().isoformat(),
        }
        items.append(record)
        with open(WAITLIST_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"save_failed: {e}")

    # GA4 event
    await send_event(
        event_name="waitlist_signup",
        params={"source": req.source, "currency": "EUR"},
    )

    return {"ok": True, "message": "joined", "email": req.email}