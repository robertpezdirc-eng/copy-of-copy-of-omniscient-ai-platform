"""
Tests for MFA Routes
"""

import pytest
from fastapi.testclient import TestClient


def test_mfa_setup_totp(client):
    """Test TOTP MFA setup"""
    response = client.post("/api/mfa/setup", json={
        "user_id": "test_user_mfa",
        "method": "totp"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["method"] == "totp"
    assert "secret" in data
    assert "qr_code_url" in data
    assert "backup_codes" in data
    assert len(data["backup_codes"]) == 10


def test_mfa_setup_sms(client):
    """Test SMS MFA setup"""
    response = client.post("/api/mfa/setup", json={
        "user_id": "test_user_sms",
        "method": "sms",
        "phone_number": "+1234567890"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["method"] == "sms"


def test_mfa_setup_email(client):
    """Test Email MFA setup"""
    response = client.post("/api/mfa/setup", json={
        "user_id": "test_user_email",
        "method": "email",
        "email": "test@example.com"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["method"] == "email"


def test_mfa_verify_invalid_code(client):
    """Test MFA verification with invalid code"""
    # Setup first
    setup_resp = client.post("/api/mfa/setup", json={
        "user_id": "test_verify_user",
        "method": "totp"
    })
    
    # Try to verify with wrong code
    response = client.post("/api/mfa/verify", json={
        "user_id": "test_verify_user",
        "method": "totp",
        "code": "000000"
    })
    
    assert response.status_code == 401


def test_mfa_status(client):
    """Test MFA status check"""
    # Setup MFA first
    client.post("/api/mfa/setup", json={
        "user_id": "status_test_user",
        "method": "totp"
    })
    
    # Check status
    response = client.get("/api/mfa/status/status_test_user")
    
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "mfa_enabled" in data


def test_mfa_regenerate_backup_codes(client):
    """Test backup code regeneration"""
    # Setup MFA first
    client.post("/api/mfa/setup", json={
        "user_id": "backup_test_user",
        "method": "totp"
    })
    
    # Regenerate codes
    response = client.post("/api/mfa/regenerate-backup-codes/backup_test_user")
    
    assert response.status_code == 200
    data = response.json()
    assert "backup_codes" in data
    assert len(data["backup_codes"]) == 10


def test_mfa_send_code_sms(client):
    """Test sending SMS code"""
    # Setup SMS MFA first
    client.post("/api/mfa/setup", json={
        "user_id": "send_code_user",
        "method": "sms",
        "phone_number": "+1234567890"
    })
    
    # Request code
    response = client.post("/api/mfa/send-code", json={
        "user_id": "send_code_user",
        "method": "sms"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True


# Run with: pytest tests/test_mfa.py -v
