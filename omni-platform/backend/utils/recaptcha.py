import os
import requests
from typing import Optional

VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"


def is_enabled() -> bool:
    return os.environ.get("RECAPTCHA_VERIFY", "0") not in ("0", "false", "False", "")


def verify_token(token: Optional[str]) -> bool:
    if not is_enabled():
        return True
    secret = os.environ.get("RECAPTCHA_SECRET")
    if not secret:
        # If enabled but no secret, fail closed
        return False
    if not token:
        return False
    try:
        r = requests.post(VERIFY_URL, data={"secret": secret, "response": token}, timeout=5)
        data = r.json()
        # v2 and v3 both return 'success'; for v3 also check score if provided
        if not data.get("success"):
            return False
        score = data.get("score")
        threshold = float(os.environ.get("RECAPTCHA_THRESHOLD", "0.5"))
        if score is not None and score < threshold:
            return False
        return True
    except Exception:
        return False