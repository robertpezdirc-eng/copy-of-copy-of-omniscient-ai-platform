import os
import json
import sys
import requests

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8080")
API_KEY = os.getenv("API_KEY", "")
UPSTREAM_AUTH = os.getenv("UPSTREAM_AUTH", "Bearer master-key-change-in-production")

def main():
    # 1) Health through gateway to backend minimal
    headers_basic = {"X-API-Key": API_KEY}
    r1 = requests.get(f"{GATEWAY_URL}/api/health", headers=headers_basic, timeout=10)
    print("Health status:", r1.status_code)
    print(json.dumps(r1.json(), indent=2))

    # 2) Minimal AI chat (will error without OpenAI key, but proves logic path)
    r2 = requests.post(
        f"{GATEWAY_URL}/api/v1/ai/chat",
        headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
        json={"prompt": "Napiši motivacijski stavek v slovenščini."},
        timeout=20,
    )
    print("Chat status:", r2.status_code)
    try:
        print(json.dumps(r2.json(), indent=2))
    except Exception:
        print(r2.text)

if __name__ == "__main__":
    main()