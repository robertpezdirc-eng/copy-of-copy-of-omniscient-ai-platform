"""
Multi-Factor Authentication (MFA) Implementation

Supports multiple MFA methods:
- TOTP (Time-based One-Time Password) - Google Authenticator, Authy
- SMS verification codes
- Email verification codes
- Backup recovery codes
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from enum import Enum
import logging
import secrets
import hashlib
import base64
import hmac
import time
import math

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mfa", tags=["Multi-Factor Authentication"])


# Enums
class MFAMethod(str, Enum):
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"


class MFAStatus(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    PENDING = "pending"


# Request/Response Models
class MFASetupRequest(BaseModel):
    user_id: str
    method: MFAMethod
    phone_number: Optional[str] = Field(None, description="Required for SMS")
    email: Optional[EmailStr] = Field(None, description="Required for email")


class MFASetupResponse(BaseModel):
    user_id: str
    method: MFAMethod
    status: MFAStatus
    secret: Optional[str] = Field(None, description="TOTP secret (only for TOTP)")
    qr_code_url: Optional[str] = Field(None, description="QR code URL for TOTP")
    backup_codes: Optional[List[str]] = Field(None, description="Backup recovery codes")


class MFAVerifyRequest(BaseModel):
    user_id: str
    method: MFAMethod
    code: str = Field(..., min_length=6, max_length=6)


class MFAVerifyResponse(BaseModel):
    verified: bool
    user_id: str
    method: MFAMethod
    timestamp: datetime


class MFASendCodeRequest(BaseModel):
    user_id: str
    method: MFAMethod


class MFADisableRequest(BaseModel):
    user_id: str
    verification_code: str = Field(..., description="Current MFA code to confirm disable")


class BackupCodeVerifyRequest(BaseModel):
    user_id: str
    backup_code: str


# In-memory storage (replace with database in production)
_mfa_secrets: Dict[str, Dict] = {}  # user_id -> {method, secret, enabled, etc}
_totp_secrets: Dict[str, str] = {}  # user_id -> base32 secret
_backup_codes: Dict[str, List[str]] = {}  # user_id -> [hashed_codes]
_pending_codes: Dict[str, Dict] = {}  # user_id -> {code, expires, method}


def generate_totp_secret() -> str:
    """Generate a random base32 secret for TOTP"""
    return base64.b32encode(secrets.token_bytes(20)).decode('utf-8')


def generate_backup_codes(count: int = 10) -> List[str]:
    """Generate backup recovery codes"""
    codes = []
    for _ in range(count):
        # Generate 8-character alphanumeric code
        code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
        codes.append(code)
    return codes


def hash_backup_code(code: str) -> str:
    """Hash backup code for storage"""
    return hashlib.sha256(code.encode()).hexdigest()


def generate_totp_code(secret: str, time_step: int = 30, digits: int = 6) -> str:
    """
    Generate TOTP code based on current time
    
    Args:
        secret: Base32 encoded secret
        time_step: Time step in seconds (default 30)
        digits: Number of digits in code (default 6)
    """
    try:
        # Decode base32 secret
        key = base64.b32decode(secret, casefold=True)
        
        # Get current time counter
        counter = int(time.time() // time_step)
        
        # Convert counter to bytes
        counter_bytes = counter.to_bytes(8, byteorder='big')
        
        # Generate HMAC-SHA1
        hmac_hash = hmac.new(key, counter_bytes, hashlib.sha1).digest()
        
        # Get offset from last 4 bits
        offset = hmac_hash[-1] & 0x0f
        
        # Get 4 bytes starting from offset
        code_bytes = hmac_hash[offset:offset + 4]
        
        # Convert to integer
        code_int = int.from_bytes(code_bytes, byteorder='big')
        
        # Remove most significant bit
        code_int &= 0x7fffffff
        
        # Get last n digits
        code = code_int % (10 ** digits)
        
        # Format with leading zeros
        return str(code).zfill(digits)
    except Exception as e:
        logger.error(f"TOTP generation error: {e}")
        raise


def verify_totp_code(secret: str, code: str, window: int = 1) -> bool:
    """
    Verify TOTP code with time window tolerance
    
    Args:
        secret: Base32 encoded secret
        code: 6-digit code to verify
        window: Number of time steps to check before/after current (default 1)
    """
    try:
        current_time = int(time.time() // 30)
        
        # Check current time and +/- window
        for offset in range(-window, window + 1):
            time_counter = current_time + offset
            expected_code = generate_totp_code(secret)
            
            if code == expected_code:
                return True
        
        return False
    except Exception as e:
        logger.error(f"TOTP verification error: {e}")
        return False


def generate_sms_code() -> str:
    """Generate 6-digit SMS verification code"""
    return ''.join(str(secrets.randbelow(10)) for _ in range(6))


def send_sms_code(phone_number: str, code: str) -> bool:
    """Send SMS code (mock implementation)"""
    logger.info(f"[SMS] Sending code {code} to {phone_number}")
    # In production: integrate with Twilio, AWS SNS, etc.
    return True


def send_email_code(email: str, code: str) -> bool:
    """Send email code (mock implementation)"""
    logger.info(f"[EMAIL] Sending code {code} to {email}")
    # In production: integrate with SendGrid, AWS SES, etc.
    return True


@router.post("/setup", response_model=MFASetupResponse)
async def setup_mfa(request: MFASetupRequest):
    """
    Set up MFA for a user
    
    Steps:
    1. Generate secret/codes based on method
    2. For TOTP: return secret and QR code URL
    3. For SMS/Email: send verification code
    4. Generate backup codes
    """
    try:
        user_id = request.user_id
        method = request.method
        
        # Initialize MFA record
        if user_id not in _mfa_secrets:
            _mfa_secrets[user_id] = {}
        
        response_data = {
            "user_id": user_id,
            "method": method,
            "status": MFAStatus.PENDING
        }
        
        if method == MFAMethod.TOTP:
            # Generate TOTP secret
            secret = generate_totp_secret()
            _totp_secrets[user_id] = secret
            
            # Generate QR code URL for authenticator apps
            # Format: otpauth://totp/AppName:user@example.com?secret=SECRET&issuer=AppName
            qr_url = f"otpauth://totp/OmniPlatform:{user_id}?secret={secret}&issuer=OmniPlatform"
            
            response_data["secret"] = secret
            response_data["qr_code_url"] = qr_url
            
        elif method == MFAMethod.SMS:
            if not request.phone_number:
                raise HTTPException(status_code=400, detail="Phone number required for SMS MFA")
            
            # Generate and send SMS code
            code = generate_sms_code()
            _pending_codes[user_id] = {
                "code": code,
                "method": MFAMethod.SMS,
                "phone": request.phone_number,
                "expires": datetime.utcnow() + timedelta(minutes=10)
            }
            
            send_sms_code(request.phone_number, code)
            
        elif method == MFAMethod.EMAIL:
            if not request.email:
                raise HTTPException(status_code=400, detail="Email required for email MFA")
            
            # Generate and send email code
            code = generate_sms_code()  # Same 6-digit code format
            _pending_codes[user_id] = {
                "code": code,
                "method": MFAMethod.EMAIL,
                "email": request.email,
                "expires": datetime.utcnow() + timedelta(minutes=10)
            }
            
            send_email_code(request.email, code)
        
        # Generate backup codes
        backup_codes = generate_backup_codes()
        _backup_codes[user_id] = [hash_backup_code(code) for code in backup_codes]
        response_data["backup_codes"] = backup_codes
        
        # Store MFA configuration
        _mfa_secrets[user_id][method.value] = {
            "enabled": False,  # Not enabled until verified
            "setup_at": datetime.utcnow(),
            "phone": request.phone_number if method == MFAMethod.SMS else None,
            "email": request.email if method == MFAMethod.EMAIL else None
        }
        
        return MFASetupResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA setup failed for user {request.user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"MFA setup failed: {str(e)}")


@router.post("/verify", response_model=MFAVerifyResponse)
async def verify_mfa_code(request: MFAVerifyRequest):
    """
    Verify MFA code
    
    For TOTP: verify against generated code
    For SMS/Email: verify against sent code
    """
    try:
        user_id = request.user_id
        method = request.method
        code = request.code
        
        verified = False
        
        if method == MFAMethod.TOTP:
            # Verify TOTP code
            if user_id in _totp_secrets:
                secret = _totp_secrets[user_id]
                verified = verify_totp_code(secret, code)
                
                if verified:
                    # Enable MFA after successful verification
                    if user_id in _mfa_secrets and method.value in _mfa_secrets[user_id]:
                        _mfa_secrets[user_id][method.value]["enabled"] = True
                        _mfa_secrets[user_id][method.value]["verified_at"] = datetime.utcnow()
            
        elif method in [MFAMethod.SMS, MFAMethod.EMAIL]:
            # Verify SMS/Email code
            if user_id in _pending_codes:
                pending = _pending_codes[user_id]
                
                if pending["method"] == method:
                    # Check expiration
                    if datetime.utcnow() > pending["expires"]:
                        del _pending_codes[user_id]
                        raise HTTPException(status_code=400, detail="Code expired")
                    
                    # Verify code
                    if pending["code"] == code:
                        verified = True
                        del _pending_codes[user_id]
                        
                        # Enable MFA
                        if user_id in _mfa_secrets and method.value in _mfa_secrets[user_id]:
                            _mfa_secrets[user_id][method.value]["enabled"] = True
                            _mfa_secrets[user_id][method.value]["verified_at"] = datetime.utcnow()
        
        if not verified:
            raise HTTPException(status_code=401, detail="Invalid verification code")
        
        return MFAVerifyResponse(
            verified=True,
            user_id=user_id,
            method=method,
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA verification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@router.post("/send-code")
async def send_mfa_code(request: MFASendCodeRequest):
    """
    Send/resend MFA code for SMS or Email method
    """
    try:
        user_id = request.user_id
        method = request.method
        
        if method not in [MFAMethod.SMS, MFAMethod.EMAIL]:
            raise HTTPException(status_code=400, detail="This endpoint only supports SMS and Email methods")
        
        # Check if user has MFA set up
        if user_id not in _mfa_secrets or method.value not in _mfa_secrets[user_id]:
            raise HTTPException(status_code=404, detail="MFA not set up for this method")
        
        mfa_config = _mfa_secrets[user_id][method.value]
        
        # Generate code
        code = generate_sms_code()
        _pending_codes[user_id] = {
            "code": code,
            "method": method,
            "expires": datetime.utcnow() + timedelta(minutes=10)
        }
        
        # Send code
        if method == MFAMethod.SMS:
            phone = mfa_config.get("phone")
            if not phone:
                raise HTTPException(status_code=400, detail="Phone number not configured")
            send_sms_code(phone, code)
            
        elif method == MFAMethod.EMAIL:
            email = mfa_config.get("email")
            if not email:
                raise HTTPException(status_code=400, detail="Email not configured")
            send_email_code(email, code)
        
        return {
            "success": True,
            "user_id": user_id,
            "method": method,
            "sent_at": datetime.utcnow(),
            "expires_in_minutes": 10
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send MFA code: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send code: {str(e)}")


@router.post("/verify-backup-code")
async def verify_backup_code(request: BackupCodeVerifyRequest):
    """
    Verify backup recovery code
    
    Backup codes can only be used once
    """
    try:
        user_id = request.user_id
        backup_code = request.backup_code.upper().replace('-', '').replace(' ', '')
        
        if user_id not in _backup_codes:
            raise HTTPException(status_code=404, detail="No backup codes found for user")
        
        # Hash the provided code
        code_hash = hash_backup_code(backup_code)
        
        # Check if code exists
        if code_hash in _backup_codes[user_id]:
            # Remove used code
            _backup_codes[user_id].remove(code_hash)
            
            logger.info(f"Backup code used for user {user_id}. Remaining codes: {len(_backup_codes[user_id])}")
            
            return {
                "verified": True,
                "user_id": user_id,
                "remaining_codes": len(_backup_codes[user_id]),
                "timestamp": datetime.utcnow()
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid backup code")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Backup code verification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@router.post("/disable")
async def disable_mfa(request: MFADisableRequest):
    """
    Disable MFA for a user (requires verification)
    """
    try:
        user_id = request.user_id
        
        if user_id not in _mfa_secrets:
            raise HTTPException(status_code=404, detail="MFA not enabled for user")
        
        # Verify current MFA code before disabling
        # Try all enabled methods
        verified = False
        for method_str, config in _mfa_secrets[user_id].items():
            if not config.get("enabled"):
                continue
                
            method = MFAMethod(method_str)
            
            if method == MFAMethod.TOTP and user_id in _totp_secrets:
                if verify_totp_code(_totp_secrets[user_id], request.verification_code):
                    verified = True
                    break
        
        if not verified:
            raise HTTPException(status_code=401, detail="Invalid verification code")
        
        # Disable all MFA methods
        del _mfa_secrets[user_id]
        if user_id in _totp_secrets:
            del _totp_secrets[user_id]
        if user_id in _backup_codes:
            del _backup_codes[user_id]
        if user_id in _pending_codes:
            del _pending_codes[user_id]
        
        logger.info(f"MFA disabled for user {user_id}")
        
        return {
            "success": True,
            "user_id": user_id,
            "message": "MFA has been disabled",
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disable MFA: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to disable MFA: {str(e)}")


@router.get("/status/{user_id}")
async def get_mfa_status(user_id: str):
    """Get MFA status and enabled methods for a user"""
    enabled_methods = []
    
    if user_id in _mfa_secrets:
        for method_str, config in _mfa_secrets[user_id].items():
            if config.get("enabled"):
                enabled_methods.append({
                    "method": method_str,
                    "setup_at": config.get("setup_at"),
                    "verified_at": config.get("verified_at")
                })
    
    backup_codes_count = len(_backup_codes.get(user_id, []))
    
    return {
        "user_id": user_id,
        "mfa_enabled": len(enabled_methods) > 0,
        "enabled_methods": enabled_methods,
        "backup_codes_remaining": backup_codes_count,
        "status": "enabled" if enabled_methods else "disabled"
    }


@router.post("/regenerate-backup-codes/{user_id}")
async def regenerate_backup_codes(user_id: str):
    """
    Regenerate backup codes for a user
    
    This invalidates all existing backup codes
    """
    try:
        if user_id not in _mfa_secrets:
            raise HTTPException(status_code=404, detail="MFA not enabled for user")
        
        # Generate new backup codes
        backup_codes = generate_backup_codes()
        _backup_codes[user_id] = [hash_backup_code(code) for code in backup_codes]
        
        logger.info(f"Backup codes regenerated for user {user_id}")
        
        return {
            "success": True,
            "user_id": user_id,
            "backup_codes": backup_codes,
            "generated_at": datetime.utcnow(),
            "message": "Save these codes in a secure location. They cannot be recovered."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to regenerate backup codes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to regenerate codes: {str(e)}")
