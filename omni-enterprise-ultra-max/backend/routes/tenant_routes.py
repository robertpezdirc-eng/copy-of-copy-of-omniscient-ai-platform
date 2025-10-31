from fastapi import APIRouter
from pydantic import BaseModel
router = APIRouter()
@router.get("/{tid}")
def get(tid: str):
    return {"id": tid}
