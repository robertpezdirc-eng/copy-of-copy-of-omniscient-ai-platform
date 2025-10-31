from typing import Any, Dict, Optional
import httpx
import os
import time
from urllib.parse import urlparse

class NetAgentAdapter:
    async def fetch(self, url: str, method: str = "GET", headers: Optional[Dict[str, str]] = None, body: Optional[Any] = None, timeout: float = 20.0) -> Dict[str, Any]:
        # Basic URL safety and SSL enforcement
        parsed = urlparse(url)
        allow_http = os.getenv("NETAGENT_ALLOW_HTTP", "0") == "1"
        if parsed.scheme not in ("http", "https"):
            return {"ok": False, "error": "unsupported_scheme", "scheme": parsed.scheme, "url": url}
        if parsed.scheme != "https" and not allow_http:
            return {"ok": False, "error": "insecure_http_blocked", "url": url}

        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                resp = await client.request(method.upper(), url, headers=headers or {}, json=body)
                latency_ms = int((time.time() - start) * 1000)
                max_latency_ms = int(os.getenv("NETAGENT_MAX_LATENCY_MS", "5000"))
                content_type = resp.headers.get("content-type", "")
                data: Any
                try:
                    if "application/json" in content_type:
                        data = resp.json()
                    else:
                        # Limit text size to prevent memory blowups
                        max_size = int(os.getenv("NETAGENT_MAX_SIZE", "1048576"))
                        txt = resp.text
                        if len(txt) > max_size:
                            txt = txt[:max_size]
                        data = txt
                except Exception:
                    data = resp.text
                safe = (parsed.scheme == "https") and (latency_ms <= max_latency_ms) and (resp.status_code < 500)
                return {
                    "ok": True,
                    "safe": safe,
                    "latency_ms": latency_ms,
                    "status_code": resp.status_code,
                    "headers": dict(resp.headers),
                    "data": data,
                    "url": str(resp.url),
                    "method": method.upper(),
                    "content_type": content_type,
                }
        except httpx.ConnectError as e:
            return {"ok": False, "error": "connect_error", "detail": str(e), "url": url}
        except httpx.ReadTimeout as e:
            latency_ms = int((time.time() - start) * 1000)
            return {"ok": False, "error": "timeout", "latency_ms": latency_ms, "detail": str(e), "url": url}
        except httpx.HTTPError as e:
            return {"ok": False, "error": "http_error", "detail": str(e), "url": url}