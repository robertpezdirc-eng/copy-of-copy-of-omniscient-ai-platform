"""
Unit tests for Security Service
"""

import pytest
from backend.services.security_service import SecurityService, TwoFactorMethod, AuditEventType


@pytest.fixture
def security_service():
    return SecurityService()


@pytest.mark.asyncio
async def test_setup_2fa_totp(security_service):
    """Test TOTP 2FA setup"""
    result = await security_service.setup_2fa(
        user_id="user_123",
        method=TwoFactorMethod.TOTP
    )
    
    assert "secret" in result
    assert "qr_code_url" in result
    assert "backup_codes" in result
    assert len(result["backup_codes"]) == 10


@pytest.mark.asyncio
async def test_verify_2fa(security_service):
    """Test 2FA verification"""
    # Setup 2FA first
    await security_service.setup_2fa("user_123", TwoFactorMethod.TOTP)
    
    # Verify with code
    result = await security_service.verify_2fa("user_123", "123456")
    
    assert "success" in result


@pytest.mark.asyncio
async def test_setup_sso_provider(security_service):
    """Test SSO provider setup"""
    provider = await security_service.setup_sso_provider(
        tenant_id="tenant_123",
        provider_name="google",
        provider_type="oauth",
        config={
            "client_id": "test_client_id",
            "client_secret": "test_secret",
            "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token"
        }
    )
    
    assert provider["provider_name"] == "google"
    assert provider["type"] == "oauth"
    assert provider["enabled"] == True


@pytest.mark.asyncio
async def test_audit_logging(security_service):
    """Test audit log creation"""
    await security_service._log_audit_event(
        user_id="user_123",
        event_type=AuditEventType.LOGIN,
        details={"method": "password"}
    )
    
    logs = await security_service.get_audit_logs(user_id="user_123")
    
    assert len(logs) > 0
    assert logs[0]["event_type"] == AuditEventType.LOGIN


@pytest.mark.asyncio
async def test_security_scan(security_service):
    """Test security vulnerability scan"""
    results = await security_service.scan_security_vulnerabilities("tenant_123")
    
    assert "scan_id" in results
    assert "vulnerabilities" in results
    assert "security_score" in results
