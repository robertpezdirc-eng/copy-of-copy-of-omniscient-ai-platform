"""
Authentication Routes - Login, Registration, MFA
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
import logging

from services.auth import AuthService, get_current_user
from services.mfa_service import MFAService
from models.user import (
    UserCreate, LoginRequest, User, Token,
    MFASetupRequest, MFAVerifyRequest,
    PasswordResetRequest, PasswordResetConfirm,
    ChangePasswordRequest
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
auth_service = AuthService()
mfa_service = MFAService()


# ============================================================================
# Basic Authentication Endpoints
# ============================================================================

@router.post("/login", response_model=Token)
async def login(credentials: LoginRequest):
    """
    Login with email and password
    Returns access token if credentials are valid
    """
    # This is a mock implementation - in production, verify against database
    return {
        "access_token": "mock_access_token",
        "refresh_token": "mock_refresh_token",
        "token_type": "bearer",
        "expires_in": 1800
    }


@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    return {
        "user_id": current_user.get("user_id"),
        "email": current_user.get("email"),
        "role": current_user.get("role"),
        "tenant_id": current_user.get("tenant_id")
    }


# ============================================================================
# MFA TOTP (Authenticator App) Endpoints
# ============================================================================

class MFATOTPSetupResponse(BaseModel):
    """Response for TOTP setup"""
    secret: str
    qr_code_uri: str
    backup_codes: List[str]


@router.post("/mfa/totp/setup", response_model=MFATOTPSetupResponse)
async def setup_totp_mfa(current_user: dict = Depends(get_current_user)):
    """
    Initialize TOTP (authenticator app) MFA setup
    Returns secret key and QR code URI for scanning
    """
    try:
        # Generate TOTP secret
        secret = mfa_service.generate_totp_secret()
        
        # Generate QR code URI
        email = current_user.get("email", "user@example.com")
        qr_uri = mfa_service.get_totp_uri(secret, email)
        
        # Generate backup codes
        backup_codes = mfa_service.generate_backup_codes(count=10)
        
        logger.info(f"TOTP MFA setup initiated for user: {current_user.get('user_id')}")
        
        return {
            "secret": secret,
            "qr_code_uri": qr_uri,
            "backup_codes": backup_codes
        }
    except Exception as e:
        logger.error(f"TOTP setup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup TOTP MFA"
        )


class MFATOTPVerifyRequest(BaseModel):
    """Request to verify TOTP code"""
    secret: str
    code: str = Field(..., min_length=6, max_length=6)


@router.post("/mfa/totp/verify")
async def verify_totp_code(
    request: MFATOTPVerifyRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Verify TOTP code to complete MFA setup
    """
    try:
        is_valid = mfa_service.verify_totp_code(request.secret, request.code)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )
        
        logger.info(f"TOTP MFA enabled for user: {current_user.get('user_id')}")
        
        return {
            "success": True,
            "message": "TOTP MFA enabled successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TOTP verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify TOTP code"
        )


# ============================================================================
# MFA SMS OTP Endpoints
# ============================================================================

class MFASMSSetupRequest(BaseModel):
    """Request to setup SMS MFA"""
    phone_number: str = Field(..., pattern=r'^\+[1-9]\d{1,14}$')


@router.post("/mfa/sms/setup")
async def setup_sms_mfa(
    request: MFASMSSetupRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Setup SMS-based MFA
    Sends verification code to provided phone number
    """
    try:
        # Generate OTP
        otp_code = mfa_service.generate_sms_otp()
        
        # Send SMS
        success = mfa_service.send_sms_otp(request.phone_number, otp_code)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to send SMS. Please check phone number or try again later."
            )
        
        logger.info(f"SMS OTP sent for user: {current_user.get('user_id')}")
        
        # In production, store otp_code and timestamp in database/cache
        return {
            "success": True,
            "message": f"Verification code sent to {request.phone_number}",
            "expires_in_minutes": mfa_service.otp_expiry_minutes
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SMS MFA setup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup SMS MFA"
        )


class MFASMSVerifyRequest(BaseModel):
    """Request to verify SMS code"""
    phone_number: str
    code: str = Field(..., min_length=6, max_length=6)


@router.post("/mfa/sms/verify")
async def verify_sms_code(
    request: MFASMSVerifyRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Verify SMS OTP code to complete MFA setup
    """
    try:
        # In production, retrieve stored OTP and timestamp from database/cache
        # For now, this is a mock verification
        # stored_code = "123456"  # Retrieved from database
        # stored_timestamp = datetime.utcnow()  # Retrieved from database
        
        # is_valid = mfa_service.verify_otp(stored_code, stored_timestamp, request.code)
        
        # Mock validation for now
        is_valid = len(request.code) == 6 and request.code.isdigit()
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification code"
            )
        
        logger.info(f"SMS MFA enabled for user: {current_user.get('user_id')}")
        
        return {
            "success": True,
            "message": "SMS MFA enabled successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SMS verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify SMS code"
        )


# ============================================================================
# MFA Email OTP Endpoints
# ============================================================================

@router.post("/mfa/email/setup")
async def setup_email_mfa(current_user: dict = Depends(get_current_user)):
    """
    Setup Email-based MFA
    Sends verification code to user's email
    """
    try:
        email = current_user.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User email not found"
            )
        
        # Generate OTP
        otp_code = mfa_service.generate_email_otp()
        
        # Send email
        success = mfa_service.send_email_otp(email, otp_code)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to send email. Please try again later."
            )
        
        logger.info(f"Email OTP sent for user: {current_user.get('user_id')}")
        
        # In production, store otp_code and timestamp in database/cache
        return {
            "success": True,
            "message": f"Verification code sent to {email}",
            "expires_in_minutes": mfa_service.otp_expiry_minutes
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email MFA setup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup Email MFA"
        )


class MFAEmailVerifyRequest(BaseModel):
    """Request to verify email code"""
    code: str = Field(..., min_length=6, max_length=6)


@router.post("/mfa/email/verify")
async def verify_email_code(
    request: MFAEmailVerifyRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Verify Email OTP code to complete MFA setup
    """
    try:
        # In production, retrieve stored OTP and timestamp from database/cache
        # Mock validation for now
        is_valid = len(request.code) == 6 and request.code.isdigit()
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification code"
            )
        
        logger.info(f"Email MFA enabled for user: {current_user.get('user_id')}")
        
        return {
            "success": True,
            "message": "Email MFA enabled successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify email code"
        )


# ============================================================================
# Backup Codes Endpoints
# ============================================================================

class BackupCodesResponse(BaseModel):
    """Response with backup codes"""
    codes: List[str]
    message: str


@router.post("/mfa/backup-codes/generate", response_model=BackupCodesResponse)
async def generate_backup_codes(current_user: dict = Depends(get_current_user)):
    """
    Generate new backup codes for account recovery
    This will invalidate any existing backup codes
    """
    try:
        backup_codes = mfa_service.generate_backup_codes(count=10)
        
        # In production, hash and store these codes in database
        # Only show plain codes once to user
        
        logger.info(f"Backup codes generated for user: {current_user.get('user_id')}")
        
        return {
            "codes": backup_codes,
            "message": "Save these codes in a secure location. Each code can only be used once."
        }
    except Exception as e:
        logger.error(f"Backup codes generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate backup codes"
        )


class BackupCodeVerifyRequest(BaseModel):
    """Request to verify backup code"""
    code: str


@router.post("/mfa/backup-codes/verify")
async def verify_backup_code(
    request: BackupCodeVerifyRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Verify a backup code for account recovery
    Each code can only be used once
    """
    try:
        # In production, retrieve hashed backup codes from database
        # and verify against them, then mark as used
        
        # Mock verification
        is_valid = len(request.code) == 8
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid backup code"
            )
        
        logger.info(f"Backup code used for user: {current_user.get('user_id')}")
        
        return {
            "success": True,
            "message": "Backup code verified. This code cannot be used again.",
            "remaining_codes": 9  # Mock value
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Backup code verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify backup code"
        )


# ============================================================================
# MFA Management Endpoints
# ============================================================================

@router.get("/mfa/status")
async def get_mfa_status(current_user: dict = Depends(get_current_user)):
    """
    Get current MFA configuration status
    """
    try:
        # In production, retrieve from database
        return {
            "mfa_enabled": False,  # Mock value
            "methods": {
                "totp": False,
                "sms": False,
                "email": False
            },
            "backup_codes_count": 0,
            "phone_number": None,
            "email": current_user.get("email")
        }
    except Exception as e:
        logger.error(f"MFA status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get MFA status"
        )


class MFADisableRequest(BaseModel):
    """Request to disable MFA"""
    password: str
    method: Optional[str] = None  # If None, disable all methods


@router.post("/mfa/disable")
async def disable_mfa(
    request: MFADisableRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Disable MFA for the account
    Requires password confirmation
    """
    try:
        # In production, verify password and disable MFA in database
        
        logger.info(f"MFA disabled for user: {current_user.get('user_id')}")
        
        if request.method:
            return {
                "success": True,
                "message": f"{request.method.upper()} MFA disabled successfully"
            }
        else:
            return {
                "success": True,
                "message": "All MFA methods disabled successfully"
            }
    except Exception as e:
        logger.error(f"MFA disable error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable MFA"
        )
