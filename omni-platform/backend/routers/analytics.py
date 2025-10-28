from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional, Dict, Any

from utils.ga4 import send_event

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/track")
async def track(event: str, redirect: Optional[str] = None, cid: Optional[str] = None):
    result = await send_event(event_name=event, params={"source": "grafana"}, client_id=cid)
    if redirect:
        return RedirectResponse(url=redirect)
    return JSONResponse(result)


@router.post("/track")
async def track_post(payload: Dict[str, Any]):
    event = payload.get("event")
    if not event:
        raise HTTPException(status_code=400, detail="missing_event")
    params = payload.get("params") or {}
    cid = payload.get("cid")
    return JSONResponse(await send_event(event_name=event, params=params, client_id=cid))