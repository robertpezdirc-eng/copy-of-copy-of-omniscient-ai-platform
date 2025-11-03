from fastapi import APIRouter
global_router = APIRouter()
@global_router.get("/regions")
def regions():
    return {"regions": ["us"]}
