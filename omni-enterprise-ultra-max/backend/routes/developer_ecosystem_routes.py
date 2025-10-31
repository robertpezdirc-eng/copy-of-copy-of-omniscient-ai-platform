from fastapi import APIRouter
router = APIRouter()
@router.get("/sdk")
def sdk():
    return {"sdk": "v1"}
