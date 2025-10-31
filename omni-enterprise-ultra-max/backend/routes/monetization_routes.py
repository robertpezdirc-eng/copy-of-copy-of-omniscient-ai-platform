from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class SubscriptionRequest(BaseModel):
    plan: str

@router.post("/subscribe")
def subscribe(req: SubscriptionRequest):
    return {"status": "subscribed", "plan": req.plan}

@router.get("/plans")
def plans():
    return {"plans": ["starter", "pro", "enterprise"]}
