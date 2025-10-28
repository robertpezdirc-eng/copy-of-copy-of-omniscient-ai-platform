import os
import uuid
from typing import Any, Dict, Optional

import httpx


MEASUREMENT_ID = os.environ.get("GA4_MEASUREMENT_ID")
API_SECRET = os.environ.get("GA4_API_SECRET")


async def send_event(
    event_name: str,
    params: Optional[Dict[str, Any]] = None,
    client_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Send a GA4 event using Measurement Protocol.

    Requires env GA4_MEASUREMENT_ID and GA4_API_SECRET.
    """
    if not MEASUREMENT_ID or not API_SECRET:
        return {"ok": False, "error": "ga4_not_configured"}

    cid = client_id or str(uuid.uuid4())
    payload: Dict[str, Any] = {
        "client_id": cid,
        "events": [
            {
                "name": event_name,
                "params": {
                    "engagement_time_msec": 1,
                    **(params or {}),
                },
            }
        ],
    }
    if user_id:
        payload["user_id"] = user_id

    url = f"https://www.google-analytics.com/mp/collect?measurement_id={MEASUREMENT_ID}&api_secret={API_SECRET}"
    async with httpx.AsyncClient(timeout=5) as client:
        r = await client.post(url, json=payload)
        return {"ok": r.status_code in (200, 204), "status": r.status_code}