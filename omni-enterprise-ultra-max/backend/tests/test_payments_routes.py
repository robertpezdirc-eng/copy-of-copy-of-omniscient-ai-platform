import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from unittest.mock import MagicMock

# Set environment variable before importing main
os.environ["PAYMENT_ACME_API_KEY"] = "test_key_123"

from main import app
from routes import payments

# Positional argument for TestClient
client = TestClient(app)


def test_authorize_route():
    # Create a mock gateway
    mock_gw = MagicMock()
    mock_gw.authorize.return_value = {"transaction_id": "tx_1", "status": "authorized"}

    # Override the dependency directly
    app.dependency_overrides[payments.get_gateway] = lambda: mock_gw

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
        # Clear the override
        app.dependency_overrides.clear()


def test_capture_route():
    # Create a mock gateway
    mock_gw = MagicMock()
    mock_gw.capture.return_value = {"transaction_id": "tx_1", "status": "captured"}

    # Override the dependency directly
    app.dependency_overrides[payments.get_gateway] = lambda: mock_gw

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
        # Clear the override
        app.dependency_overrides.clear()
