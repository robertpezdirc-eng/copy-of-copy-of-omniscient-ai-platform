"""
GDPR (General Data Protection Regulation) API Routes

Endpoints expose consent management and data subject rights (DSRs):
- Consent record/withdraw/check
- Right to access, rectification, erasure, portability
- Processing activity and breach recording hooks
"""

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import logging

from services.compliance.gdpr_service import (
    get_gdpr_service,
    ConsentType,
)

router = APIRouter(prefix="/api/v1/gdpr", tags=["GDPR"])
logger = logging.getLogger(__name__)


# Request models
class ConsentRecordRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    consent_type: ConsentType = Field(..., description="Type of consent")
    granted: bool = Field(..., description="Whether consent is granted")
    purpose: str = Field(..., description="Purpose of processing")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ConsentWithdrawRequest(BaseModel):
    user_id: str
    consent_type: ConsentType


class AccessRequest(BaseModel):
    user_id: str
    include_processing_info: bool = True


class ErasureRequest(BaseModel):
    user_id: str
    reason: Optional[str] = None


class RectificationRequest(BaseModel):
    user_id: str
    corrections: Dict[str, Any]


class PortabilityRequest(BaseModel):
    user_id: str
    format: str = Field("json", description="One of: json, csv, xml")


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "gdpr"}


@router.post("/consent")
async def record_consent(payload: ConsentRecordRequest, request: Request, x_user_ip: Optional[str] = Header(None)):
    try:
        gdpr = get_gdpr_service()
        ip = x_user_ip or (request.client.host if request.client else None)
        record = gdpr.record_consent(
            user_id=payload.user_id,
            consent_type=payload.consent_type,
            granted=payload.granted,
            purpose=payload.purpose,
            ip_address=ip,
            metadata=payload.metadata,
        )
        return {"success": True, "record": record}
    except Exception as e:
        logger.error(f"Consent record failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/consent/withdraw")
async def withdraw_consent(payload: ConsentWithdrawRequest):
    try:
        gdpr = get_gdpr_service()
        record = gdpr.withdraw_consent(user_id=payload.user_id, consent_type=payload.consent_type)
        return {"success": True, "record": record}
    except Exception as e:
        logger.error(f"Consent withdraw failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/consent/check")
async def check_consent(user_id: str, consent_type: ConsentType):
    try:
        gdpr = get_gdpr_service()
        granted = gdpr.check_consent(user_id=user_id, consent_type=consent_type)
        return {"user_id": user_id, "consent_type": consent_type, "granted": granted}
    except Exception as e:
        logger.error(f"Consent check failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rights/access")
async def right_to_access(payload: AccessRequest):
    try:
        gdpr = get_gdpr_service()
        response = await gdpr.exercise_right_to_access(
            user_id=payload.user_id,
            include_processing_info=payload.include_processing_info,
        )
        return response
    except Exception as e:
        logger.error(f"Access request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rights/erasure")
async def right_to_erasure(payload: ErasureRequest):
    try:
        gdpr = get_gdpr_service()
        response = await gdpr.exercise_right_to_erasure(user_id=payload.user_id, reason=payload.reason)
        return response
    except Exception as e:
        logger.error(f"Erasure request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rights/rectification")
async def right_to_rectification(payload: RectificationRequest):
    try:
        gdpr = get_gdpr_service()
        response = await gdpr.exercise_right_to_rectification(
            user_id=payload.user_id,
            corrections=payload.corrections,
        )
        return response
    except Exception as e:
        logger.error(f"Rectification request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rights/portability")
async def right_to_portability(payload: PortabilityRequest):
    try:
        gdpr = get_gdpr_service()
        response = await gdpr.exercise_right_to_data_portability(user_id=payload.user_id, format=payload.format)
        return response
    except Exception as e:
        logger.error(f"Portability request failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status")
async def gdpr_status():
    try:
        gdpr = get_gdpr_service()
        return {
            "dpo_email": gdpr.dpo_email,
            "consent_users": len(gdpr.consent_records),
            "processing_activities": len(gdpr.processing_activities),
            "audit_events": len(gdpr.audit_log),
            "retention_days": gdpr.retention_period.days,
        }
    except Exception as e:
        logger.error(f"GDPR status failed: {e}")
        return {"error": str(e)}
