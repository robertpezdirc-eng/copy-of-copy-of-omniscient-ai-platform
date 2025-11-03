from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class Device(BaseModel):
    device_id: str

@router.post("/register")
def register(d: Device):
    return {"ok": True}

@router.get("/devices")
def devices():
    return {"devices": []}
