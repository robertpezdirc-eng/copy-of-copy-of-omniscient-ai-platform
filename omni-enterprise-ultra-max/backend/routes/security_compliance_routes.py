from fastapi import APIRouter
security_router = APIRouter()
@security_router.get("/status")
def status():
    return {"ok": True}
