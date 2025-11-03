"""
Tests for Authentication Routes with MFA
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from main import app
from services.mfa_service import MFAService


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_current_user():
    """Mock authenticated user"""
    return {
        "user_id": "test_user_123",
        "email": "test@example.com",
        "role": "user",
        "tenant_id": "test_tenant"
    }


@pytest.fixture
def auth_headers():
    """Mock authorization headers"""
    return {"Authorization": "Bearer mock_token"}


class TestAuthenticationRoutes:
    """Test basic authentication routes"""
    
    def test_login_endpoint(self, client):
        """Test login endpoint"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"


class TestMFATOTPRoutes:
    """Test TOTP MFA routes"""
    
    @patch('routes.auth_routes.get_current_user')
    def test_setup_totp_mfa(self, mock_get_user, client, mock_current_user):
        """Test TOTP MFA setup endpoint"""
        mock_get_user.return_value = mock_current_user
        
        response = client.post(
            "/api/v1/auth/mfa/totp/setup",
            headers={"Authorization": "Bearer mock_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "secret" in data
        assert "qr_code_uri" in data
        assert "backup_codes" in data
        assert len(data["backup_codes"]) == 10
        assert data["qr_code_uri"].startswith("otpauth://totp/")
    
    @patch('routes.auth_routes.get_current_user')
    @patch('routes.auth_routes.mfa_service')
    def test_verify_totp_code_valid(self, mock_mfa, mock_get_user, client, mock_current_user):
        """Test TOTP code verification with valid code"""
        mock_get_user.return_value = mock_current_user
        mock_mfa.verify_totp_code.return_value = True
        
        response = client.post(
            "/api/v1/auth/mfa/totp/verify",
            headers={"Authorization": "Bearer mock_token"},
            json={
                "secret": "JBSWY3DPEHPK3PXP",
                "code": "123456"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "TOTP MFA enabled" in data["message"]
    
    @patch('routes.auth_routes.get_current_user')
    @patch('routes.auth_routes.mfa_service')
    def test_verify_totp_code_invalid(self, mock_mfa, mock_get_user, client, mock_current_user):
        """Test TOTP code verification with invalid code"""
        mock_get_user.return_value = mock_current_user
        mock_mfa.verify_totp_code.return_value = False
        
        response = client.post(
            "/api/v1/auth/mfa/totp/verify",
            headers={"Authorization": "Bearer mock_token"},
            json={
                "secret": "JBSWY3DPEHPK3PXP",
                "code": "000000"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid verification code" in data["detail"]


class TestMFASMSRoutes:
    """Test SMS MFA routes"""
    
    @patch('routes.auth_routes.get_current_user')
    @patch('routes.auth_routes.mfa_service')
    def test_setup_sms_mfa_success(self, mock_mfa, mock_get_user, client, mock_current_user):
        """Test SMS MFA setup with successful send"""
        mock_get_user.return_value = mock_current_user
        mock_mfa.generate_sms_otp.return_value = "123456"
        mock_mfa.send_sms_otp.return_value = True
        mock_mfa.otp_expiry_minutes = 5
        
        response = client.post(
            "/api/v1/auth/mfa/sms/setup",
            headers={"Authorization": "Bearer mock_token"},
            json={"phone_number": "+1234567890"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Verification code sent" in data["message"]
        assert data["expires_in_minutes"] == 5
    
    @patch('routes.auth_routes.get_current_user')
    @patch('routes.auth_routes.mfa_service')
    def test_setup_sms_mfa_failure(self, mock_mfa, mock_get_user, client, mock_current_user):
        """Test SMS MFA setup with failed send"""
        mock_get_user.return_value = mock_current_user
        mock_mfa.generate_sms_otp.return_value = "123456"
        mock_mfa.send_sms_otp.return_value = False
        
        response = client.post(
            "/api/v1/auth/mfa/sms/setup",
            headers={"Authorization": "Bearer mock_token"},
            json={"phone_number": "+1234567890"}
        )
        
        assert response.status_code == 503
        data = response.json()
        assert "Failed to send SMS" in data["detail"]
    
    @patch('routes.auth_routes.get_current_user')
    def test_verify_sms_code_valid(self, mock_get_user, client, mock_current_user):
        """Test SMS code verification with valid code"""
        mock_get_user.return_value = mock_current_user
        
        response = client.post(
            "/api/v1/auth/mfa/sms/verify",
            headers={"Authorization": "Bearer mock_token"},
            json={
                "phone_number": "+1234567890",
                "code": "123456"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "SMS MFA enabled" in data["message"]
    
    @patch('routes.auth_routes.get_current_user')
    def test_verify_sms_code_invalid(self, mock_get_user, client, mock_current_user):
        """Test SMS code verification with invalid code"""
        mock_get_user.return_value = mock_current_user
        
        response = client.post(
            "/api/v1/auth/mfa/sms/verify",
            headers={"Authorization": "Bearer mock_token"},
            json={
                "phone_number": "+1234567890",
                "code": "abc"  # Invalid format
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid or expired" in data["detail"]


class TestMFAEmailRoutes:
    """Test Email MFA routes"""
    
    @patch('routes.auth_routes.get_current_user')
    @patch('routes.auth_routes.mfa_service')
    def test_setup_email_mfa_success(self, mock_mfa, mock_get_user, client, mock_current_user):
        """Test Email MFA setup with successful send"""
        mock_get_user.return_value = mock_current_user
        mock_mfa.generate_email_otp.return_value = "123456"
        mock_mfa.send_email_otp.return_value = True
        mock_mfa.otp_expiry_minutes = 5
        
        response = client.post(
            "/api/v1/auth/mfa/email/setup",
            headers={"Authorization": "Bearer mock_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Verification code sent" in data["message"]
        assert data["expires_in_minutes"] == 5
    
    @patch('routes.auth_routes.get_current_user')
    @patch('routes.auth_routes.mfa_service')
    def test_setup_email_mfa_failure(self, mock_mfa, mock_get_user, client, mock_current_user):
        """Test Email MFA setup with failed send"""
        mock_get_user.return_value = mock_current_user
        mock_mfa.generate_email_otp.return_value = "123456"
        mock_mfa.send_email_otp.return_value = False
        
        response = client.post(
            "/api/v1/auth/mfa/email/setup",
            headers={"Authorization": "Bearer mock_token"}
        )
        
        assert response.status_code == 503
        data = response.json()
        assert "Failed to send email" in data["detail"]
    
    @patch('routes.auth_routes.get_current_user')
    def test_verify_email_code_valid(self, mock_get_user, client, mock_current_user):
        """Test Email code verification with valid code"""
        mock_get_user.return_value = mock_current_user
        
        response = client.post(
            "/api/v1/auth/mfa/email/verify",
            headers={"Authorization": "Bearer mock_token"},
            json={"code": "123456"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Email MFA enabled" in data["message"]


class TestBackupCodesRoutes:
    """Test Backup Codes routes"""
    
    @patch('routes.auth_routes.get_current_user')
    def test_generate_backup_codes(self, mock_get_user, client, mock_current_user):
        """Test backup codes generation"""
        mock_get_user.return_value = mock_current_user
        
        response = client.post(
            "/api/v1/auth/mfa/backup-codes/generate",
            headers={"Authorization": "Bearer mock_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "codes" in data
        assert len(data["codes"]) == 10
        assert "Save these codes" in data["message"]
        
        # Verify all codes are 8 characters
        for code in data["codes"]:
            assert len(code) == 8
    
    @patch('routes.auth_routes.get_current_user')
    def test_verify_backup_code_valid(self, mock_get_user, client, mock_current_user):
        """Test backup code verification with valid code"""
        mock_get_user.return_value = mock_current_user
        
        response = client.post(
            "/api/v1/auth/mfa/backup-codes/verify",
            headers={"Authorization": "Bearer mock_token"},
            json={"code": "abc12345"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Backup code verified" in data["message"]
        assert "remaining_codes" in data
    
    @patch('routes.auth_routes.get_current_user')
    def test_verify_backup_code_invalid(self, mock_get_user, client, mock_current_user):
        """Test backup code verification with invalid code"""
        mock_get_user.return_value = mock_current_user
        
        response = client.post(
            "/api/v1/auth/mfa/backup-codes/verify",
            headers={"Authorization": "Bearer mock_token"},
            json={"code": "abc"}  # Too short
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid backup code" in data["detail"]


class TestMFAManagementRoutes:
    """Test MFA management routes"""
    
    @patch('routes.auth_routes.get_current_user')
    def test_get_mfa_status(self, mock_get_user, client, mock_current_user):
        """Test MFA status endpoint"""
        mock_get_user.return_value = mock_current_user
        
        response = client.get(
            "/api/v1/auth/mfa/status",
            headers={"Authorization": "Bearer mock_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "mfa_enabled" in data
        assert "methods" in data
        assert "totp" in data["methods"]
        assert "sms" in data["methods"]
        assert "email" in data["methods"]
        assert "backup_codes_count" in data
    
    @patch('routes.auth_routes.get_current_user')
    def test_disable_mfa_all_methods(self, mock_get_user, client, mock_current_user):
        """Test disabling all MFA methods"""
        mock_get_user.return_value = mock_current_user
        
        response = client.post(
            "/api/v1/auth/mfa/disable",
            headers={"Authorization": "Bearer mock_token"},
            json={"password": "testpassword123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "All MFA methods disabled" in data["message"]
    
    @patch('routes.auth_routes.get_current_user')
    def test_disable_mfa_specific_method(self, mock_get_user, client, mock_current_user):
        """Test disabling specific MFA method"""
        mock_get_user.return_value = mock_current_user
        
        response = client.post(
            "/api/v1/auth/mfa/disable",
            headers={"Authorization": "Bearer mock_token"},
            json={
                "password": "testpassword123",
                "method": "totp"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "TOTP MFA disabled" in data["message"]
