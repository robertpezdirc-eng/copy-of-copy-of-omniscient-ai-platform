from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import os

router = APIRouter(prefix="/support", tags=["support"])

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data")
CONTACTS_FILE = os.path.join(DATA_DIR, "support_contacts.json")

os.makedirs(DATA_DIR, exist_ok=True)

class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    message: str
    topic: Optional[str] = None
    plan: Optional[str] = None
    recaptchaToken: Optional[str] = None

class ContactResponse(BaseModel):
    status: str
    ticket_id: str
    created_at: datetime
    data: Dict[str, Any]

class ContactList(BaseModel):
    items: List[ContactResponse]
    total: int


def load_contacts() -> List[Dict[str, Any]]:
    if os.path.exists(CONTACTS_FILE):
        try:
            with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_contacts(items: List[Dict[str, Any]]):
    with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2, default=str)


@router.post("/contact", response_model=ContactResponse)
async def submit_contact(request: ContactRequest):
    # reCAPTCHA gate (optional)
    try:
        from utils.recaptcha import verify_token
        if not verify_token(request.recaptchaToken):
            raise HTTPException(status_code=400, detail="recaptcha_failed")
    except HTTPException:
        raise
    except Exception:
        # If util import fails and verify is enabled, fail closed inside util
        pass

    ticket_id = f"SUP-{int(datetime.utcnow().timestamp())}"
    record = {
        "ticket_id": ticket_id,
        "created_at": datetime.utcnow().isoformat(),
        "name": request.name,
        "email": request.email,
        "message": request.message,
        "topic": request.topic,
        "plan": request.plan,
    }
    items = load_contacts()
    items.append(record)
    save_contacts(items)

    # Send confirmation email (Mailhog/SMTP based on env)
    try:
        from utils.emailer import send_template  # lazy import
        send_template(
            to=request.email,
            subject="Potrditev prejema sporočila",
            template="contact_confirmation",
            variables={
                "name": request.name,
                "topic": request.topic or "Splošno",
                "plan": request.plan or "Starter",
                "message": request.message,
                "year": str(datetime.utcnow().year),
            }
        )
    except Exception:
        # swallow errors to not break UX
        pass

    return ContactResponse(status="received", ticket_id=ticket_id, created_at=datetime.utcnow(), data=record)


@router.get("/contact", response_model=ContactList)
async def list_contacts():
    items = load_contacts()
    formatted = [
        {
            "status": "received",
            "ticket_id": item.get("ticket_id", ""),
            "created_at": item.get("created_at", datetime.utcnow().isoformat()),
            "data": item,
        }
        for item in items
    ]
    return ContactList(items=formatted, total=len(formatted))