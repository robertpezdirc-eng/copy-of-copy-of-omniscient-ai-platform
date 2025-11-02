from __future__ import annotations
  """
  The code defines API endpoints for handling GDPR consent, data export, data erasure, and
  encryption/decryption operations.
  :return: The code provided defines several API endpoints related to security and GDPR operations
  using FastAPI. Here is a summary of what is being returned by each endpoint:
  """
  """
  The code defines API endpoints for handling GDPR consent, data export, data erasure, and
  encryption/decryption operations.
  :return: The code provided defines several API endpoints related to security and GDPR operations
  using FastAPI. Here is a summary of what is being returned by each endpoint:
  """

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.security import get_encryption_service, get_gdpr_service

try:
    from prometheus_client import Counter  # type: ignore

    gdpr_consent_total = Counter("gdpr_consent_total", "Total GDPR consent operations", ["operation"])
    gdpr_export_total = Counter("gdpr_export_total", "Total GDPR export operations")
    gdpr_erase_total = Counter("gdpr_erase_total", "Total GDPR erase operations")
except Exception:  # pragma: no cover - optional dependency
    gdpr_consent_total = gdpr_export_total = gdpr_erase_total = None  # type: ignore

security_router = APIRouter()


class ConsentPayload(BaseModel):
    user_id: str
    consent: Dict[str, Any] = Field(default_factory=dict)


class ExportPayload(BaseModel):
    user_id: str


class ErasePayload(BaseModel):
    user_id: str


class EncryptPayload(BaseModel):
    plaintext: str
    aad: Optional[str] = None


class DecryptPayload(BaseModel):
    token: str
    aad: Optional[str] = None


@security_router.get("/status")
def status():
    return {"ok": True}


@security_router.post("/consent")
async def record_consent(payload: ConsentPayload) -> Dict[str, Any]:
    gdpr = get_gdpr_service()
    result = await gdpr.record_consent(payload.user_id, payload.consent)
    if gdpr_consent_total:
        gdpr_consent_total.labels(operation="record").inc()
    return result


@security_router.get("/consent/{user_id}")
async def get_consent(user_id: str) -> Dict[str, Any]:
    gdpr = get_gdpr_service()
    result = await gdpr.get_consent(user_id)
    if gdpr_consent_total:
        gdpr_consent_total.labels(operation="get").inc()
    return result


@security_router.post("/gdpr/export")
async def gdpr_export(payload: ExportPayload) -> Dict[str, Any]:
    gdpr = get_gdpr_service()
    result = await gdpr.export_user_data(payload.user_id)
    if gdpr_export_total:
        gdpr_export_total.inc()
    return result


@security_router.post("/gdpr/erase")
async def gdpr_erase(payload: ErasePayload) -> Dict[str, Any]:
    gdpr = get_gdpr_service()
    result = await gdpr.erase_user_data(payload.user_id)
    if gdpr_erase_total:
        gdpr_erase_total.inc()
    return result


@security_router.post("/crypto/encrypt")
def crypto_encrypt(payload: EncryptPayload) -> Dict[str, Any]:
    svc = get_encryption_service()
    aad = payload.aad.encode("utf-8") if payload.aad else None
    token = svc.encrypt(payload.plaintext, associated_data=aad)
    return {"token": token}


@security_router.post("/crypto/decrypt")
def crypto_decrypt(payload: DecryptPayload) -> Dict[str, Any]:
    svc = get_encryption_service()
    aad = payload.aad.encode("utf-8") if payload.aad else None
    try:
        data = svc.decrypt(payload.token, associated_data=aad)
        return {"plaintext": data.decode("utf-8")}
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Decryption failed") from exc
