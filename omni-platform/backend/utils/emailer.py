import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates", "email")


def _smtp_config():
    mail_mode = (os.environ.get("MAIL_MODE") or "").lower().strip()
    if mail_mode == "mailhog":
        mailhog = True
    elif mail_mode == "smtp":
        mailhog = False
    else:
        mailhog = os.environ.get("MAILHOG_ENABLED", "1") == "1"
    host = os.environ.get("SMTP_HOST", "mailhog" if mailhog else "localhost")
    port = int(os.environ.get("SMTP_PORT", "1025" if mailhog else "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASS") or os.environ.get("SMTP_PASSWORD")
    sender = os.environ.get("SMTP_FROM") or (user or "no-reply@omni.local")
    use_tls = os.environ.get("SMTP_TLS", "0" if mailhog else "1") != "0"
    return host, port, user, password, sender, use_tls


def _render_template(name: str, variables: Dict[str, str]) -> str:
    path = os.path.join(TEMPLATES_DIR, f"{name}.html")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Email template not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    # Simple placeholder replacement: {{key}} -> value
    for k, v in (variables or {}).items():
        html = html.replace(f"{{{{{k}}}}}", str(v))
    return html


def send_template(to: str, subject: str, template: str, variables: Dict[str, str]) -> bool:
    host, port, user, password, sender, use_tls = _smtp_config()

    html_body = _render_template(template, variables)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html", _charset="utf-8"))

    try:
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            if use_tls:
                try:
                    smtp.starttls()
                except Exception:
                    pass
            if user and password:
                smtp.login(user, password)
            smtp.sendmail(sender, [to], msg.as_string())
        return True
    except Exception as e:
        # In production, log this properly
        print(f"[emailer] send failed: {e}")
        return False