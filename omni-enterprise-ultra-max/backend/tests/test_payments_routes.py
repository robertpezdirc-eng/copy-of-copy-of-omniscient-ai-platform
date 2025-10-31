import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from main import app

# Positional argument for TestClient
client = TestClient(app)


def test_authorize_route():
    # Set environment variable to allow AcmePayGateway to instantiate
    os.environ["PAYMENT_ACME_API_KEY"] = "test_key_123"
    
    mock_gw = MagicMock()
    mock_gw.authorize.return_value = {"transaction_id": "tx_1", "status": "authorized"}
    with patch("routes.payments.get_gateway", return_value=mock_gw):
        resp = client.post(
            "/api/payments/authorize",
            json={"amount": 5.0, "currency": "EUR", "metadata": {"k": "v"}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "authorized"
        assert data["transaction_id"] == "tx_1"


def test_capture_route():
    # Set environment variable to allow AcmePayGateway to instantiate
    os.environ["PAYMENT_ACME_API_KEY"] = "test_key_123"
    
    mock_gw = MagicMock()
    mock_gw.capture.return_value = {"transaction_id": "tx_1", "status": "captured"}
    with patch("routes.payments.get_gateway", return_value=mock_gw):
        resp = client.post(
            "/api/payments/capture",
            json={"transaction_id": "tx_1", "amount": 5.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "captured"
        assert data["transaction_id"] == "tx_1"
