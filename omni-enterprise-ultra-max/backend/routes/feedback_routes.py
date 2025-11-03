from fastapi import APIRouter
router = APIRouter()
@router.post("/submit")
def submit():
    return {"ok": True}
