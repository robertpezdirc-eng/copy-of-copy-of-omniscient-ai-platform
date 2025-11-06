"""
Advanced Security API Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from services.security_service import SecurityService, TwoFactorMethod, AuditEventType

router = APIRouter(prefix="/api/v1/security", tags=["Advanced Security"])
security_service = SecurityService()


class Setup2FARequest(BaseModel):
    user_id: str
    method: TwoFactorMethod = TwoFactorMethod.TOTP


class Verify2FARequest(BaseModel):
    user_id: str
    code: str


class SetupSSORequest(BaseModel):
    tenant_id: str
    provider_name: str
    provider_type: str
    config: dict


class InitiateSSORequest(BaseModel):
    state: str


@router.post("/2fa/setup")
async def setup_2fa(request: Setup2FARequest):
    """Setup two-factor authentication"""
    try:
        result = await security_service.setup_2fa(
            user_id=request.user_id,
            method=request.method
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/2fa/verify")
async def verify_2fa(request: Verify2FARequest):
    """Verify 2FA code and enable 2FA"""
    try:
        result = await security_service.verify_2fa(
            user_id=request.user_id,
            code=request.code
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/2fa/validate")
async def validate_2fa_code(request: Verify2FARequest):
    """Validate 2FA code during login"""
    try:
        is_valid = await security_service.validate_2fa_code(
            user_id=request.user_id,
            code=request.code
        )
        return {"valid": is_valid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sso/setup")
async def setup_sso_provider(request: SetupSSORequest):
    """Setup SSO provider for tenant"""
    try:
        provider = await security_service.setup_sso_provider(
            tenant_id=request.tenant_id,
            provider_name=request.provider_name,
            provider_type=request.provider_type,
            config=request.config
        )
        return provider
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sso/{provider_id}/initiate")
async def initiate_sso_login(provider_id: str, request: InitiateSSORequest):
    """Initiate SSO login flow"""
    try:
        result = await security_service.initiate_sso_login(
            provider_id=provider_id,
            state=request.state
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sso/{provider_id}/callback")
async def complete_sso_login(provider_id: str, code: str):
    """Complete SSO login"""
    try:
        result = await security_service.complete_sso_login(
            provider_id=provider_id,
            code_or_response=code
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-logs")
async def get_audit_logs(
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    event_type: Optional[AuditEventType] = None,
    limit: int = 100
):
    """Get audit logs with filters"""
    try:
        logs = await security_service.get_audit_logs(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            limit=limit
        )
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audit-logs/export")
async def export_audit_logs(
    tenant_id: str,
    start_date: datetime,
    end_date: datetime,
    format: str = "json"
):
    """Export audit logs for compliance"""
    try:
        export = await security_service.export_audit_logs(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            format=format
        )
        return export
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{tenant_id}/scan")
async def scan_security_vulnerabilities(tenant_id: str):
    """Scan for security vulnerabilities"""
    try:
        results = await security_service.scan_security_vulnerabilities(tenant_id)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/{tenant_id}")
async def get_security_dashboard(tenant_id: str):
    """Get security dashboard overview"""
    try:
        dashboard = await security_service.get_security_dashboard(tenant_id)
        return dashboard
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
