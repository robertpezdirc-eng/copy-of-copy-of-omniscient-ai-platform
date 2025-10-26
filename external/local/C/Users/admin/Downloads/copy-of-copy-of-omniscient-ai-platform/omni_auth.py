#!/usr/bin/env python3
"""
OMNI Platform Authentication Module
Handles secure authentication between dashboard and OMNI platform
"""

import os
import json
import time
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class AuthMethod(Enum):
    API_KEY = "api_key"
    JWT = "jwt"
    HMAC = "hmac"

@dataclass
class AuthConfig:
    """Authentication configuration"""
    method: AuthMethod
    api_key: Optional[str] = None
    secret_key: Optional[str] = None
    jwt_secret: Optional[str] = None
    token_expiry: int = 3600  # seconds

@dataclass
class AuthToken:
    """Authentication token information"""
    token: str
    expires_at: datetime
    user_id: str
    permissions: list

class OmniAuthenticator:
    """
    Handles authentication between dashboard and OMNI platform
    """

    def __init__(self, config: Optional[AuthConfig] = None):
        self.config = config or self._load_config()
        self.tokens: Dict[str, AuthToken] = {}

        # Generate secret key if not provided
        if not self.config.secret_key:
            self.config.secret_key = secrets.token_hex(32)

        logger.info(f"OMNI Authenticator initialized with method: {self.config.method}")

    def _load_config(self) -> AuthConfig:
        """Load authentication configuration from environment"""
        method_str = os.environ.get('OMNI_AUTH_METHOD', 'api_key').lower()

        try:
            method = AuthMethod(method_str)
        except ValueError:
            logger.warning(f"Invalid auth method: {method_str}, defaulting to api_key")
            method = AuthMethod.API_KEY

        return AuthConfig(
            method=method,
            api_key=os.environ.get('OMNI_API_KEY'),
            secret_key=os.environ.get('OMNI_SECRET_KEY'),
            jwt_secret=os.environ.get('OMNI_JWT_SECRET'),
            token_expiry=int(os.environ.get('OMNI_TOKEN_EXPIRY', '3600'))
        )

    def generate_api_key(self) -> str:
        """Generate a new API key"""
        timestamp = str(int(time.time()))
        random_part = secrets.token_hex(16)
        raw_key = f"{timestamp}:{random_part}:{self.config.secret_key}"

        # Create hash for verification
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        return f"omni_{timestamp}_{random_part}_{key_hash[:16]}"

    def verify_api_key(self, api_key: str) -> bool:
        """Verify API key format and validity"""
        if not api_key or not api_key.startswith('omni_'):
            return False

        try:
            parts = api_key.split('_')
            if len(parts) != 4:
                return False

            timestamp_str, random_part, provided_hash = parts[1:]

            # Check if key is too old (24 hours)
            timestamp = int(timestamp_str)
            if time.time() - timestamp > 24 * 3600:
                return False

            # Verify hash
            raw_key = f"{timestamp_str}:{random_part}:{self.config.secret_key}"
            expected_hash = hashlib.sha256(raw_key.encode()).hexdigest()[:16]

            return hmac.compare_digest(provided_hash, expected_hash)

        except (ValueError, IndexError):
            return False

    def generate_hmac_signature(self, message: str, secret_key: Optional[str] = None) -> str:
        """Generate HMAC signature for message"""
        key = secret_key or self.config.secret_key
        if not key:
            raise ValueError("Secret key required for HMAC authentication")

        return hmac.new(
            key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

    def verify_hmac_signature(self, message: str, signature: str, secret_key: Optional[str] = None) -> bool:
        """Verify HMAC signature"""
        try:
            expected_signature = self.generate_hmac_signature(message, secret_key)
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"HMAC verification failed: {e}")
            return False

    def create_signed_request(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a signed request with authentication"""
        timestamp = str(int(time.time()))
        payload_str = json.dumps(payload, sort_keys=True)

        # Create signature
        message = f"{url}:{timestamp}:{payload_str}"
        signature = self.generate_hmac_signature(message)

        return {
            'url': url,
            'payload': payload,
            'timestamp': timestamp,
            'signature': signature,
            'auth_method': self.config.method.value
        }

    def verify_signed_request(self, signed_request: Dict[str, Any]) -> bool:
        """Verify a signed request"""
        try:
            url = signed_request['url']
            payload = signed_request['payload']
            timestamp = signed_request['timestamp']
            signature = signed_request['signature']

            # Check timestamp (allow 5 minutes tolerance)
            request_time = int(timestamp)
            current_time = int(time.time())
            if abs(current_time - request_time) > 300:
                return False

            # Recreate message and verify signature
            payload_str = json.dumps(payload, sort_keys=True)
            message = f"{url}:{timestamp}:{payload_str}"

            return self.verify_hmac_signature(message, signature)

        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Request verification failed: {e}")
            return False

    def get_auth_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Get authentication headers for requests"""
        headers = {}

        if self.config.method == AuthMethod.API_KEY:
            if self.config.api_key:
                headers['Authorization'] = f'Bearer {self.config.api_key}'
            else:
                logger.warning("No API key configured")

        elif self.config.method == AuthMethod.HMAC:
            # HMAC is handled per-request in create_signed_request
            pass

        # Add any additional headers
        if additional_headers:
            headers.update(additional_headers)

        return headers

    def authenticate_request(self, request_data: Dict[str, Any]) -> bool:
        """Authenticate an incoming request"""
        auth_header = request_data.get('headers', {}).get('Authorization', '')

        if self.config.method == AuthMethod.API_KEY:
            if not auth_header.startswith('Bearer '):
                return False

            api_key = auth_header[7:]  # Remove 'Bearer ' prefix
            return self.verify_api_key(api_key)

        elif self.config.method == AuthMethod.HMAC:
            # For HMAC, we need the full signed request
            return self.verify_signed_request(request_data)

        return False

    def get_dashboard_credentials(self) -> Dict[str, str]:
        """Get credentials for dashboard to authenticate with OMNI platform"""
        return {
            'auth_method': self.config.method.value,
            'api_key': self.config.api_key,
            'timestamp': str(int(time.time())),
            'dashboard_id': 'omni-operational-dashboard'
        }

# Global authenticator instance
omni_auth = None

def get_omni_authenticator() -> OmniAuthenticator:
    """Get or create global OMNI authenticator"""
    global omni_auth
    if omni_auth is None:
        omni_auth = OmniAuthenticator()
    return omni_auth

def initialize_auth(config: Optional[AuthConfig] = None) -> OmniAuthenticator:
    """Initialize OMNI authenticator with custom config"""
    global omni_auth
    omni_auth = OmniAuthenticator(config)
    return omni_auth