"""
Tests for Enhanced GDPR Routes
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime


def test_gdpr_export_json(client):
    """Test data export in JSON format"""
    response = client.post("/api/gdpr/export", json={
        "user_id": "test_user_123",
        "format": "json"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "export_id" in data
    assert data["user_id"] == "test_user_123"
    assert data["format"] == "json"
    assert data["status"] == "completed"


def test_gdpr_export_csv(client):
    """Test data export in CSV format"""
    response = client.post("/api/gdpr/export", json={
        "user_id": "test_user_456",
        "format": "csv"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "csv"


def test_gdpr_delete_data(client):
    """Test data deletion request"""
    response = client.post("/api/gdpr/delete", json={
        "user_id": "test_user_789",
        "reason": "User request",
        "hard_delete": False
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "test_user_789"
    assert data["status"] == "pending"
    assert "deletion_id" in data


def test_gdpr_consent_grant(client):
    """Test granting consent"""
    response = client.post("/api/gdpr/consent", json={
        "user_id": "test_user_consent",
        "consent_type": "marketing",
        "granted": True,
        "purpose": "Email marketing campaigns"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["granted"] == True
    assert data["consent_type"] == "marketing"


def test_gdpr_consent_withdraw(client):
    """Test withdrawing consent"""
    # First grant consent
    client.post("/api/gdpr/consent", json={
        "user_id": "test_user_withdraw",
        "consent_type": "analytics",
        "granted": True,
        "purpose": "Usage analytics"
    })
    
    # Then withdraw
    response = client.post("/api/gdpr/consent", json={
        "user_id": "test_user_withdraw",
        "consent_type": "analytics",
        "granted": False,
        "purpose": "Withdrawing consent"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["granted"] == False


def test_gdpr_audit_log(client):
    """Test audit log retrieval"""
    # Generate some activity
    client.post("/api/gdpr/consent", json={
        "user_id": "audit_test_user",
        "consent_type": "marketing",
        "granted": True,
        "purpose": "Test"
    })
    
    # Get audit log
    response = client.get("/api/gdpr/audit?user_id=audit_test_user")
    
    assert response.status_code == 200
    data = response.json()
    assert "entries" in data
    assert "total_count" in data


def test_gdpr_compliance_status(client):
    """Test compliance status endpoint"""
    response = client.get("/api/gdpr/compliance/status")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "statistics" in data
    assert "features" in data


# Run with: pytest tests/test_gdpr_enhanced.py -v
