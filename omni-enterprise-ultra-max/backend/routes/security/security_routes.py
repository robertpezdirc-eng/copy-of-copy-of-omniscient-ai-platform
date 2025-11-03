from fastapi import APIRouter
router = APIRouter()
@router.get("/audit")
def audit():
    return {"logs": []}
