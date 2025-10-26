# Billing Security and Notifications

## Stripe Webhook Verification
- Set `STRIPE_WEBHOOK_SECRET` to your webhook signing secret.
- Optional `STRIPE_TOLERANCE` (seconds, default `300`) enforces timestamp window.
- Verification logic:
  - Header: `Stripe-Signature: t=<timestamp>,v1=<signature>`
  - Signed payload: `f"{t}.{raw_body}"` HMAC-SHA256 with the secret.

Example Python request:
```python
import os, json, time, hmac, hashlib, requests
secret = os.environ['STRIPE_WEBHOOK_SECRET']
body = {"type":"payment_intent.succeeded","subscription_id": "<sid>", "id": "evt_123"}
body_str = json.dumps(body, separators=(',',':'))
t = int(time.time())
signed = f"{t}.{body_str}".encode('utf-8')
sig = hmac.new(secret.encode('utf-8'), signed, hashlib.sha256).hexdigest()
headers = {"Stripe-Signature": f"t={t},v1={sig}", "Content-Type":"application/json"}
r = requests.post("http://localhost:8002/api/v1/billing/saas/payments/stripe/webhook", data=body_str, headers=headers)
print(r.status_code, r.json())
```

## PayPal Webhook Verification
Two modes are available via `PAYPAL_VERIFY_MODE`:
- `hmac` (default): set `PAYPAL_WEBHOOK_SECRET` and header `Transmission-Sig` to `HMAC(secret, raw_body)` (sha256).
- `remote`: uses PayPal API to verify signatures.
  - Required env: `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `PAYPAL_WEBHOOK_ID`.
  - Choose environment with `PAYPAL_ENV` = `sandbox` or `live`.

## API Key Protection
Set `API_KEY` to enforce requests on internal endpoints. Use header `X-API-Key: <API_KEY>`.
Protected endpoints:
- `POST /api/v1/billing/saas/subscriptions`
- `POST /api/v1/billing/saas/subscriptions/{sid}/update`
- `GET  /api/v1/billing/saas/subscriptions`
- `POST /api/v1/billing/usage/{tenant_id}/track`
- `POST /api/v1/billing/saas/payments/stripe/intent`
- `POST /api/v1/billing/saas/payments/paypal/order`
Webhooks are not API-key protected; they rely on signature verification.

## Real Notifications
Slack:
- Set `SLACK_WEBHOOK_URL` (incoming webhook).
Email:
- Set `SMTP_HOST`, `SMTP_PORT` (default 587), `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`, and `NOTIFY_EMAIL_TO`.
- Optional `SMTP_TLS` (default `1`, set to `0` to disable).
Local forwarding:
- Set `NOTIFY_LOCAL_FORWARD=1` to additionally forward events to `POST /api/v1/notifications/events/payment-<kind>`.

## Testing Notes
- Health: `GET http://localhost:8002/api/v1/billing/health`
- Create subscription: `POST /api/v1/billing/saas/subscriptions` with `X-API-Key`.
- Generate Stripe intent: `POST /api/v1/billing/saas/payments/stripe/intent` with `X-API-Key`.
- Stripe webhook: see Python example above; ensure `STRIPE_WEBHOOK_SECRET` is set.
- PayPal webhook (HMAC): compute `Transmission-Sig` = `HMAC(secret, raw_body)`.

## Idempotency
- Webhook processing is idempotent when `event_id` or `id` repeats; duplicate events return `{"idempotent": true}` and do not reapply side effects.