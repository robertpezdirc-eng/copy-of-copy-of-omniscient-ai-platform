"""
Multi-Factor Authentication Service
Supports TOTP, SMS OTP, Email OTP, and Backup Codes
"""

import os
import pyotp
import secrets
import logging
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# For hashing backup codes
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class MFAService:
    """
    Comprehensive MFA service supporting multiple authentication methods:
    - TOTP (Time-based One-Time Password for authenticator apps)
    - SMS OTP (via Twilio)
    - Email OTP (via SendGrid)
    - Backup codes (for account recovery)
    """
    
    def __init__(self):
        """Initialize MFA service with required credentials"""
        # Twilio configuration
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        # SendGrid configuration
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.sendgrid_from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@omni-ultra.com")
        
        # OTP configuration
        self.otp_expiry_minutes = int(os.getenv("OTP_EXPIRY_MINUTES", "5"))
        self.otp_length = 6
        
    # ============================================================================
    # TOTP (Time-based One-Time Password) Methods
    # ============================================================================
    
    def generate_totp_secret(self) -> str:
        """
        Generate a new TOTP secret for authenticator apps
        
        Returns:
            Base32-encoded secret string
        """
        return pyotp.random_base32()
    
    def get_totp_uri(self, secret: str, email: str, issuer: str = "OMNI Platform") -> str:
        """
        Generate provisioning URI for QR code generation
        
        Args:
            secret: Base32-encoded TOTP secret
            email: User's email address
            issuer: Application name
            
        Returns:
            otpauth:// URI for QR code
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=email, issuer_name=issuer)
    
    def generate_totp_code(self, secret: str) -> str:
        """
        Generate current TOTP code (for testing purposes)
        
        Args:
            secret: Base32-encoded TOTP secret
            
        Returns:
            6-digit TOTP code
        """
        totp = pyotp.TOTP(secret)
        return totp.now()
    
    def verify_totp_code(self, secret: str, code: str) -> bool:
        """
        Verify a TOTP code
        
        Args:
            secret: Base32-encoded TOTP secret
            code: 6-digit code to verify
            
        Returns:
            True if code is valid, False otherwise
        """
        try:
            totp = pyotp.TOTP(secret)
            # valid_window=1 allows codes from previous/next 30s window
            return totp.verify(code, valid_window=1)
        except Exception as e:
            logger.error(f"TOTP verification error: {e}")
            return False
    
    # ============================================================================
    # SMS OTP Methods
    # ============================================================================
    
    def generate_sms_otp(self) -> str:
        """
        Generate a random SMS OTP code
        
        Returns:
            6-digit numeric code
        """
        return ''.join([str(secrets.randbelow(10)) for _ in range(self.otp_length)])
    
    def send_sms_otp(self, phone_number: str, code: str) -> bool:
        """
        Send OTP code via SMS using Twilio
        
        Args:
            phone_number: Recipient phone number (E.164 format)
            code: OTP code to send
            
        Returns:
            True if SMS sent successfully, False otherwise
        """
        if not all([self.twilio_account_sid, self.twilio_auth_token, self.twilio_phone_number]):
            logger.warning("Twilio credentials not configured, skipping SMS send")
            return False
            
        try:
            from twilio.rest import Client
            
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            message = client.messages.create(
                body=f"Your OMNI Platform verification code is: {code}. Valid for {self.otp_expiry_minutes} minutes.",
                from_=self.twilio_phone_number,
                to=phone_number
            )
            
            logger.info(f"SMS OTP sent successfully. SID: {message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS OTP: {e}")
            return False
    
    # ============================================================================
    # Email OTP Methods
    # ============================================================================
    
    def generate_email_otp(self) -> str:
        """
        Generate a random Email OTP code
        
        Returns:
            6-digit numeric code
        """
        return ''.join([str(secrets.randbelow(10)) for _ in range(self.otp_length)])
    
    def send_email_otp(self, email: str, code: str) -> bool:
        """
        Send OTP code via email using SendGrid
        
        Args:
            email: Recipient email address
            code: OTP code to send
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.sendgrid_api_key:
            logger.warning("SendGrid API key not configured, skipping email send")
            return False
            
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            
            message = Mail(
                from_email=self.sendgrid_from_email,
                to_emails=email,
                subject="OMNI Platform - Verification Code",
                html_content=f"""
                <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2>Your Verification Code</h2>
                    <p>Your OMNI Platform verification code is:</p>
                    <h1 style="color: #4CAF50; letter-spacing: 5px;">{code}</h1>
                    <p>This code will expire in {self.otp_expiry_minutes} minutes.</p>
                    <p>If you did not request this code, please ignore this email.</p>
                </body>
                </html>
                """
            )
            
            sg = SendGridAPIClient(self.sendgrid_api_key)
            response = sg.send(message)
            
            logger.info(f"Email OTP sent successfully. Status code: {response.status_code}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email OTP: {e}")
            return False
    
    def verify_otp(self, stored_code: str, stored_timestamp: datetime, provided_code: str) -> bool:
        """
        Verify an OTP code (SMS or Email)
        
        Args:
            stored_code: The OTP code that was generated
            stored_timestamp: When the OTP was generated
            provided_code: The code provided by the user
            
        Returns:
            True if code is valid and not expired, False otherwise
        """
        # Check if code has expired
        expiry_time = stored_timestamp + timedelta(minutes=self.otp_expiry_minutes)
        if datetime.utcnow() > expiry_time:
            logger.info("OTP code has expired")
            return False
        
        # Verify code matches
        return secrets.compare_digest(stored_code, provided_code)
    
    # ============================================================================
    # Backup Codes Methods
    # ============================================================================
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """
        Generate backup codes for account recovery
        
        Args:
            count: Number of backup codes to generate
            
        Returns:
            List of backup codes
        """
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric codes
            code = secrets.token_hex(4)  # Generates 8 hex chars
            codes.append(code)
        return codes
    
    def hash_backup_code(self, code: str) -> str:
        """
        Hash a backup code for secure storage
        
        Args:
            code: Plain text backup code
            
        Returns:
            Hashed backup code
        """
        return pwd_context.hash(code)
    
    def verify_backup_code(self, plain_code: str, hashed_code: str) -> bool:
        """
        Verify a backup code against its hash
        
        Args:
            plain_code: Plain text backup code provided by user
            hashed_code: Stored hashed backup code
            
        Returns:
            True if code matches, False otherwise
        """
        try:
            return pwd_context.verify(plain_code, hashed_code)
        except Exception as e:
            logger.error(f"Backup code verification error: {e}")
            return False
    
    # ============================================================================
    # Utility Methods
    # ============================================================================
    
    def generate_qr_code_data(self, secret: str, email: str) -> str:
        """
        Generate QR code data for TOTP setup
        
        Args:
            secret: TOTP secret
            email: User email
            
        Returns:
            URI string for QR code generation
        """
        return self.get_totp_uri(secret, email)