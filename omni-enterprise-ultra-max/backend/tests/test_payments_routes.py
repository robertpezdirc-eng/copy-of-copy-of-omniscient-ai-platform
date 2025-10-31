import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from main import app
from routes import payments

# Positional argument for TestClient
client = TestClient(app)


def test_authorize_route():
    # Mock the gateway at the module level
    mock_gw = MagicMock()
    mock_gw.authorize.return_value = {"transaction_id": "tx_1", "status": "authorized"}
    
    # Replace the dependency
    original_get_gateway = payments.get_gateway
    payments.get_gateway = lambda: mock_gw
    
    try:
        resp = client.post(
            "/api/payments/authorize",
            json={"amount": 5.0, "currency": "EUR", "metadata": {"k": "v"}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "authorized"
        assert data["transaction_id"] == "tx_1"
    finally:
        # Restore original
        payments.get_gateway = original_get_gateway


def test_capture_route():
    # Mock the gateway at the module level
    mock_gw = MagicMock()
    mock_gw.capture.return_value = {"transaction_id": "tx_1", "status": "captured"}
    
    # Replace the dependency
    original_get_gateway = payments.get_gateway
    payments.get_gateway = lambda: mock_gw
    
    try:
        resp = client.post(
            "/api/payments/capture",
            json={"transaction_id": "tx_1", "amount": 5.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "captured"
        assert data["transaction_id"] == "tx_1"
    finally:
        # Restore original
        payments.get_gateway = original_get_gateway
