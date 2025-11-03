# MFA Implementation Documentation

## Overview

This document describes the comprehensive Multi-Factor Authentication (MFA) implementation for the OMNI Enterprise Ultra Max platform. The implementation includes support for:

1. **TOTP** (Time-based One-Time Password) - for authenticator apps like Google Authenticator, Authy
2. **SMS OTP** - for text message verification
3. **Email OTP** - for email verification
4. **Backup Codes** - for account recovery

## Architecture

### Core Components

#### 1. MFA Service (`backend/services/mfa_service.py`)

The main MFA service provides all multi-factor authentication functionality:

**TOTP Methods:**
- `generate_totp_secret()` - Creates a new Base32-encoded secret for TOTP
- `get_totp_uri(secret, email)` - Generates QR code URI for authenticator apps
- `generate_totp_code(secret)` - Generates current TOTP code (for testing)
- `verify_totp_code(secret, code)` - Verifies a TOTP code with time window support

**SMS OTP Methods:**
- `generate_sms_otp()` - Creates a 6-digit numeric OTP
- `send_sms_otp(phone_number, code)` - Sends OTP via Twilio SMS

**Email OTP Methods:**
- `generate_email_otp()` - Creates a 6-digit numeric OTP
- `send_email_otp(email, code)` - Sends OTP via SendGrid email

**Backup Codes Methods:**
- `generate_backup_codes(count)` - Generates recovery codes
- `hash_backup_code(code)` - Hashes a code for secure storage
- `verify_backup_code(plain_code, hashed_code)` - Verifies a backup code

**OTP Verification:**
- `verify_otp(stored_code, stored_timestamp, provided_code)` - Verifies OTP with expiry check

#### 2. Authentication Routes (`backend/routes/auth_routes.py`)

RESTful API endpoints for MFA operations:

**TOTP Endpoints:**
- `POST /api/v1/auth/mfa/totp/setup` - Initialize TOTP setup, returns secret and QR code
- `POST /api/v1/auth/mfa/totp/verify` - Verify TOTP code to complete setup

**SMS Endpoints:**
- `POST /api/v1/auth/mfa/sms/setup` - Send SMS OTP to phone number
- `POST /api/v1/auth/mfa/sms/verify` - Verify SMS OTP code

**Email Endpoints:**
- `POST /api/v1/auth/mfa/email/setup` - Send Email OTP
- `POST /api/v1/auth/mfa/email/verify` - Verify Email OTP code

**Backup Codes Endpoints:**
- `POST /api/v1/auth/mfa/backup-codes/generate` - Generate new backup codes
- `POST /api/v1/auth/mfa/backup-codes/verify` - Verify a backup code

**Management Endpoints:**
- `GET /api/v1/auth/mfa/status` - Get current MFA configuration
- `POST /api/v1/auth/mfa/disable` - Disable MFA (requires password)

#### 3. Data Models (`backend/models/user.py`)

Pydantic models for request/response validation:
- `MFASetupRequest` - Request to setup MFA
- `MFAVerifyRequest` - Request to verify MFA code
- User models include `mfa_enabled` field

## Configuration

### Environment Variables

Required for SMS (Twilio):
```bash
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

Required for Email (SendGrid):
```bash
SENDGRID_API_KEY=your_api_key
SENDGRID_FROM_EMAIL=noreply@omni-ultra.com
```

Optional:
```bash
OTP_EXPIRY_MINUTES=5  # Default: 5 minutes
```

## Usage Examples

### 1. Setting up TOTP (Authenticator App)

**Step 1: Initialize TOTP Setup**
```bash
POST /api/v1/auth/mfa/totp/setup
Authorization: Bearer <access_token>
```

Response:
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code_uri": "otpauth://totp/OMNI%20Platform:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=OMNI%20Platform",
  "backup_codes": [
    "abc12345",
    "def67890",
    ...
  ]
}
```

**Step 2: User scans QR code with authenticator app**

**Step 3: Verify TOTP code**
```bash
POST /api/v1/auth/mfa/totp/verify
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "secret": "JBSWY3DPEHPK3PXP",
  "code": "123456"
}
```

### 2. Setting up SMS OTP

**Step 1: Send SMS**
```bash
POST /api/v1/auth/mfa/sms/setup
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "phone_number": "+1234567890"
}
```

**Step 2: Verify Code**
```bash
POST /api/v1/auth/mfa/sms/verify
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "phone_number": "+1234567890",
  "code": "123456"
}
```

### 3. Setting up Email OTP

**Step 1: Send Email**
```bash
POST /api/v1/auth/mfa/email/setup
Authorization: Bearer <access_token>
```

**Step 2: Verify Code**
```bash
POST /api/v1/auth/mfa/email/verify
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "code": "123456"
}
```

### 4. Using Backup Codes

**Generate codes:**
```bash
POST /api/v1/auth/mfa/backup-codes/generate
Authorization: Bearer <access_token>
```

**Verify a backup code:**
```bash
POST /api/v1/auth/mfa/backup-codes/verify
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "code": "abc12345"
}
```

## Security Considerations

### 1. TOTP Security
- Uses standard TOTP algorithm (RFC 6238)
- 30-second time windows with ±1 window tolerance
- Secrets are Base32-encoded for QR code compatibility
- Supports standard authenticator apps

### 2. OTP Security
- 6-digit numeric codes for ease of entry
- Configurable expiry (default 5 minutes)
- One-time use (should be invalidated after verification)
- Uses cryptographically secure random generation

### 3. Backup Codes Security
- 8-character hexadecimal codes
- Hashed using bcrypt before storage
- Each code is single-use only
- Should be regenerated periodically

### 4. Communication Security
- SMS via Twilio (encrypted in transit)
- Email via SendGrid (TLS encrypted)
- All API endpoints require authentication
- Rate limiting should be applied to prevent abuse

## Database Schema Recommendations

To fully implement MFA, add the following fields to your user table:

```sql
-- User MFA configuration
mfa_enabled BOOLEAN DEFAULT FALSE,
mfa_method VARCHAR(20), -- 'totp', 'sms', 'email', or 'multiple'

-- TOTP data
totp_secret VARCHAR(255), -- encrypted
totp_enabled BOOLEAN DEFAULT FALSE,

-- SMS data
sms_phone VARCHAR(20),
sms_enabled BOOLEAN DEFAULT FALSE,

-- Email MFA data
email_mfa_enabled BOOLEAN DEFAULT FALSE,

-- Backup codes (separate table recommended)
CREATE TABLE mfa_backup_codes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    code_hash VARCHAR(255),
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    used_at TIMESTAMP
);

-- OTP verification attempts (for rate limiting)
CREATE TABLE mfa_otp_attempts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    method VARCHAR(20),
    code_sent VARCHAR(10), -- encrypted or hashed
    expires_at TIMESTAMP,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Testing

### Unit Tests

Run MFA service tests:
```bash
cd backend
pytest tests/test_mfa_service.py -v
```

Test coverage:
- 23 comprehensive tests
- Tests for TOTP generation and verification
- Tests for SMS/Email OTP generation
- Tests for backup code generation and verification
- Tests for OTP expiry logic

### Integration Testing

Use the validation script:
```bash
python /tmp/validate_mfa.py
```

## Production Deployment Checklist

- [ ] Configure Twilio credentials for SMS
- [ ] Configure SendGrid credentials for Email
- [ ] Set up database schema for MFA data
- [ ] Implement rate limiting on MFA endpoints
- [ ] Add audit logging for MFA operations
- [ ] Configure OTP expiry times
- [ ] Test all MFA methods end-to-end
- [ ] Document MFA setup process for users
- [ ] Implement backup code regeneration workflow
- [ ] Set up monitoring for MFA success/failure rates
- [ ] Configure alerts for unusual MFA patterns
- [ ] Test recovery flows for lost devices

## Future Enhancements

1. **WebAuthn/FIDO2 Support** - Hardware security keys
2. **Push Notifications** - Mobile app push for approval
3. **Biometric Authentication** - Fingerprint, Face ID integration
4. **Risk-Based Authentication** - Adaptive MFA based on login context
5. **MFA Session Management** - Remember trusted devices
6. **Multi-method MFA** - Require multiple factors simultaneously
7. **Admin Override** - Emergency MFA bypass with audit trail
8. **User Activity Dashboard** - Show MFA usage patterns

## Support

For issues or questions about the MFA implementation:
1. Review the test cases in `backend/tests/test_mfa_service.py`
2. Check the service implementation in `backend/services/mfa_service.py`
3. Verify environment variables are configured correctly
4. Check logs for error messages from Twilio or SendGrid

## References

- [RFC 6238 - TOTP Algorithm](https://tools.ietf.org/html/rfc6238)
- [PyOTP Documentation](https://pyauth.github.io/pyotp/)
- [Twilio Python SDK](https://www.twilio.com/docs/libraries/python)
- [SendGrid Python SDK](https://github.com/sendgrid/sendgrid-python)
