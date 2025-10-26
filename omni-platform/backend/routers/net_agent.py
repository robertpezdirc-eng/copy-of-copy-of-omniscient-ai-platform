from fastapi import APIRouter, Depends
from pydantic import BaseModel, ValidationError
from typing import Optional, Dict, Any, List, Union
from adapters.net_agent_adapter import NetAgentAdapter
from .access_controller import require_api_key

router = APIRouter(prefix="/api/v1/net-agent", tags=["net-agent"])

class FetchRequest(BaseModel):
    url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    body: Optional[Any] = None

class ExternalJSON(BaseModel):
    data: Union[Dict[str, Any], List[Any]]
    status_code: int
    headers: Dict[str, Any]
    url: str
    method: str
    latency_ms: int

class ExternalText(BaseModel):
    text: str
    status_code: int
    headers: Dict[str, Any]
    url: str
    method: str
    latency_ms: int

@router.post("/fetch")
async def fetch(req: FetchRequest, auth: Dict[str, Any] = Depends(require_api_key)):
    adapter = NetAgentAdapter()
    result = await adapter.fetch(req.url, method=req.method, headers=req.headers or {}, body=req.body)
    # Validate data via Pydantic
    validated: Dict[str, Any]
    try:
        if (result.get("content_type") or "").startswith("application/json") and result.get("ok"):
            model = ExternalJSON(
                data=result.get("data"),
                status_code=result.get("status_code"),
                headers=result.get("headers"),
                url=result.get("url"),
                method=result.get("method"),
                latency_ms=result.get("latency_ms", 0),
            )
            validated = {"json": model.dict(), "safe": result.get("safe", False)}
        else:
            text_model = ExternalText(
                text=str(result.get("data")),
                status_code=result.get("status_code", 0),
                headers=result.get("headers") or {},
                url=str(result.get("url")),
                method=str(result.get("method")),
                latency_ms=int(result.get("latency_ms", 0)),
            )
            validated = {"text": text_model.dict(), "safe": result.get("safe", False)}
    except ValidationError as e:
        return {"ok": False, "error": "validation_error", "detail": e.errors(), "raw": result}
    return {"ok": bool(result.get("ok")), "data": validated, "status_code": result.get("status_code"), "latency_ms": result.get("latency_ms"), "safe": result.get("safe")}

@router.get("/health")
async def net_health():
    return {"status": "OK", "agent": "net-agent"}
