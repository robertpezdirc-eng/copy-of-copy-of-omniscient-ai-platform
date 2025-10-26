from typing import Any, Dict, Optional
from fastapi import APIRouter
import os
import json
import time
import smtplib
from email.mime.text import MIMEText

router = APIRouter(prefix="/notifications", tags=["notifications"])

STORE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
CONF_FILE = os.path.join(STORE_DIR, "notifications_config.json")
LOG_FILE = os.path.join(STORE_DIR, "notifications_log.json")


def _ensure():
    os.makedirs(STORE_DIR, exist_ok=True)
    for path in (CONF_FILE, LOG_FILE):
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump({}, f)


def _load(path: str) -> Dict[str, Any]:
    _ensure()
    try:
        return json.load(open(path, "r", encoding="utf-8"))
    except Exception:
        return {}


def _save(path: str, data: Dict[str, Any]):
    _ensure()
    json.dump(data, open(path, "w", encoding="utf-8"), indent=2)


def _log(event: Dict[str, Any]):
    log = _load(LOG_FILE)
    eid = str(int(time.time()*1000))
    log[eid] = event
    _save(LOG_FILE, log)


def _send_email(smtp_cfg: Dict[str, Any], to_addr: str, subject: str, body: str) -> bool:
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = smtp_cfg.get('from', smtp_cfg.get('user', 'no-reply@example.com'))
        msg['To'] = to_addr
        server = smtplib.SMTP(smtp_cfg.get('host', 'localhost'), int(smtp_cfg.get('port', 25)))
        if smtp_cfg.get('tls'):
            server.starttls()
        if smtp_cfg.get('user') and smtp_cfg.get('password'):
            server.login(smtp_cfg['user'], smtp_cfg['password'])
        server.sendmail(msg['From'], [to_addr], msg.as_string())
        server.quit()
        return True
    except Exception:
        return False


def _send_slack(webhook_url: Optional[str], text: str) -> bool:
    try:
        import requests  # type: ignore
        if webhook_url:
            r = requests.post(webhook_url, json={'text': text}, timeout=5)
            return r.status_code < 300
        return False
    except Exception:
        return False


@router.post('/config')
def set_config(payload: Dict[str, Any]) -> Dict[str, Any]:
    cfg = _load(CONF_FILE)
    cfg['smtp'] = payload.get('smtp') or cfg.get('smtp') or {}
    cfg['slack_webhook'] = payload.get('slack_webhook') or cfg.get('slack_webhook')
    _save(CONF_FILE, cfg)
    return {'ok': True, 'config': cfg}


@router.post('/send/test')
def send_test(payload: Dict[str, Any]) -> Dict[str, Any]:
    cfg = _load(CONF_FILE)
    smtp = cfg.get('smtp') or {}
    slack = cfg.get('slack_webhook')
    email_ok = False
    slack_ok = False
    if payload.get('email'):
        email_ok = _send_email(smtp, payload['email'], 'Test Notification', 'Hello from Notifications router')
    if payload.get('slack'):
        slack_ok = _send_slack(slack, 'Test Notification: hello from Notifications router')
    _log({'type': 'test', 'email_ok': email_ok, 'slack_ok': slack_ok, 'ts': int(time.time()*1000)})
    return {'ok': True, 'email_ok': email_ok, 'slack_ok': slack_ok}


@router.post('/events/expired-subscription')
def expired_subscription(payload: Dict[str, Any]) -> Dict[str, Any]:
    cfg = _load(CONF_FILE)
    smtp = cfg.get('smtp') or {}
    slack = cfg.get('slack_webhook')
    email_ok = False
    slack_ok = False
    tenant = payload.get('tenant_id') or 'unknown'
    subj = f'Subscription expired for {tenant}'
    body = f'Your subscription has expired. Please renew to continue service.'
    if payload.get('email'):
        email_ok = _send_email(smtp, payload['email'], subj, body)
    slack_ok = _send_slack(slack, f':warning: {subj}')
    _log({'type': 'expired', 'tenant': tenant, 'email_ok': email_ok, 'slack_ok': slack_ok, 'ts': int(time.time()*1000)})
    return {'ok': True}


@router.post('/events/system-error')
def system_error(payload: Dict[str, Any]) -> Dict[str, Any]:
    cfg = _load(CONF_FILE)
    smtp = cfg.get('smtp') or {}
    slack = cfg.get('slack_webhook')
    email_ok = False
    slack_ok = False
    tenant = payload.get('tenant_id') or 'unknown'
    error = payload.get('error') or 'Unknown error'
    subj = f'System error for {tenant}'
    body = f'Detected system error: {error}. Our team is investigating.'
    if payload.get('email'):
        email_ok = _send_email(smtp, payload['email'], subj, body)
    slack_ok = _send_slack(slack, f':rotating_light: {subj}: {error}')
    _log({'type': 'error', 'tenant': tenant, 'email_ok': email_ok, 'slack_ok': slack_ok, 'ts': int(time.time()*1000)})
    return {'ok': True}

@router.post('/events/payment-success')
def payment_success(payload: Dict[str, Any]) -> Dict[str, Any]:
    cfg = _load(CONF_FILE)
    smtp = cfg.get('smtp') or {}
    slack = cfg.get('slack_webhook')
    email_ok = False
    slack_ok = False
    tenant = payload.get('tenant_id') or 'unknown'
    gateway = payload.get('gateway') or 'unknown'
    amount = payload.get('amount')
    currency = payload.get('currency', 'USD')
    subj = f'Payment succeeded for {tenant} via {gateway}'
    body = f'We received your payment{f" of {amount} {currency}" if amount is not None else ""}. Thank you.'
    if payload.get('email'):
        email_ok = _send_email(smtp, payload['email'], subj, body)
    slack_ok = _send_slack(slack, f':white_check_mark: {subj}')
    _log({'type': 'payment-success', 'tenant': tenant, 'gateway': gateway, 'email_ok': email_ok, 'slack_ok': slack_ok, 'ts': int(time.time()*1000)})
    return {'ok': True}

@router.post('/events/payment-failed')
def payment_failed(payload: Dict[str, Any]) -> Dict[str, Any]:
    cfg = _load(CONF_FILE)
    smtp = cfg.get('smtp') or {}
    slack = cfg.get('slack_webhook')
    email_ok = False
    slack_ok = False
    tenant = payload.get('tenant_id') or 'unknown'
    gateway = payload.get('gateway') or 'unknown'
    subj = f'Payment failed for {tenant} via {gateway}'
    body = f'Payment attempt failed. Please update your billing information.'
    if payload.get('email'):
        email_ok = _send_email(smtp, payload['email'], subj, body)
    slack_ok = _send_slack(slack, f':x: {subj}')
    _log({'type': 'payment-failed', 'tenant': tenant, 'gateway': gateway, 'email_ok': email_ok, 'slack_ok': slack_ok, 'ts': int(time.time()*1000)})
    return {'ok': True}
