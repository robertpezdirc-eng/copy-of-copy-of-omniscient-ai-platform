import os
from typing import Dict, Any, List

import httpx
from fastapi import HTTPException

from .common import build_app, get_async_client


app = build_app("omni_forensics")

PROM_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
LOKI_URL = os.getenv("LOKI_URL", "http://loki:3100")
RICA_URL = os.getenv("RICA_URL", "http://omni-rica:8000")

JIRA_URL = os.getenv("JIRA_URL", "")
JIRA_USER = os.getenv("JIRA_USER", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_PROJECT = os.getenv("JIRA_PROJECT", "")


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok", "service": "omni-forensics"}


def _jira_headers() -> Dict[str, str]:
    return {
        "Authorization": httpx.BasicAuth(JIRA_USER, JIRA_API_TOKEN).auth_header.decode() if JIRA_USER and JIRA_API_TOKEN else "",
        "Content-Type": "application/json",
    }


async def _create_jira(summary: str, description: str) -> Dict[str, Any]:
    if not all([JIRA_URL, JIRA_PROJECT, JIRA_USER, JIRA_API_TOKEN]):
        raise HTTPException(status_code=500, detail="JIRA env not fully configured")
    url = f"{JIRA_URL}/rest/api/3/issue"
    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT},
            "summary": summary,
            "description": description,
            "issuetype": {"name": "Bug"},
        }
    }
    headers = _jira_headers()
    client = get_async_client()
    resp = await client.post(url, headers=headers, json=payload)
    if resp.status_code >= 300:
        raise HTTPException(status_code=resp.status_code, detail=f"JIRA error: {resp.text}")
    return resp.json()


@app.post("/analyze")
async def analyze(body: Dict[str, Any]):
    """
    Body example:
    {
      "query": "rate(container_cpu_usage_seconds_total[5m])",
      "log_query": "{app=\"backend\"}",
      "start": "-15m",
      "end": "now",
      "auto_jira": true,
      "context": {"service": "backend", "release": "v1.2.3"}
    }
    """
    start = body.get("start", "-15m")
    end = body.get("end", "now")
    context = body.get("context", {})

    # Delegate correlation to omni-rica
    rica_payload = {
        "start": start,
        "end": end,
        "prom_query": body.get("query", "up"),
        "loki_query": body.get("log_query", "{}"),
        "context": context,
    }
    client = get_async_client()
    rica_resp = await client.post(f"{RICA_URL}/correlate", json=rica_payload)
    if rica_resp.status_code >= 300:
        raise HTTPException(status_code=rica_resp.status_code, detail=f"RICA error: {rica_resp.text}")
    correlation = rica_resp.json()

    # Simple heuristic root-cause guess (stub)
    signals = correlation.get("signals", {})
    score = signals.get("score", 0.5)
    culprit = context.get("service", "unknown-service")

    result = {
        "culprit": culprit,
        "confidence": score,
        "correlation": correlation,
        "recommendation": "Preveri zadnje spremembe in povišane latence v odvisnostih.",
    }

    if body.get("auto_jira"):
        summary = f"[Auto] Incident v {culprit} (confidence {int(score*100)}%)"
        description = (
            f"Samodejna forenzična analiza predlaga možen vzrok v storitvi {culprit}.\n\n"
            f"Kontekst: {context}\n\nKorrelacija: {correlation}"
        )
        try:
            jira_issue = await _create_jira(summary, description)
            result["jira"] = jira_issue
        except HTTPException as e:
            result["jira_error"] = e.detail

    return result