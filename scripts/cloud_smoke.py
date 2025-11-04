import os
import sys
import time
import requests


def check_url(url: str, expect_text: str | None = None, timeout: int = 15) -> None:
    if not url:
        raise ValueError("URL is empty")
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code != 200:
            raise RuntimeError(f"{url} returned status {resp.status_code}")
        if expect_text and expect_text not in resp.text:
            raise RuntimeError(f"Expected text not found in response from {url}")
        print(f"OK: {url} -> {resp.status_code}")
    except Exception as e:
        raise RuntimeError(f"Failed to check {url}: {e}")


def main() -> int:
    gateway = os.getenv("GATEWAY_URL", "").strip()
    frontend = os.getenv("FRONTEND_URL", "").strip()

    failures = []

    # Gateway checks
    if gateway:
        for path, expect in [
            ("/healthz", "\"status\":\"ok\""),
            ("/metrics", None),
            ("/", None),
        ]:
            url = gateway.rstrip("/") + path
            try:
                check_url(url, expect_text=expect)
            except Exception as e:
                print(str(e))
                failures.append(url)
            time.sleep(0.5)
    else:
        print("GATEWAY_URL not provided; skipping gateway checks.")

    # Frontend checks
    if frontend:
        try:
            # Typical Vite/React build contains root div
            check_url(frontend, expect_text="id=\"root\"")
        except Exception as e:
            print(str(e))
            failures.append(frontend)
    else:
        print("FRONTEND_URL not provided; skipping frontend checks.")

    if failures:
        print(f"Failures: {failures}")
        return 1
    print("All cloud smoke checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())