from payment_gateways.acmepay import AcmePayGateway


class DummyResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise Exception(f"HTTP {self.status_code}")

    def json(self):
        return self._json


def test_acmepay_authorize_and_capture(monkeypatch):
    def fake_post(url, json, headers, timeout):
        if url.endswith("/authorize"):
            return DummyResponse({"transaction_id": "tx_123", "status": "authorized"})
        if url.endswith("/capture"):
            return DummyResponse({"transaction_id": "tx_123", "status": "captured"})
        return DummyResponse({}, status_code=404)

    # Patch requests.post used within gateway
    import requests

    monkeypatch.setattr(requests, "post", fake_post)

    gw = AcmePayGateway(api_key="test-key")
    auth = gw.authorize(10.0, "USD", {"order_id": "o-1"})
    assert auth["status"] == "authorized"
    assert auth["transaction_id"] == "tx_123"

    cap = gw.capture("tx_123", 10.0)
    assert cap["status"] == "captured"
    assert cap["transaction_id"] == "tx_123"
