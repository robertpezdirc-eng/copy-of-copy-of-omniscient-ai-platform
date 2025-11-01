from __future__ import annotations

import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from .auth import verify_api_key
from .business_metrics import business_metrics
from .settings import settings
from .tracing import add_trace_context_to_headers

logger = logging.getLogger(__name__)
router = APIRouter()


def _client() -> httpx.AsyncClient:
    timeout = httpx.Timeout(
        connect=settings.connect_timeout,
        read=settings.request_timeout,
        write=settings.request_timeout,
        pool=5.0,  # connection pool acquisition timeout
    )
    return httpx.AsyncClient(base_url=settings.upstream_url, timeout=timeout, trust_env=True)


async def _forward(req: Request, method: str, path: str, body: Optional[bytes] = None) -> Response:
    # Build upstream request
    headers = dict(req.headers)
    # Remove any hop-by-hop headers
    for h in ["host", "content-length"]:
        headers.pop(h, None)

    # Add distributed tracing context
    add_trace_context_to_headers(headers)

    query = str(req.url.query)
    url = path + ("?" + query if query else "")

    async with _client() as client:
        try:
            upstream_resp = await client.request(method, url, content=body, headers=headers)

            # Track business metrics
            tenant_id = getattr(req.state, "tenant_id", "unknown")
            tier = getattr(req.state, "tier", "free")
            bytes_in = len(body) if body else 0
            bytes_out = len(upstream_resp.content or b"")

            business_metrics.track_api_call(
                tenant_id=tenant_id,
                endpoint=path,
                tier=tier,
                bytes_in=bytes_in,
                bytes_out=bytes_out,
            )

        except httpx.HTTPError as e:
            logger.exception("Upstream error: %s", e)
            business_metrics.track_business_error(
                error_type="upstream_unavailable",
                severity="high",
            )
            raise HTTPException(status_code=502, detail="Bad Gateway: upstream unavailable")

    # Map response back
    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers={k: v for k, v in upstream_resp.headers.items() if k.lower() in ("content-type", "cache-control")},
        media_type=upstream_resp.headers.get("content-type"),
    )


@router.api_route("/api/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], dependencies=[Depends(verify_api_key)])
async def proxy_any(req: Request, full_path: str):
    body = await req.body()
    # Forward to upstream under /api prefix to match backend routes
    return await _forward(req, req.method, f"/api/{full_path}", body)


@router.get("/health", dependencies=[Depends(verify_api_key)])
async def health(req: Request):
    # Check upstream health quickly
    async with _client() as client:
        ok = True
        try:
            r = await client.get("/api/health")
            ok = r.status_code == 200
        except Exception:
            ok = False
    return {"ok": True, "upstream_ok": ok, "service": settings.service_name}
