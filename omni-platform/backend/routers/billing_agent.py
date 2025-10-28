import os
import json
import time
import uuid
import hmac
import hashlib
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, Header, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/billing", tags=["billing"])

class CreateSubscriptionBody(BaseModel):
    tenant_id: str
    plan: Optional[str] = "starter"
    status: Optional[str] = "active"
    meta: Optional[Dict[str, Any]] = {}

class StripeIntentBody(BaseModel):
    tenant_id: str
    amount: float
    currency: Optional[str] = "USD"
    subscription_id: Optional[str] = None

class PayPalOrderBody(BaseModel):
    tenant_id: str
    amount: float
    currency: Optional[str] = "USD"
    subscription_id: Optional[str] = None

from routers.access_controller import require_api_key

@router.get("/health")
def billing_health() -> Dict[str, Any]:
    ready = True
    try:
        _ensure_store()
    except Exception:
        ready = False
    return {"ok": True, "store_ready": ready}

STORE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
USAGE_FILE = os.path.join(STORE_DIR, "usage_store.json")
SUBS_FILE = os.path.join(STORE_DIR, "subscriptions_store.json")
CATALOG_FILE = os.path.join(STORE_DIR, "billing_catalog.json")


def _ensure_store():
    os.makedirs(STORE_DIR, exist_ok=True)
    for path in (USAGE_FILE, SUBS_FILE, CATALOG_FILE):
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump({}, f)


def _load_json(path: str) -> Dict[str, Any]:
    _ensure_store()
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _save_json(path: str, data: Dict[str, Any]):
    _ensure_store()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


@router.get("/usage/{tenant_id}")
def get_usage(tenant_id: str) -> Dict[str, Any]:
    usage = _load_json(USAGE_FILE)
    summary = usage.get(tenant_id) or {
        "prompt_tokens": 0,
        "output_tokens": 0,
        "tasks": 0,
        "duration_ms": 0,
        "last_update": None,
        "entries": [],
    }
    return {"tenant_id": tenant_id, "usage": summary}


@router.post("/usage/{tenant_id}/track")
def track_usage(tenant_id: str, payload: Dict[str, Any], _: None = Depends(require_api_key)) -> Dict[str, Any]:
    usage = _load_json(USAGE_FILE)
    entry = {
        "id": uuid.uuid4().hex,
        "ts": int(time.time() * 1000),
        "prompt_tokens": int(payload.get("prompt_tokens", 0)),
        "output_tokens": int(payload.get("output_tokens", 0)),
        "tasks": int(payload.get("tasks", 0)),
        "duration_ms": int(payload.get("duration_ms", 0)),
        "meta": payload.get("meta") or {},
    }
    agg = usage.get(tenant_id) or {
        "prompt_tokens": 0,
        "output_tokens": 0,
        "tasks": 0,
        "duration_ms": 0,
        "last_update": None,
        "entries": [],
    }
    agg["prompt_tokens"] += entry["prompt_tokens"]
    agg["output_tokens"] += entry["output_tokens"]
    agg["tasks"] += entry["tasks"]
    agg["duration_ms"] += entry["duration_ms"]
    agg["last_update"] = entry["ts"]
    agg["entries"].append(entry)
    usage[tenant_id] = agg
    _save_json(USAGE_FILE, usage)
    return {"tracked": True, "entry": entry, "summary": agg}


@router.get("/saas/subscriptions")
def list_subscriptions(_: None = Depends(require_api_key)) -> Dict[str, Any]:
    subs = _load_json(SUBS_FILE)
    return {"count": len(subs), "items": list(subs.values())}


@router.post("/saas/subscriptions")
def create_subscription(body: CreateSubscriptionBody, _: None = Depends(require_api_key)) -> Dict[str, Any]:
    payload = body.dict()
    tenant_id = payload.get("tenant_id")
    plan = payload.get("plan") or "starter"
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    subs = _load_json(SUBS_FILE)
    sid = uuid.uuid4().hex
    item = {
        "id": sid,
        "tenant_id": tenant_id,
        "plan": plan,
        "status": payload.get("status", "active"),
        "created_at": int(time.time() * 1000),
        "meta": payload.get("meta") or {},
    }
    subs[sid] = item
    _save_json(SUBS_FILE, subs)
    return {"created": True, "subscription": item}


@router.post("/saas/subscriptions/{sid}/update")
def update_subscription(sid: str, payload: Dict[str, Any], _: None = Depends(require_api_key)) -> Dict[str, Any]:
    subs = _load_json(SUBS_FILE)
    if sid not in subs:
        raise HTTPException(status_code=404, detail="subscription not found")
    item = subs[sid]
    if "plan" in payload:
        item["plan"] = payload["plan"]
    if "status" in payload:
        item["status"] = payload["status"]
    item["meta"] = payload.get("meta", item.get("meta") or {})
    item["updated_at"] = int(time.time() * 1000)
    subs[sid] = item
    _save_json(SUBS_FILE, subs)
    return {"updated": True, "subscription": item}


@router.get("/saas/subscriptions/by-tenant/{tenant_id}")
def get_subscription_by_tenant(tenant_id: str) -> Dict[str, Any]:
    subs = _load_json(SUBS_FILE)
    for s in subs.values():
        if s.get("tenant_id") == tenant_id:
            return {"found": True, "subscription": s}
    return {"found": False}

# ---- Billing catalog endpoints ----

@router.get("/catalog")
def list_catalog(_: None = Depends(require_api_key)) -> Dict[str, Any]:
    catalog = _load_json(CATALOG_FILE)
    items = list(catalog.values())
    return {"count": len(items), "items": items}

@router.post("/catalog/add")
def catalog_add(payload: Dict[str, Any], _: None = Depends(require_api_key)) -> Dict[str, Any]:
    catalog = _load_json(CATALOG_FILE)
    cid = uuid.uuid4().hex
    item = {
        "id": cid,
        "name": payload.get("name") or payload.get("function_name") or "new-api-function",
        "version": str(payload.get("version") or "v1"),
        "price_per_call": float(payload.get("price_per_call") or payload.get("price") or 0.0),
        "currency": str(payload.get("currency") or "USD"),
        "path": payload.get("path") or "/api/v1/unknown",
        "tenant_id": payload.get("tenant_id") or None,
        "description": payload.get("description") or "",
        "created_at": int(time.time() * 1000),
        "meta": payload.get("meta") or {},
    }
    catalog[cid] = item
    _save_json(CATALOG_FILE, catalog)
    return {"created": True, "catalog_item": item}

@router.put("/catalog/{cid}")
def catalog_update(cid: str, payload: Dict[str, Any], _: None = Depends(require_api_key)) -> Dict[str, Any]:
    catalog = _load_json(CATALOG_FILE)
    if cid not in catalog:
        raise HTTPException(status_code=404, detail="catalog item not found")
    item = catalog[cid]
    for key in ["name", "version", "price_per_call", "currency", "path", "tenant_id", "description", "meta"]:
        if key in payload:
            item[key] = payload[key] if key != "price_per_call" else float(payload[key])
    item["updated_at"] = int(time.time() * 1000)
    catalog[cid] = item
    _save_json(CATALOG_FILE, catalog)
    return {"updated": True, "catalog_item": item}

@router.delete("/catalog/{cid}")
def catalog_delete(cid: str, _: None = Depends(require_api_key)) -> Dict[str, Any]:
    catalog = _load_json(CATALOG_FILE)
    if cid not in catalog:
        raise HTTPException(status_code=404, detail="catalog item not found")
    deleted = catalog.pop(cid)
    _save_json(CATALOG_FILE, catalog)
    return {"deleted": True, "catalog_item": deleted}

# ---- Payment gateway stubs (Stripe / PayPal) ----

def _retry(callable_fn, attempts: int = 3, base_delay: float = 0.5) -> bool:
    for i in range(attempts):
        try:
            if callable_fn():
                return True
        except Exception:
            pass
        time.sleep(base_delay * (2 ** i))
    return False

def _notify_slack(kind: str, payload: Dict[str, Any]) -> bool:
    import requests  # type: ignore
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        return False
    text = (
        f"Payment {kind}: tenant={payload.get('tenant_id')} gateway={payload.get('gateway')} "
        f"amount={payload.get('amount')} currency={payload.get('currency')} subscription={payload.get('subscription_id')}"
    )
    def once():
        r = requests.post(url, json={"text": text, "mrkdwn": True}, timeout=5)
        return r.status_code < 300
    return _retry(once)

def _notify_email(kind: str, payload: Dict[str, Any]) -> bool:
    import smtplib
    from email.mime.text import MIMEText
    host = os.environ.get("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASS")
    sender = os.environ.get("SMTP_FROM") or user
    to = os.environ.get("NOTIFY_EMAIL_TO")
    if not (host and sender and to):
        return False
    body = (
        f"Payment {kind}\n"
        f"Tenant: {payload.get('tenant_id')}\n"
        f"Gateway: {payload.get('gateway')}\n"
        f"Amount: {payload.get('amount')} {payload.get('currency')}\n"
        f"Subscription: {payload.get('subscription_id')}\n"
    )
    msg = MIMEText(body)
    msg["Subject"] = f"[Billing] Payment {kind}"
    msg["From"] = sender
    msg["To"] = to
    def once():
        with smtplib.SMTP(host, port, timeout=5) as smtp:
            if os.environ.get("SMTP_TLS", "1") != "0":
                smtp.starttls()
            if user and password:
                smtp.login(user, password)
            smtp.sendmail(sender, [to], msg.as_string())
        return True
    return _retry(once)

def _notify_payment_event(kind: str, payload: Dict[str, Any]) -> bool:
    ok = True
    try:
        if os.environ.get("SLACK_WEBHOOK_URL"):
            ok = _notify_slack(kind, payload) and ok
        if os.environ.get("SMTP_HOST") and os.environ.get("NOTIFY_EMAIL_TO"):
            ok = _notify_email(kind, payload) and ok
        if os.environ.get("NOTIFY_LOCAL_FORWARD") == "1":
            import requests  # type: ignore
            port = int(os.environ.get("PORT", "8002"))
            base = f"http://localhost:{port}/api/v1/notifications/events"
            url = f"{base}/payment-{kind}"
            r = requests.post(url, json=payload, timeout=5)
            ok = (r.status_code < 300) and ok
    except Exception:
        return False
    return ok

# Signature verification helpers (stubbed)

def _hmac_hex(secret: str, raw: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()

def _verify_stripe_signature(raw_body: bytes, headers: Dict[str, str]) -> bool:
    """Verify Stripe webhook signature per spec:
    - Header: Stripe-Signature: t=timestamp,v1=signature
    - Signed payload: f"{t}.{raw_body}" using webhook secret and HMAC-SHA256
    - Enforce timestamp tolerance (default 300s)
    """
    secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    if not secret:
        return True
    sig_header = headers.get("Stripe-Signature") or headers.get("stripe-signature")
    if not sig_header:
        return False
    parts: Dict[str, str] = {}
    for p in sig_header.split(","):
        k, _, v = p.partition("=")
        parts[k.strip()] = v.strip()
    t = parts.get("t")
    v1 = parts.get("v1")
    if not t or not v1:
        return False
    try:
        ts = int(t)
    except ValueError:
        return False
    tolerance = int(os.environ.get("STRIPE_TOLERANCE", "300"))
    if abs(int(time.time()) - ts) > tolerance:
        return False
    body_str = raw_body.decode("utf-8")
    signed_payload = f"{t}.{body_str}".encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, v1)

def _paypal_remote_verify(raw_body: bytes, headers: Dict[str, str]) -> bool:
    try:
        import requests  # type: ignore
        env = os.environ.get("PAYPAL_ENV", "sandbox").lower()
        base = "https://api-m.paypal.com" if env == "live" else "https://api-m.sandbox.paypal.com"
        client_id = os.environ.get("PAYPAL_CLIENT_ID")
        client_secret = os.environ.get("PAYPAL_CLIENT_SECRET")
        webhook_id = os.environ.get("PAYPAL_WEBHOOK_ID")
        if not (client_id and client_secret and webhook_id):
            return False
        r = requests.post(base + "/v1/oauth2/token", auth=(client_id, client_secret), data={"grant_type": "client_credentials"}, timeout=5)
        if r.status_code >= 300:
            return False
        token = r.json().get("access_token")
        if not token:
            return False
        body_str = raw_body.decode("utf-8")
        payload = {
            "transmission_id": headers.get("Transmission-Id") or headers.get("transmission-id"),
            "transmission_time": headers.get("Transmission-Time") or headers.get("transmission-time"),
            "cert_url": headers.get("Cert-Url") or headers.get("cert-url"),
            "auth_algo": headers.get("Auth-Algo") or headers.get("auth-algo"),
            "transmission_sig": headers.get("Transmission-Sig") or headers.get("transmission-sig"),
            "webhook_id": webhook_id,
            "webhook_event": json.loads(body_str),
        }
        vr = requests.post(base + "/v1/notifications/verify-webhook-signature", headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"}, json=payload, timeout=5)
        return vr.status_code < 300 and vr.json().get("verification_status") == "SUCCESS"
    except Exception:
        return False

def _verify_paypal_signature(raw_body: bytes, headers: Dict[str, str]) -> bool:
    mode = os.environ.get("PAYPAL_VERIFY_MODE", "hmac").lower()
    if mode == "remote":
        ok = _paypal_remote_verify(raw_body, headers)
        if isinstance(ok, bool):
            return ok
    secret = os.environ.get("PAYPAL_WEBHOOK_SECRET")
    if not secret:
        return True
    sig = headers.get("Transmission-Sig") or headers.get("transmission-sig")
    if not sig:
        return False
    calc = _hmac_hex(secret, raw_body)
    return hmac.compare_digest(calc, sig)

@router.post("/saas/payments/stripe/intent")
def stripe_create_intent(body: StripeIntentBody, _: None = Depends(require_api_key)) -> Dict[str, Any]:
    payload = body.dict()
    tenant_id = payload.get("tenant_id") or "unknown"
    amount = float(payload.get("amount", 0))
    currency = payload.get("currency", "USD")
    subs = _load_json(SUBS_FILE)
    intent_id = "pi_" + uuid.uuid4().hex[:24]
    client_secret = "cs_" + uuid.uuid4().hex[:24]
    sid = payload.get("subscription_id")
    if sid and sid in subs:
        subs[sid]["last_payment"] = {
            "gateway": "stripe",
            "intent_id": intent_id,
            "amount": amount,
            "currency": currency,
            "status": "created",
            "ts": int(time.time()*1000),
        }
        _save_json(SUBS_FILE, subs)
    return {
        "ok": True,
        "gateway": "stripe",
        "intent": {
            "id": intent_id,
            "client_secret": client_secret,
            "amount": amount,
            "currency": currency,
        },
    }

@router.post("/saas/payments/stripe/webhook")
async def stripe_webhook(request: Request) -> Dict[str, Any]:
    raw = await request.body()
    headers = dict(request.headers)
    if not _verify_stripe_signature(raw, headers):
        raise HTTPException(status_code=400, detail="invalid signature")
    try:
        payload: Dict[str, Any] = json.loads(raw.decode("utf-8"))
    except Exception:
        payload = {}
    event = payload.get("type") or "unknown"
    sid = payload.get("subscription_id")
    subs = _load_json(SUBS_FILE)
    updated = False
    notified = False
    if sid and sid in subs:
        item = subs[sid]
        lp = item.get("last_payment") or {}
        event_id = payload.get("event_id") or payload.get("id")
        if event_id and lp.get("last_event_id") == event_id:
            return {"ok": True, "event": event, "updated": False, "notified": False, "idempotent": True}
        if event == "payment_intent.succeeded":
            item["status"] = "active"
            lp["status"] = "succeeded"
            updated = True
            notified = _notify_payment_event("success", {
                "tenant_id": item.get("tenant_id"),
                "subscription_id": sid,
                "gateway": "stripe",
                "amount": lp.get("amount"),
                "currency": lp.get("currency"),
            })
        elif event == "payment_intent.payment_failed":
            item["status"] = "past_due"
            lp["status"] = "failed"
            updated = True
            notified = _notify_payment_event("failed", {
                "tenant_id": item.get("tenant_id"),
                "subscription_id": sid,
                "gateway": "stripe",
            })
        if event_id:
            lp["last_event_id"] = event_id
        item["last_payment"] = lp
        if updated:
            item["updated_at"] = int(time.time()*1000)
            subs[sid] = item
            _save_json(SUBS_FILE, subs)
    return {"ok": True, "event": event, "updated": updated, "notified": notified}

@router.post("/saas/payments/paypal/order")
def paypal_create_order(body: PayPalOrderBody, _: None = Depends(require_api_key)) -> Dict[str, Any]:
    payload = body.dict()
    tenant_id = payload.get("tenant_id") or "unknown"
    amount = float(payload.get("amount", 0))
    currency = payload.get("currency", "USD")
    order_id = "PO-" + uuid.uuid4().hex[:12]
    sid = payload.get("subscription_id")
    subs = _load_json(SUBS_FILE)
    if sid and sid in subs:
        subs[sid]["last_payment"] = {
            "gateway": "paypal",
            "order_id": order_id,
            "amount": amount,
            "currency": currency,
            "status": "created",
            "ts": int(time.time()*1000),
        }
        _save_json(SUBS_FILE, subs)
    return {
        "ok": True,
        "gateway": "paypal",
        "order": {
            "id": order_id,
            "amount": amount,
            "currency": currency,
            "approve_url": f"https://example.paypal.com/checkout/{order_id}",
        },
    }

@router.post("/saas/payments/paypal/webhook")
async def paypal_webhook(request: Request) -> Dict[str, Any]:
    raw = await request.body()
    headers = dict(request.headers)
    if not _verify_paypal_signature(raw, headers):
        raise HTTPException(status_code=400, detail="invalid signature")
    try:
        payload: Dict[str, Any] = json.loads(raw.decode("utf-8"))
    except Exception:
        payload = {}
    event = payload.get("event_type") or "unknown"
    sid = payload.get("subscription_id")
    subs = _load_json(SUBS_FILE)
    updated = False
    notified = False
    if sid and sid in subs:
        item = subs[sid]
        lp = item.get("last_payment") or {}
        event_id = payload.get("event_id") or payload.get("id")
        if event_id and lp.get("last_event_id") == event_id:
            return {"ok": True, "event": event, "updated": False, "notified": False, "idempotent": True}
        if event == "PAYMENT.CAPTURE.COMPLETED":
            item["status"] = "active"
            lp["status"] = "succeeded"
            updated = True
            notified = _notify_payment_event("success", {
                "tenant_id": item.get("tenant_id"),
                "subscription_id": sid,
                "gateway": "paypal",
                "amount": lp.get("amount"),
                "currency": lp.get("currency"),
            })
        elif event == "PAYMENT.CAPTURE.DENIED":
            item["status"] = "past_due"
            lp["status"] = "failed"
            updated = True
            notified = _notify_payment_event("failed", {
                "tenant_id": item.get("tenant_id"),
                "subscription_id": sid,
                "gateway": "paypal",
            })
        if event_id:
            lp["last_event_id"] = event_id
        item["last_payment"] = lp
        if updated:
            item["updated_at"] = int(time.time()*1000)
            subs[sid] = item
            _save_json(SUBS_FILE, subs)
    return {"ok": True, "event": event, "updated": updated, "notified": notified}


@router.post("/saas/checkout/mock")
def saas_checkout_mock(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Mock SaaS checkout: creates subscription and sends welcome email.
    Body: { email: str, plan: str in [starter, pro, enterprise] }
    """
    # Optional reCAPTCHA gate
    try:
        from utils.recaptcha import verify_token
        if not verify_token(payload.get("recaptchaToken")):
            raise HTTPException(status_code=400, detail="recaptcha_failed")
    except HTTPException:
        raise
    except Exception:
        pass

    email = str(payload.get("email") or "").strip()
    plan = str(payload.get("plan") or "starter").lower()
    if plan not in ("starter", "pro", "enterprise"):
        raise HTTPException(status_code=400, detail="invalid plan")
    if not email:
        raise HTTPException(status_code=400, detail="email required")

    # Derive tenant_id
    base = email.split("@")[0] if "@" in email else email
    tenant_id = (base or "tenant") + "-" + uuid.uuid4().hex[:6]

    # Create subscription
    subs = _load_json(SUBS_FILE)
    sid = uuid.uuid4().hex
    session_id = "sess_" + uuid.uuid4().hex[:24]
    item = {
        "id": sid,
        "tenant_id": tenant_id,
        "plan": plan,
        "status": "active",
        "created_at": int(time.time() * 1000),
        "meta": {"email": email, "mock": True, "session_id": session_id},
        "last_payment": {
            "gateway": "stripe-mock",
            "status": "succeeded",
            "amount": {"starter": 29, "pro": 99, "enterprise": 499}.get(plan, 29),
            "currency": "USD",
            "ts": int(time.time() * 1000),
        },
    }
    subs[sid] = item
    _save_json(SUBS_FILE, subs)

    # Send welcome email
    try:
        from utils.emailer import send_template
        dash_url = os.environ.get("DASHBOARD_URL", "https://dashboard.omni.local")
        api_base = os.environ.get("API_BASE_URL", "http://localhost:8080/api/v1")
        send_template(
            to=email,
            subject="Dobrodošli v Omni SaaS",
            template="saas_welcome",
            variables={
                "name": base or email,
                "plan": plan.title(),
                "tenant_id": tenant_id,
                "dashboard_url": dash_url,
                "api_base": api_base,
                "year": str(int(time.strftime("%Y"))),
            }
        )
    except Exception:
        pass

    return {
        "ok": True,
        "checkout": {
            "subscription_id": sid,
            "tenant_id": tenant_id,
            "plan": plan,
            "status": "active",
            "session_id": session_id,
        },
    }

@router.post("/saas/checkout/mock/confirm")
def saas_checkout_mock_confirm(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Confirm a mock checkout session and mark subscription confirmed.
    Body: { session_id: str }
    """
    try:
        from utils.recaptcha import verify_token
        if not verify_token(payload.get("recaptchaToken")):
            raise HTTPException(status_code=400, detail="recaptcha_failed")
    except HTTPException:
        raise
    except Exception:
        pass

    session_id = str(payload.get("session_id") or "").strip()
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    subs = _load_json(SUBS_FILE)
    target_sid = None
    for sid, item in subs.items():
        if (item.get("meta") or {}).get("session_id") == session_id:
            target_sid = sid
            break
    if not target_sid:
        raise HTTPException(status_code=404, detail="session_not_found")

    # Mark as confirmed (no-op for mock, but set flag)
    item = subs[target_sid]
    meta = item.get("meta") or {}
    meta["confirmed"] = True
    item["meta"] = meta
    item["updated_at"] = int(time.time() * 1000)
    subs[target_sid] = item
    _save_json(SUBS_FILE, subs)

    return {"ok": True, "subscription_id": target_sid, "confirmed": True}


# ---- Stripe Checkout (test mode) ----

@router.post("/saas/checkout/stripe/session")
def saas_checkout_stripe_session(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create Stripe Checkout Session (test mode) and return hosted URL.
    Body: { email: str, plan: str in [starter, pro, enterprise] }
    """
    # Optional reCAPTCHA gate
    try:
        from utils.recaptcha import verify_token
        if not verify_token(payload.get("recaptchaToken")):
            raise HTTPException(status_code=400, detail="recaptcha_failed")
    except HTTPException:
        raise
    except Exception:
        pass

    email = str(payload.get("email") or "").strip()
    plan = str(payload.get("plan") or "starter").lower()
    if plan not in ("starter", "pro", "enterprise"):
        raise HTTPException(status_code=400, detail="invalid plan")
    if not email:
        raise HTTPException(status_code=400, detail="email required")

    secret = os.environ.get("STRIPE_SECRET_KEY")
    if not secret:
        raise HTTPException(status_code=400, detail="stripe_not_configured")

    # Amount mapping (cents)
    amount_cents = {"starter": 2900, "pro": 9900, "enterprise": 49900}.get(plan, 2900)
    public_base = os.environ.get("PUBLIC_BASE_URL", "http://localhost:8003/").rstrip("/")
    success_url = f"{public_base}/?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{public_base}/?cancelled=1"

    try:
        import stripe  # type: ignore
        stripe.api_key = secret
        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            customer_email=email,
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": f"Omni SaaS {plan.title()}"},
                    "unit_amount": amount_cents,
                },
                "quantity": 1,
            }],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"plan": plan, "flow": "omni"},
        )
        return {"ok": True, "session": {"id": session.id, "url": session.url}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"stripe_error: {e}")


@router.post("/saas/checkout/confirm")
def saas_checkout_confirm(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Generic confirm endpoint: supports mock sessions and Stripe checkout.
    Body: { session_id: str }
    """
    try:
        from utils.recaptcha import verify_token
        if not verify_token(payload.get("recaptchaToken")):
            raise HTTPException(status_code=400, detail="recaptcha_failed")
    except HTTPException:
        raise
    except Exception:
        pass

    session_id = str(payload.get("session_id") or "").strip()
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    # If Stripe checkout session
    if session_id.startswith("cs_"):
        secret = os.environ.get("STRIPE_SECRET_KEY")
        if not secret:
            raise HTTPException(status_code=400, detail="stripe_not_configured")
        try:
            import stripe  # type: ignore
            stripe.api_key = secret
            sess = stripe.checkout.Session.retrieve(session_id)
            # Ensure paid/complete
            status = getattr(sess, "status", "")
            payment_status = getattr(sess, "payment_status", "")
            if not (status == "complete" or payment_status == "paid"):
                raise HTTPException(status_code=402, detail="payment_not_completed")
            email = (getattr(sess, "customer_details", None) or {}).get("email") or getattr(sess, "customer_email", None) or ""
            plan = (getattr(sess, "metadata", {}) or {}).get("plan") or "starter"
            amount_cents = {"starter": 2900, "pro": 9900, "enterprise": 49900}.get(plan, 2900)
            # Create subscription (similar to mock)
            base = email.split("@")[0] if "@" in email else (email or "tenant")
            tenant_id = (base or "tenant") + "-" + uuid.uuid4().hex[:6]
            subs = _load_json(SUBS_FILE)
            sid = uuid.uuid4().hex
            item = {
                "id": sid,
                "tenant_id": tenant_id,
                "plan": plan,
                "status": "active",
                "created_at": int(time.time() * 1000),
                "meta": {"email": email, "stripe": True, "session_id": session_id, "confirmed": True},
                "last_payment": {
                    "gateway": "stripe",
                    "status": "succeeded",
                    "amount": amount_cents / 100.0,
                    "currency": "USD",
                    "ts": int(time.time() * 1000),
                },
            }
            subs[sid] = item
            _save_json(SUBS_FILE, subs)
            return {"ok": True, "subscription_id": sid, "confirmed": True}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"stripe_error: {e}")

    # Fallback to mock confirmation
    subs = _load_json(SUBS_FILE)
    target_sid = None
    for sid, item in subs.items():
        if (item.get("meta") or {}).get("session_id") == session_id:
            target_sid = sid
            break
    if not target_sid:
        raise HTTPException(status_code=404, detail="session_not_found")

    itm = subs[target_sid]
    meta = itm.get("meta") or {}
    meta["confirmed"] = True
    itm["meta"] = meta
    itm["updated_at"] = int(time.time() * 1000)
    subs[target_sid] = itm
    _save_json(SUBS_FILE, subs)
    return {"ok": True, "subscription_id": target_sid, "confirmed": True}
