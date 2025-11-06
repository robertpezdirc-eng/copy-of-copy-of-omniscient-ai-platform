import os
from typing import Any, Dict

import requests

from .base import PaymentGateway


class AcmePayGateway(PaymentGateway):
    API_BASE = "https://api.acmepay.test/v1"

    def __init__(self, api_key: str | None = None, timeout: int = 10):
        self.api_key = api_key or os.getenv("PAYMENT_ACME_API_KEY")
        if not self.api_key:
            raise RuntimeError("PAYMENT_ACME_API_KEY environment variable is not set")
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def authorize(self, amount: float, currency: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"amount": amount, "currency": currency, "metadata": metadata}
        resp = requests.post(
            f"{self.API_BASE}/authorize",
            json=payload,
            headers=self.headers,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def capture(self, transaction_id: str, amount: float) -> Dict[str, Any]:
        payload = {"transaction_id": transaction_id, "amount": amount}
        resp = requests.post(
            f"{self.API_BASE}/capture",
            json=payload,
            headers=self.headers,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()
