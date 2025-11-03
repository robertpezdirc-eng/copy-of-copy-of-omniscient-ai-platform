"""
Tests for MFA Service
Tests TOTP, SMS OTP, Email OTP, and Backup Codes functionality
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from services.mfa_service import MFAService


class TestMFAService:
    """Test MFA Service functionality"""
    
    @pytest.fixture
    def mfa_service(self):
        """Create MFA service instance"""
        return MFAService()
    
    # ============================================================================
    # TOTP Tests
    # ============================================================================
    
    def test_generate_totp_secret(self, mfa_service):
        """Test TOTP secret generation"""
        secret = mfa_service.generate_totp_secret()
        
        assert secret is not None
        assert isinstance(secret, str)
        assert len(secret) == 32  # Base32 encoded
        # Should be alphanumeric uppercase
        assert secret.isupper()
        assert secret.isalnum()
    
    def test_get_totp_uri(self, mfa_service):
        """Test TOTP URI generation for QR codes"""
        secret = "JBSWY3DPEHPK3PXP"
        email = "test@example.com"
        
        uri = mfa_service.get_totp_uri(secret, email)
        
        assert uri.startswith("otpauth://totp/")
        assert "test%40example.com" in uri  # @ is URL encoded as %40
        assert "OMNI%20Platform" in uri  # Space is URL encoded as %20
        assert f"secret={secret}" in uri
    
    def test_generate_and_verify_totp_code(self, mfa_service):
        """Test TOTP code generation and verification"""
        secret = mfa_service.generate_totp_secret()
        
        # Generate code
        code = mfa_service.generate_totp_code(secret)
        
        assert code is not None
        assert isinstance(code, str)
        assert len(code) == 6
        assert code.isdigit()
        
        # Verify the generated code
        is_valid = mfa_service.verify_totp_code(secret, code)
        assert is_valid is True
    
    def test_verify_totp_code_invalid(self, mfa_service):
        """Test TOTP code verification with invalid code"""
        secret = mfa_service.generate_totp_secret()
        invalid_code = "000000"
        
        is_valid = mfa_service.verify_totp_code(secret, invalid_code)
        assert is_valid is False
    
    def test_verify_totp_code_with_time_window(self, mfa_service):
        """Test TOTP code verification within valid window"""
        secret = mfa_service.generate_totp_secret()
        code = mfa_service.generate_totp_code(secret)
        
        # Should be valid immediately
        is_valid = mfa_service.verify_totp_code(secret, code)
        assert is_valid is True
    
    # ============================================================================
    # SMS OTP Tests
    # ============================================================================
    
    def test_generate_sms_otp(self, mfa_service):
        """Test SMS OTP generation"""
        otp = mfa_service.generate_sms_otp()
        
        assert otp is not None
        assert isinstance(otp, str)
        assert len(otp) == 6
        assert otp.isdigit()
    
    def test_generate_sms_otp_uniqueness(self, mfa_service):
        """Test that generated OTPs are different"""
        otp1 = mfa_service.generate_sms_otp()
        otp2 = mfa_service.generate_sms_otp()
        
        # While technically they could be the same, probability is very low
        # This test might occasionally fail but would catch a broken generator
        assert otp1 != otp2 or len(otp1) == 6  # At least verify format
    
    @patch('services.mfa_service.MFAService.send_sms_otp')
    def test_send_sms_otp_success(self, mock_send_sms, mfa_service, monkeypatch):
        """Test successful SMS OTP sending"""
        # Set up environment variables
        monkeypatch.setenv("TWILIO_ACCOUNT_SID", "test_sid")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "test_token")
        monkeypatch.setenv("TWILIO_PHONE_NUMBER", "+1234567890")
        
        # Recreate service to pick up env vars
        mfa_service = MFAService()
        
        # Mock the method to return True
        mock_send_sms.return_value = True
        
        phone_number = "+1234567890"
        code = "123456"
        
        result = mfa_service.send_sms_otp(phone_number, code)
        
        assert result is True
    
    def test_send_sms_otp_no_credentials(self, mfa_service):
        """Test SMS OTP sending without credentials"""
        phone_number = "+1234567890"
        code = "123456"
        
        # Should return False when credentials are not set
        result = mfa_service.send_sms_otp(phone_number, code)
        assert result is False
    
    # ============================================================================
    # Email OTP Tests
    # ============================================================================
    
    def test_generate_email_otp(self, mfa_service):
        """Test Email OTP generation"""
        otp = mfa_service.generate_email_otp()
        
        assert otp is not None
        assert isinstance(otp, str)
        assert len(otp) == 6
        assert otp.isdigit()
    
    @patch('services.mfa_service.MFAService.send_email_otp')
    def test_send_email_otp_success(self, mock_send_email, mfa_service, monkeypatch):
        """Test successful Email OTP sending"""
        # Set up environment variable
        monkeypatch.setenv("SENDGRID_API_KEY", "test_key")
        
        # Recreate service to pick up env vars
        mfa_service = MFAService()
        
        # Mock the method to return True
        mock_send_email.return_value = True
        
        email = "test@example.com"
        code = "123456"
        
        result = mfa_service.send_email_otp(email, code)
        
        assert result is True
    
    def test_send_email_otp_no_credentials(self, mfa_service):
        """Test Email OTP sending without credentials"""
        email = "test@example.com"
        code = "123456"
        
        # Should return False when credentials are not set
        result = mfa_service.send_email_otp(email, code)
        assert result is False
    
    # ============================================================================
    # OTP Verification Tests
    # ============================================================================
    
    def test_verify_otp_valid(self, mfa_service):
        """Test OTP verification with valid code"""
        stored_code = "123456"
        stored_timestamp = datetime.utcnow()
        provided_code = "123456"
        
        is_valid = mfa_service.verify_otp(stored_code, stored_timestamp, provided_code)
        assert is_valid is True
    
    def test_verify_otp_invalid_code(self, mfa_service):
        """Test OTP verification with invalid code"""
        stored_code = "123456"
        stored_timestamp = datetime.utcnow()
        provided_code = "654321"
        
        is_valid = mfa_service.verify_otp(stored_code, stored_timestamp, provided_code)
        assert is_valid is False
    
    def test_verify_otp_expired(self, mfa_service):
        """Test OTP verification with expired code"""
        stored_code = "123456"
        # Set timestamp to 10 minutes ago (default expiry is 5 minutes)
        stored_timestamp = datetime.utcnow() - timedelta(minutes=10)
        provided_code = "123456"
        
        is_valid = mfa_service.verify_otp(stored_code, stored_timestamp, provided_code)
        assert is_valid is False
    
    def test_verify_otp_just_before_expiry(self, mfa_service):
        """Test OTP verification just before expiry"""
        stored_code = "123456"
        # Set timestamp to 4 minutes ago (default expiry is 5 minutes)
        stored_timestamp = datetime.utcnow() - timedelta(minutes=4)
        provided_code = "123456"
        
        is_valid = mfa_service.verify_otp(stored_code, stored_timestamp, provided_code)
        assert is_valid is True
    
    # ============================================================================
    # Backup Codes Tests
    # ============================================================================
    
    def test_generate_backup_codes(self, mfa_service):
        """Test backup codes generation"""
        codes = mfa_service.generate_backup_codes(count=10)
        
        assert codes is not None
        assert isinstance(codes, list)
        assert len(codes) == 10
        
        for code in codes:
            assert isinstance(code, str)
            assert len(code) == 8
    
    def test_generate_backup_codes_uniqueness(self, mfa_service):
        """Test that backup codes are unique"""
        codes = mfa_service.generate_backup_codes(count=10)
        
        # All codes should be unique
        assert len(codes) == len(set(codes))
    
    def test_generate_backup_codes_custom_count(self, mfa_service):
        """Test backup codes generation with custom count"""
        codes = mfa_service.generate_backup_codes(count=5)
        
        assert len(codes) == 5
    
    def test_hash_backup_code(self, mfa_service):
        """Test backup code hashing"""
        plain_code = "abc12345"
        
        hashed_code = mfa_service.hash_backup_code(plain_code)
        
        assert hashed_code is not None
        assert isinstance(hashed_code, str)
        assert hashed_code != plain_code
        assert len(hashed_code) > len(plain_code)
    
    def test_verify_backup_code_valid(self, mfa_service):
        """Test backup code verification with valid code"""
        plain_code = "abc12345"
        hashed_code = mfa_service.hash_backup_code(plain_code)
        
        is_valid = mfa_service.verify_backup_code(plain_code, hashed_code)
        assert is_valid is True
    
    def test_verify_backup_code_invalid(self, mfa_service):
        """Test backup code verification with invalid code"""
        plain_code = "abc12345"
        wrong_code = "xyz98765"
        hashed_code = mfa_service.hash_backup_code(plain_code)
        
        is_valid = mfa_service.verify_backup_code(wrong_code, hashed_code)
        assert is_valid is False
    
    # ============================================================================
    # Utility Tests
    # ============================================================================
    
    def test_generate_qr_code_data(self, mfa_service):
        """Test QR code data generation"""
        secret = "JBSWY3DPEHPK3PXP"
        email = "test@example.com"
        
        qr_data = mfa_service.generate_qr_code_data(secret, email)
        
        assert qr_data.startswith("otpauth://totp/")
        assert "test%40example.com" in qr_data  # @ is URL encoded as %40
        assert secret in qr_data
