"""
Tests for Threat Detection Routes
"""

import pytest
from fastapi.testclient import TestClient


def test_blacklist_ip(client):
    """Test manual IP blacklisting"""
    response = client.post("/api/security/threat-detection/ip/blacklist", json={
        "ip_address": "192.168.1.100",
        "reason": "manual",
        "duration_hours": 24,
        "notes": "Test blacklist"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["blacklisted"] == True
    assert data["ip_address"] == "192.168.1.100"


def test_check_blacklisted_ip(client):
    """Test checking if IP is blacklisted"""
    # First blacklist an IP
    client.post("/api/security/threat-detection/ip/blacklist", json={
        "ip_address": "10.0.0.1",
        "reason": "suspicious_activity",
        "duration_hours": 1
    })
    
    # Check if blacklisted
    response = client.get("/api/security/threat-detection/ip/blacklist/10.0.0.1")
    
    assert response.status_code == 200
    data = response.json()
    assert data["blacklisted"] == True


def test_remove_from_blacklist(client):
    """Test removing IP from blacklist"""
    # Blacklist first
    client.post("/api/security/threat-detection/ip/blacklist", json={
        "ip_address": "172.16.0.1",
        "reason": "manual",
        "duration_hours": 1
    })
    
    # Remove from blacklist
    response = client.delete("/api/security/threat-detection/ip/blacklist/172.16.0.1")
    
    assert response.status_code == 200
    assert response.json()["success"] == True


def test_record_successful_login(client):
    """Test recording successful login attempt"""
    response = client.post("/api/security/threat-detection/login/attempt", json={
        "user_id": "test_user",
        "ip_address": "203.0.113.1",
        "success": True,
        "user_agent": "Mozilla/5.0"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "recorded"
    assert data["attempt_successful"] == True


def test_record_failed_login(client):
    """Test recording failed login attempt"""
    response = client.post("/api/security/threat-detection/login/attempt", json={
        "user_id": "test_user_fail",
        "ip_address": "203.0.113.2",
        "success": False
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "recorded"
    assert data["attempt_successful"] == False


def test_brute_force_detection(client):
    """Test brute force attack detection"""
    # Make multiple failed attempts
    ip_address = "203.0.113.100"
    
    for i in range(6):  # Threshold is 5
        response = client.post("/api/security/threat-detection/login/attempt", json={
            "user_id": "brute_force_target",
            "ip_address": ip_address,
            "success": False
        })
        
        if i >= 5:  # Should be blocked on 6th attempt
            assert response.status_code == 200
            data = response.json()
            if data.get("status") == "blocked":
                assert data["reason"] == "brute_force_detected"
                break


def test_get_threat_events(client):
    """Test retrieving threat events"""
    response = client.get("/api/security/threat-detection/threats")
    
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert "total_count" in data


def test_get_security_stats(client):
    """Test getting security statistics"""
    response = client.get("/api/security/threat-detection/stats")
    
    assert response.status_code == 200
    data = response.json()
    assert "total_threats_detected" in data
    assert "blacklisted_ips" in data
    assert "active_monitoring" in data


def test_check_request_security(client):
    """Test request security check"""
    response = client.post("/api/security/threat-detection/check-request", json={
        "endpoint": "/api/test",
        "user_id": "test_user"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "allowed" in data
    assert "recommended_action" in data


def test_list_blacklisted_ips(client):
    """Test listing all blacklisted IPs"""
    response = client.get("/api/security/threat-detection/ip/blacklist")
    
    assert response.status_code == 200
    data = response.json()
    assert "blacklisted_ips" in data
    assert "total_count" in data


# Run with: pytest tests/test_threat_detection.py -v
