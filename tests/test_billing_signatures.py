import os
import sys
import json
import time
import hmac
import hashlib
from fastapi.testclient import TestClient

# Ensure backend is importable
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'omni-platform', 'backend'))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from main import app  # type: ignore

client = TestClient(app)

API_KEY = "test-key"
os.environ["API_KEY"] = API_KEY


def _create_subscription(tenant: str = "sigtenant", plan: str = "starter"):
    res = client.post(
        "/api/v1/billing/saas/subscriptions",
        json={"tenant_id": tenant, "plan": plan},
        headers={"X-API-Key": API_KEY},
    )
    assert res.status_code == 200, res.text
    return res.json()["subscription"]["id"]


def test_stripe_signature_valid_and_idempotent():
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
    os.environ["STRIPE_TOLERANCE"] = "300"
    sid = _create_subscription("tenant_stripe")
    body = {"type": "payment_intent.succeeded", "subscription_id": sid, "id": "evt_sig_1"}
    body_str = json.dumps(body, separators=(",", ":"))
    t = int(time.time())
    signed_payload = f"{t}.{body_str}".encode("utf-8")
    sig = hmac.new(os.environ["STRIPE_WEBHOOK_SECRET"].encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    headers = {"Stripe-Signature": f"t={t},v1={sig}"}
    res = client.post("/api/v1/billing/saas/payments/stripe/webhook", data=body_str, headers=headers)
    assert res.status_code == 200, res.text
    j = res.json()
    assert j.get("updated") is True
    # Idempotent repeat
    res2 = client.post("/api/v1/billing/saas/payments/stripe/webhook", data=body_str, headers=headers)
    assert res2.status_code == 200
    j2 = res2.json()
    assert j2.get("idempotent") is True


def test_stripe_signature_timestamp_tolerance():
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
    os.environ["STRIPE_TOLERANCE"] = "10"
    sid = _create_subscription("tenant_stripe_tol")
    body = {"type": "payment_intent.succeeded", "subscription_id": sid, "id": "evt_sig_2"}
    body_str = json.dumps(body, separators=(",", ":"))
    t = int(time.time()) - 1000  # exceed tolerance
    signed_payload = f"{t}.{body_str}".encode("utf-8")
    sig = hmac.new(os.environ["STRIPE_WEBHOOK_SECRET"].encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    headers = {"Stripe-Signature": f"t={t},v1={sig}"}
    res = client.post("/api/v1/billing/saas/payments/stripe/webhook", data=body_str, headers=headers)
    assert res.status_code == 400


def test_paypal_hmac_signature_completed():
    os.environ["PAYPAL_VERIFY_MODE"] = "hmac"
    os.environ["PAYPAL_WEBHOOK_SECRET"] = "ppsec_test"
    sid = _create_subscription("tenant_paypal")
    body = {"event_type": "PAYMENT.CAPTURE.COMPLETED", "subscription_id": sid, "id": "evt_pp_1"}
    body_str = json.dumps(body, separators=(",", ":"))
    sig = hmac.new(os.environ["PAYPAL_WEBHOOK_SECRET"].encode("utf-8"), body_str.encode("utf-8"), hashlib.sha256).hexdigest()
    headers = {"Transmission-Sig": sig}
    res = client.post("/api/v1/billing/saas/payments/paypal/webhook", data=body_str, headers=headers)
    assert res.status_code == 200, res.text
    assert res.json().get("updated") is True


def test_api_key_enforcement_on_internal_endpoints():
    # list_subscriptions requires API key
    res1 = client.get("/api/v1/billing/saas/subscriptions")
    assert res1.status_code == 401
    # track_usage requires API key
    res2 = client.post("/api/v1/billing/usage/tenantX/track", json={"tasks": 1})
    assert res2.status_code == 401
    # stripe intent requires API key
    sid = _create_subscription("tenant_intent")
    res3 = client.post("/api/v1/billing/saas/payments/stripe/intent", json={"tenant_id": "tenant_intent", "amount": 100, "currency": "USD", "subscription_id": sid})
    assert res3.status_code == 401
    res3b = client.post("/api/v1/billing/saas/payments/stripe/intent", json={"tenant_id": "tenant_intent", "amount": 100, "currency": "USD", "subscription_id": sid}, headers={"X-API-Key": API_KEY})
    assert res3b.status_code == 200