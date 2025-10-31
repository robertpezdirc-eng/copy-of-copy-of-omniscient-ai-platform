from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from payment_gateways import AcmePayGateway

router = APIRouter(prefix="/api/payments", tags=["payments"])


class AuthorizeRequest(BaseModel):
    amount: float
    currency: str
    metadata: Dict[str, Any] = {}


class AuthorizeResponse(BaseModel):
    transaction_id: str
    status: str
    raw: Dict[str, Any] | None = None


class CaptureRequest(BaseModel):
    transaction_id: str
    amount: float


class CaptureResponse(BaseModel):
    transaction_id: str
    status: str
    raw: Dict[str, Any] | None = None


def get_gateway() -> AcmePayGateway:
    """
    Factory dependency that instantiates AcmePayGateway reading PAYMENT_ACME_API_KEY
    from environment. If multiple providers are supported later, choose by config here.
    """
    return AcmePayGateway()


@router.post("/authorize", response_model=AuthorizeResponse)
def authorize(req: AuthorizeRequest, gateway: AcmePayGateway = Depends(get_gateway)):
    try:
        result = gateway.authorize(req.amount, req.currency, req.metadata)
    except Exception:
        # Do not log secrets or token contents.
        raise HTTPException(status_code=502, detail="Payment provider error")
    # Assume provider returns transaction_id and status
    return {
        "transaction_id": result.get("transaction_id", ""),
        "status": result.get("status", "unknown"),
        "raw": result,
    }


@router.post("/capture", response_model=CaptureResponse)
def capture(req: CaptureRequest, gateway: AcmePayGateway = Depends(get_gateway)):
    try:
        result = gateway.capture(req.transaction_id, req.amount)
    except Exception:
        raise HTTPException(status_code=502, detail="Payment provider error")
    return {
        "transaction_id": result.get("transaction_id", req.transaction_id),
        "status": result.get("status", "unknown"),
        "raw": result,
    }
