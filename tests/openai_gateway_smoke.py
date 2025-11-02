#!/usr/bin/env python3
"""
OpenAI-compatible Gateway Smoke Test

Sends a small /v1/chat/completions request to the gateway and validates shape.
Writes a timestamped JSON report under tests/.

Env vars:
  GATEWAY_URL   - defaults to deployed gateway URL
  GATEWAY_TOKEN - Bearer API key for gateway (defaults to 'prod-key-omni-2025')
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict

import requests


def main() -> int:
    gateway_url = os.getenv(
        "GATEWAY_URL",
        "https://ai-gateway-661612368188.europe-west1.run.app",
    ).rstrip("/")
    token = os.getenv("GATEWAY_TOKEN", "prod-key-omni-2025")

    url = f"{gateway_url}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body: Dict[str, Any] = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "Say hello in one short sentence (smoke test)."}
        ],
    }

    print(f"Target: {url}")
    start = time.time()
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=60)
        latency_ms = (time.time() - start) * 1000
        ok = resp.status_code == 200
        data: Dict[str, Any] = {}
        error = None
        try:
            data = resp.json()
        except Exception as je:  # non-JSON response
            error = f"Invalid JSON response: {je}; text={resp.text[:200]}"

        status = "PASS" if ok and isinstance(data, dict) and "choices" in data else "FAIL"

        # Minimal shape checks
        details = {
            "status_code": resp.status_code,
            "latency_ms": round(latency_ms, 2),
            "has_choices": isinstance(data, dict) and "choices" in data,
            "model": (data.get("model") if isinstance(data, dict) else None),
            "error": error or data.get("error") if isinstance(data, dict) else error,
        }

        # Write report
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "target": url,
            "status": status,
            "details": details,
            "sample": data if ok else {"text": resp.text[:400]},
        }
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out_path = os.path.join(os.path.dirname(__file__), f"smoke_openai_gateway_{ts}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Result: {status} | {details} | Report: {out_path}")

        return 0 if status == "PASS" else 1
    except Exception as e:
        print(f"Error: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
