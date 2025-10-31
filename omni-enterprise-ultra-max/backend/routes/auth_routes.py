from fastapi import APIRouter
from pydantic import BaseModel, EmailStr
router = APIRouter()
class UserLogin(BaseModel):
    email: EmailStr
    password: str
@router.post("/login")
def login(u: UserLogin):
    return {"token": "mock"}
@router.get("/me")
def me():
    return {"user": "test"}
