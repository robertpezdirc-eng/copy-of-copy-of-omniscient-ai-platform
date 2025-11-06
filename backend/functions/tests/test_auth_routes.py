"""
Tests for Authentication Routes with MFA
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime


class TestMFATOTPRoutes:
    """Test TOTP MFA routes"""
    
    @pytest.mark.asyncio
    @patch('routes.auth_routes.get_current_user')
    @patch('routes.auth_routes.mfa_service')
    async def test_setup_totp_mfa(self, mock_mfa, mock_get_user):
        """Test TOTP MFA setup endpoint logic"""
        from routes.auth_routes import setup_totp_mfa
        
        mock_current_user = {
            "user_id": "test_user_123",
            "email": "test@example.com",
            "role": "user",
            "tenant_id": "test_tenant"
        }
        mock_get_user.return_value = mock_current_user
        
        # Mock MFA service methods
        mock_mfa.generate_totp_secret.return_value = "TESTSECRET123456"
        mock_mfa.get_totp_uri.return_value = "otpauth://totp/test"
        mock_mfa.generate_backup_codes.return_value = ["code1", "code2", "code3"]
        
        result = await setup_totp_mfa(current_user=mock_current_user)
        
        assert "secret" in result
        assert "qr_code_uri" in result
        assert "backup_codes" in result
        assert len(result["backup_codes"]) == 3
    
    @pytest.mark.asyncio
    @patch('routes.auth_routes.mfa_service')
    async def test_verify_totp_code_valid(self, mock_mfa):
        """Test TOTP code verification with valid code"""
        from routes.auth_routes import verify_totp_code, MFATOTPVerifyRequest
        
        mock_current_user = {
            "user_id": "test_user_123",
            "email": "test@example.com"
        }
        
        mock_mfa.verify_totp_code.return_value = True
        
        request = MFATOTPVerifyRequest(secret="TESTSECRET", code="123456")
        result = await verify_totp_code(request, current_user=mock_current_user)
        
        assert result["success"] is True
        assert "TOTP MFA enabled" in result["message"]
    
    @pytest.mark.asyncio
    @patch('routes.auth_routes.mfa_service')
    async def test_verify_totp_code_invalid(self, mock_mfa):
        """Test TOTP code verification with invalid code"""
        from routes.auth_routes import verify_totp_code, MFATOTPVerifyRequest
        from fastapi import HTTPException
        
        mock_current_user = {
            "user_id": "test_user_123",
            "email": "test@example.com"
        }
        
        mock_mfa.verify_totp_code.return_value = False
        
        request = MFATOTPVerifyRequest(secret="TESTSECRET", code="000000")
        
        with pytest.raises(HTTPException) as exc_info:
            await verify_totp_code(request, current_user=mock_current_user)
        
        assert exc_info.value.status_code == 400
        assert "Invalid verification code" in exc_info.value.detail


class TestMFASMSRoutes:
    """Test SMS MFA routes"""
    
    @pytest.mark.asyncio
    @patch('routes.auth_routes.mfa_service')
    async def test_setup_sms_mfa_success(self, mock_mfa):
        """Test SMS MFA setup with successful send"""
        from routes.auth_routes import setup_sms_mfa, MFASMSSetupRequest
        
        mock_current_user = {
            "user_id": "test_user_123",
            "email": "test@example.com"
        }
        
        mock_mfa.generate_sms_otp.return_value = "123456"
        mock_mfa.send_sms_otp.return_value = True
        mock_mfa.otp_expiry_minutes = 5
        
        request = MFASMSSetupRequest(phone_number="+1234567890")
        result = await setup_sms_mfa(request, current_user=mock_current_user)
        
        assert result["success"] is True
        assert "Verification code sent" in result["message"]
        assert result["expires_in_minutes"] == 5
    
    @pytest.mark.asyncio
    @patch('routes.auth_routes.mfa_service')
    async def test_setup_sms_mfa_failure(self, mock_mfa):
        """Test SMS MFA setup with failed send"""
        from routes.auth_routes import setup_sms_mfa, MFASMSSetupRequest
        from fastapi import HTTPException
        
        mock_current_user = {
            "user_id": "test_user_123",
            "email": "test@example.com"
        }
        
        mock_mfa.generate_sms_otp.return_value = "123456"
        mock_mfa.send_sms_otp.return_value = False
        
        request = MFASMSSetupRequest(phone_number="+1234567890")
        
        with pytest.raises(HTTPException) as exc_info:
            await setup_sms_mfa(request, current_user=mock_current_user)
        
        assert exc_info.value.status_code == 503
        assert "Failed to send SMS" in exc_info.value.detail


class TestMFAEmailRoutes:
    """Test Email MFA routes"""
    
    @pytest.mark.asyncio
    @patch('routes.auth_routes.mfa_service')
    async def test_setup_email_mfa_success(self, mock_mfa):
        """Test Email MFA setup with successful send"""
        from routes.auth_routes import setup_email_mfa
        
        mock_current_user = {
            "user_id": "test_user_123",
            "email": "test@example.com"
        }
        
        mock_mfa.generate_email_otp.return_value = "123456"
        mock_mfa.send_email_otp.return_value = True
        mock_mfa.otp_expiry_minutes = 5
        
        result = await setup_email_mfa(current_user=mock_current_user)
        
        assert result["success"] is True
        assert "Verification code sent" in result["message"]
        assert result["expires_in_minutes"] == 5
    
    @pytest.mark.asyncio
    @patch('routes.auth_routes.mfa_service')
    async def test_setup_email_mfa_failure(self, mock_mfa):
        """Test Email MFA setup with failed send"""
        from routes.auth_routes import setup_email_mfa
        from fastapi import HTTPException
        
        mock_current_user = {
            "user_id": "test_user_123",
            "email": "test@example.com"
        }
        
        mock_mfa.generate_email_otp.return_value = "123456"
        mock_mfa.send_email_otp.return_value = False
        
        with pytest.raises(HTTPException) as exc_info:
            await setup_email_mfa(current_user=mock_current_user)
        
        assert exc_info.value.status_code == 503
        assert "Failed to send email" in exc_info.value.detail


class TestBackupCodesRoutes:
    """Test Backup Codes routes"""
    
    @pytest.mark.asyncio
    @patch('routes.auth_routes.mfa_service')
    async def test_generate_backup_codes(self, mock_mfa):
        """Test backup codes generation"""
        from routes.auth_routes import generate_backup_codes
        
        mock_current_user = {
            "user_id": "test_user_123",
            "email": "test@example.com"
        }
        
        mock_mfa.generate_backup_codes.return_value = ["code1", "code2", "code3"]
        
        result = await generate_backup_codes(current_user=mock_current_user)
        
        assert "codes" in result
        assert len(result["codes"]) == 3
        assert "Save these codes" in result["message"]


class TestMFAManagementRoutes:
    """Test MFA management routes"""
    
    @pytest.mark.asyncio
    async def test_get_mfa_status(self):
        """Test MFA status endpoint"""
        from routes.auth_routes import get_mfa_status
        
        mock_current_user = {
            "user_id": "test_user_123",
            "email": "test@example.com"
        }
        
        result = await get_mfa_status(current_user=mock_current_user)
        
        assert "mfa_enabled" in result
        assert "methods" in result
        assert "totp" in result["methods"]
        assert "sms" in result["methods"]
        assert "email" in result["methods"]
    
    @pytest.mark.asyncio
    async def test_disable_mfa_all_methods(self):
        """Test disabling all MFA methods"""
        from routes.auth_routes import disable_mfa, MFADisableRequest
        
        mock_current_user = {
            "user_id": "test_user_123",
            "email": "test@example.com"
        }
        
        request = MFADisableRequest(password="testpassword123")
        result = await disable_mfa(request, current_user=mock_current_user)
        
        assert result["success"] is True
        assert "All MFA methods disabled" in result["message"]
    
    @pytest.mark.asyncio
    async def test_disable_mfa_specific_method(self):
        """Test disabling specific MFA method"""
        from routes.auth_routes import disable_mfa, MFADisableRequest
        
        mock_current_user = {
            "user_id": "test_user_123",
            "email": "test@example.com"
        }
        
        request = MFADisableRequest(password="testpassword123", method="totp")
        result = await disable_mfa(request, current_user=mock_current_user)
        
        assert result["success"] is True
        assert "TOTP MFA disabled" in result["message"]
