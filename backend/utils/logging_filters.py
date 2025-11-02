from __future__ import annotations

import logging
import re
from typing import Iterable

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_BEARER_RE = re.compile(r"Bearer\s+[A-Za-z0-9._\-]+", re.IGNORECASE)


class PIIRedactionFilter(logging.Filter):
    """Best-effort redaction of common PII in log records.

    This filter scrubs emails and bearer tokens in the formatted message.
    """

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        msg = record.getMessage()
        msg = _EMAIL_RE.sub("[redacted-email]", msg)
        msg = _BEARER_RE.sub("Bearer [redacted-token]", msg)
        record.msg = msg
        record.args = ()
        return True
