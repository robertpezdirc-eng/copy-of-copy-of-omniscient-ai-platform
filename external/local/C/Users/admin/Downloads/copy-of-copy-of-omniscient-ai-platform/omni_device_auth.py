#!/usr/bin/env python3
"""
OMNI Device Authorization and Key Management System
Secure authentication and authorization for all connected devices
Supports API keys, JWT tokens, and certificate-based authentication
"""

import json
import time
import uuid
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
import logging
import sqlite3
import os
from pathlib import Path
from enum import Enum

class AuthMethod(Enum):
    """Authentication methods"""
    API_KEY = "api_key"
    JWT = "jwt"
    CERTIFICATE = "certificate"
    OAUTH = "oauth"

class DevicePermission(Enum):
    """Device permissions"""
    READ_TELEMETRY = "read_telemetry"
    WRITE_TELEMETRY = "write_telemetry"
    RECEIVE_COMMANDS = "receive_commands"
    SEND_COMMANDS = "send_commands"
    READ_CONFIG = "read_config"
    WRITE_CONFIG = "write_config"
    STREAM_VIDEO = "stream_video"
    ACCESS_FILES = "access_files"
    ADMIN = "admin"

@dataclass
class DeviceCredentials:
    """Device credentials and permissions"""
    device_id: str
    device_type: str
    auth_method: AuthMethod
    api_key: str = ""
    jwt_secret: str = ""
    certificate_thumbprint: str = ""
    permissions: List[DevicePermission] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    is_active: bool = True

@dataclass
class AuthToken:
    """Authentication token"""
    token_id: str
    device_id: str
    token_type: str
    expires_at: datetime
    permissions: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

class OmniDeviceAuth:
    """Device Authentication and Authorization Manager"""

    def __init__(self, db_path: str = "omni_device_auth.db"):
        self.db_path = db_path
        self.jwt_secret = os.getenv("OMNI_JWT_SECRET", secrets.token_hex(32))
        self.api_key_length = 64
        self.token_expiry_hours = 24

        # Initialize database
        self._init_database()

        # Load existing credentials
        self._load_credentials()

        print("🔐 OMNI Device Authentication system initialized")

    def _init_database(self):
        """Initialize SQLite database for device credentials"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Create credentials table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS device_credentials (
                        device_id TEXT PRIMARY KEY,
                        device_type TEXT NOT NULL,
                        auth_method TEXT NOT NULL,
                        api_key TEXT,
                        jwt_secret TEXT,
                        certificate_thumbprint TEXT,
                        permissions TEXT,
                        created_at TEXT NOT NULL,
                        expires_at TEXT,
                        last_used TEXT,
                        is_active BOOLEAN DEFAULT 1
                    )
                """)

                # Create auth tokens table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS auth_tokens (
                        token_id TEXT PRIMARY KEY,
                        device_id TEXT NOT NULL,
                        token_type TEXT NOT NULL,
                        expires_at TEXT NOT NULL,
                        permissions TEXT,
                        metadata TEXT,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (device_id) REFERENCES device_credentials (device_id)
                    )
                """)

                # Create audit log table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS auth_audit_log (
                        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        device_id TEXT,
                        event_type TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        ip_address TEXT,
                        user_agent TEXT,
                        details TEXT
                    )
                """)

                conn.commit()

        except Exception as e:
            print(f"❌ Failed to initialize auth database: {e}")

    def _load_credentials(self):
        """Load device credentials from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM device_credentials WHERE is_active = 1")

                for row in cursor:
                    credentials = DeviceCredentials(
                        device_id=row['device_id'],
                        device_type=row['device_type'],
                        auth_method=AuthMethod(row['auth_method']),
                        api_key=row['api_key'] or "",
                        jwt_secret=row['jwt_secret'] or "",
                        certificate_thumbprint=row['certificate_thumbprint'] or "",
                        permissions=json.loads(row['permissions'] or '[]'),
                        created_at=datetime.fromisoformat(row['created_at']),
                        expires_at=datetime.fromisoformat(row['expires_at']) if row['expires_at'] else None,
                        last_used=datetime.fromisoformat(row['last_used']) if row['last_used'] else None,
                        is_active=bool(row['is_active'])
                    )

                    # Store in memory (in production, use Redis or similar)
                    setattr(self, f"_credentials_{credentials.device_id}", credentials)

        except Exception as e:
            print(f"❌ Failed to load credentials: {e}")

    def register_device(self, device_type: str, permissions: List[DevicePermission] = None) -> Tuple[str, str]:
        """Register a new device and generate credentials"""
        try:
            device_id = str(uuid.uuid4())
            api_key = secrets.token_hex(self.api_key_length)

            # Set default permissions based on device type
            if permissions is None:
                permissions = self._get_default_permissions(device_type)

            # Create credentials
            credentials = DeviceCredentials(
                device_id=device_id,
                device_type=device_type,
                auth_method=AuthMethod.API_KEY,
                api_key=api_key,
                permissions=permissions,
                expires_at=datetime.now() + timedelta(hours=self.token_expiry_hours * 30)  # 30 days
            )

            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO device_credentials
                    (device_id, device_type, auth_method, api_key, permissions, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    credentials.device_id,
                    credentials.device_type,
                    credentials.auth_method.value,
                    credentials.api_key,
                    json.dumps([p.value for p in credentials.permissions]),
                    credentials.created_at.isoformat(),
                    credentials.expires_at.isoformat() if credentials.expires_at else None
                ))
                conn.commit()

            # Store in memory
            setattr(self, f"_credentials_{credentials.device_id}", credentials)

            # Log registration
            self._log_auth_event(device_id, "device_registered", {"device_type": device_type})

            print(f"📱 Device registered: {device_id}")
            return device_id, api_key

        except Exception as e:
            print(f"❌ Failed to register device: {e}")
            return None, None

    def _get_default_permissions(self, device_type: str) -> List[DevicePermission]:
        """Get default permissions based on device type"""
        base_permissions = [
            DevicePermission.READ_TELEMETRY,
            DevicePermission.WRITE_TELEMETRY,
            DevicePermission.RECEIVE_COMMANDS
        ]

        if device_type == "vr_glasses":
            base_permissions.extend([
                DevicePermission.STREAM_VIDEO,
                DevicePermission.READ_CONFIG
            ])
        elif device_type == "camera":
            base_permissions.extend([
                DevicePermission.STREAM_VIDEO,
                DevicePermission.READ_CONFIG,
                DevicePermission.ACCESS_FILES
            ])
        elif device_type == "iot_device":
            base_permissions.extend([
                DevicePermission.READ_CONFIG,
                DevicePermission.WRITE_CONFIG
            ])
        elif device_type == "car_device":
            base_permissions.extend([
                DevicePermission.READ_TELEMETRY,
                DevicePermission.RECEIVE_COMMANDS
            ])

        return base_permissions

    def authenticate_device(self, device_id: str, api_key: str = None, jwt_token: str = None) -> bool:
        """Authenticate device using API key or JWT"""
        try:
            # Get stored credentials
            credentials = getattr(self, f"_credentials_{device_id}", None)

            if not credentials or not credentials.is_active:
                self._log_auth_event(device_id, "authentication_failed", {"reason": "invalid_device"})
                return False

            # Check if credentials are expired
            if credentials.expires_at and datetime.now() > credentials.expires_at:
                self._log_auth_event(device_id, "authentication_failed", {"reason": "expired"})
                return False

            # Authenticate based on method
            if credentials.auth_method == AuthMethod.API_KEY:
                if api_key and secrets.compare_digest(credentials.api_key, api_key):
                    credentials.last_used = datetime.now()
                    self._log_auth_event(device_id, "authentication_success", {"method": "api_key"})
                    return True

            elif credentials.auth_method == AuthMethod.JWT:
                if jwt_token:
                    try:
                        payload = jwt.decode(jwt_token, credentials.jwt_secret, algorithms=["HS256"])

                        if payload.get("device_id") == device_id:
                            credentials.last_used = datetime.now()
                            self._log_auth_event(device_id, "authentication_success", {"method": "jwt"})
                            return True

                    except jwt.ExpiredSignatureError:
                        self._log_auth_event(device_id, "authentication_failed", {"reason": "expired_token"})
                    except jwt.InvalidTokenError:
                        self._log_auth_event(device_id, "authentication_failed", {"reason": "invalid_token"})

            self._log_auth_event(device_id, "authentication_failed", {"reason": "invalid_credentials"})
            return False

        except Exception as e:
            print(f"❌ Device authentication error: {e}")
            return False

    def generate_jwt_token(self, device_id: str, expiry_hours: int = None) -> Optional[str]:
        """Generate JWT token for device"""
        try:
            credentials = getattr(self, f"_credentials_{device_id}", None)

            if not credentials or not credentials.is_active:
                return None

            expiry = expiry_hours or self.token_expiry_hours

            payload = {
                "device_id": device_id,
                "device_type": credentials.device_type,
                "permissions": [p.value for p in credentials.permissions],
                "exp": datetime.utcnow() + timedelta(hours=expiry),
                "iat": datetime.utcnow(),
                "iss": "omni_platform"
            }

            token = jwt.encode(payload, credentials.jwt_secret, algorithm="HS256")

            # Log token generation
            self._log_auth_event(device_id, "jwt_generated", {"expiry_hours": expiry})

            return token

        except Exception as e:
            print(f"❌ JWT generation error: {e}")
            return None

    def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token"""
        try:
            # Decode without verification first to get device_id
            unverified_payload = jwt.decode(token, options={"verify_signature": False})

            device_id = unverified_payload.get("device_id")
            if not device_id:
                return None

            # Get device credentials
            credentials = getattr(self, f"_credentials_{device_id}", None)
            if not credentials:
                return None

            # Verify token
            payload = jwt.decode(token, credentials.jwt_secret, algorithms=["HS256"])

            # Update last used
            credentials.last_used = datetime.now()

            return payload

        except Exception as e:
            print(f"❌ JWT validation error: {e}")
            return None

    def check_device_permission(self, device_id: str, permission: DevicePermission) -> bool:
        """Check if device has specific permission"""
        try:
            credentials = getattr(self, f"_credentials_{device_id}", None)

            if not credentials or not credentials.is_active:
                return False

            return permission in credentials.permissions

        except Exception as e:
            print(f"❌ Permission check error: {e}")
            return False

    def revoke_device_access(self, device_id: str) -> bool:
        """Revoke device access"""
        try:
            # Update database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE device_credentials SET is_active = 0 WHERE device_id = ?", (device_id,))
                conn.commit()

            # Remove from memory
            if hasattr(self, f"_credentials_{device_id}"):
                delattr(self, f"_credentials_{device_id}")

            # Log revocation
            self._log_auth_event(device_id, "access_revoked", {})

            print(f"🚫 Device access revoked: {device_id}")
            return True

        except Exception as e:
            print(f"❌ Failed to revoke device access: {e}")
            return False

    def get_device_info(self, device_id: str) -> Dict[str, Any]:
        """Get device information"""
        try:
            credentials = getattr(self, f"_credentials_{device_id}", None)

            if not credentials:
                return {"error": "Device not found"}

            return {
                "device_id": credentials.device_id,
                "device_type": credentials.device_type,
                "auth_method": credentials.auth_method.value,
                "permissions": [p.value for p in credentials.permissions],
                "created_at": credentials.created_at.isoformat(),
                "expires_at": credentials.expires_at.isoformat() if credentials.expires_at else None,
                "last_used": credentials.last_used.isoformat() if credentials.last_used else None,
                "is_active": credentials.is_active
            }

        except Exception as e:
            return {"error": str(e)}

    def list_devices(self, device_type: str = None) -> List[Dict[str, Any]]:
        """List all registered devices"""
        try:
            devices = []

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                if device_type:
                    cursor = conn.execute(
                        "SELECT * FROM device_credentials WHERE device_type = ? AND is_active = 1",
                        (device_type,)
                    )
                else:
                    cursor = conn.execute("SELECT * FROM device_credentials WHERE is_active = 1")

                for row in cursor:
                    devices.append({
                        "device_id": row['device_id'],
                        "device_type": row['device_type'],
                        "auth_method": row['auth_method'],
                        "created_at": row['created_at'],
                        "last_used": row['last_used']
                    })

            return devices

        except Exception as e:
            print(f"❌ Failed to list devices: {e}")
            return []

    def _log_auth_event(self, device_id: str, event_type: str, details: Dict[str, Any]):
        """Log authentication event"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO auth_audit_log (device_id, event_type, timestamp, details)
                    VALUES (?, ?, ?, ?)
                """, (
                    device_id,
                    event_type,
                    datetime.now().isoformat(),
                    json.dumps(details)
                ))
                conn.commit()

        except Exception as e:
            print(f"⚠️ Failed to log auth event: {e}")

    def cleanup_expired_tokens(self):
        """Clean up expired authentication tokens"""
        try:
            current_time = datetime.now().isoformat()

            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM auth_tokens WHERE expires_at < ?", (current_time,))
                conn.commit()

            print("🧹 Cleaned up expired auth tokens")

        except Exception as e:
            print(f"❌ Failed to cleanup expired tokens: {e}")

    def rotate_device_key(self, device_id: str) -> Optional[str]:
        """Rotate device API key"""
        try:
            credentials = getattr(self, f"_credentials_{device_id}", None)

            if not credentials:
                return None

            # Generate new API key
            new_api_key = secrets.token_hex(self.api_key_length)
            credentials.api_key = new_api_key

            # Update database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE device_credentials SET api_key = ? WHERE device_id = ?",
                    (new_api_key, device_id)
                )
                conn.commit()

            # Log key rotation
            self._log_auth_event(device_id, "key_rotated", {})

            print(f"🔄 API key rotated for device: {device_id}")
            return new_api_key

        except Exception as e:
            print(f"❌ Failed to rotate device key: {e}")
            return None

    def get_auth_stats(self) -> Dict[str, Any]:
        """Get authentication statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # Count devices by type
                device_types = {}
                for row in conn.execute("SELECT device_type, COUNT(*) as count FROM device_credentials WHERE is_active = 1 GROUP BY device_type"):
                    device_types[row['device_type']] = row['count']

                # Count recent events
                recent_events = len(list(conn.execute(
                    "SELECT * FROM auth_audit_log WHERE timestamp > ?",
                    (datetime.now() - timedelta(hours=24)).isoformat()
                )))

                # Count active tokens
                active_tokens = len(list(conn.execute(
                    "SELECT * FROM auth_tokens WHERE expires_at > ?",
                    datetime.now().isoformat()
                )))

            return {
                "total_devices": sum(device_types.values()),
                "device_types": device_types,
                "recent_events_24h": recent_events,
                "active_tokens": active_tokens,
                "last_updated": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": str(e)}

# Global auth manager instance
omni_device_auth = None

def initialize_device_auth(db_path: str = "omni_device_auth.db") -> OmniDeviceAuth:
    """Initialize device authentication system"""
    global omni_device_auth
    omni_device_auth = OmniDeviceAuth(db_path)
    return omni_device_auth

def get_device_auth() -> OmniDeviceAuth:
    """Get global device auth instance"""
    return omni_device_auth

# API functions for external use
def register_device(device_type: str, permissions: List[str] = None) -> Tuple[str, str]:
    """Register a new device"""
    if omni_device_auth:
        device_permissions = [DevicePermission(p) for p in (permissions or [])]
        return omni_device_auth.register_device(device_type, device_permissions)
    return None, None

def authenticate_device(device_id: str, api_key: str = None, jwt_token: str = None) -> bool:
    """Authenticate device"""
    if omni_device_auth:
        return omni_device_auth.authenticate_device(device_id, api_key, jwt_token)
    return False

def check_device_permission(device_id: str, permission: str) -> bool:
    """Check device permission"""
    if omni_device_auth:
        return omni_device_auth.check_device_permission(device_id, DevicePermission(permission))
    return False

def generate_device_jwt(device_id: str) -> str:
    """Generate JWT for device"""
    if omni_device_auth:
        return omni_device_auth.generate_jwt_token(device_id)
    return None

def get_device_list(device_type: str = None) -> List[Dict[str, Any]]:
    """Get list of devices"""
    if omni_device_auth:
        return omni_device_auth.list_devices(device_type)
    return []

if __name__ == "__main__":
    # Test device authentication system
    print("🧪 Testing OMNI Device Authentication...")

    # Initialize auth system
    auth = initialize_device_auth()

    # Test device registration
    device_id, api_key = register_device("vr_glasses", ["read_telemetry", "write_telemetry", "stream_video"])
    print(f"✅ Device registered: {device_id}")
    print(f"✅ API Key: {api_key[:20]}...")

    # Test authentication
    if authenticate_device(device_id, api_key=api_key):
        print("✅ Device authentication successful")
    else:
        print("❌ Device authentication failed")

    # Test JWT generation
    jwt_token = generate_device_jwt(device_id)
    if jwt_token:
        print(f"✅ JWT generated: {jwt_token[:50]}...")

        # Test JWT validation
        payload = auth.validate_jwt_token(jwt_token)
        if payload:
            print(f"✅ JWT validated for device: {payload.get('device_id')}")
        else:
            print("❌ JWT validation failed")

    # Test permission check
    if check_device_permission(device_id, "stream_video"):
        print("✅ Device has stream_video permission")
    else:
        print("❌ Device missing stream_video permission")

    # Test device listing
    devices = get_device_list("vr_glasses")
    print(f"✅ Found {len(devices)} VR devices")

    # Test auth stats
    stats = auth.get_auth_stats()
    print(f"✅ Auth stats: {stats}")

    print("\n✅ OMNI Device Authentication test completed!")