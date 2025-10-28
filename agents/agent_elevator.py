import os
import json
from typing import Optional, Dict, Any

import httpx
from fastapi import Request, Header, HTTPException
from fastapi.responses import JSONResponse

from .common import build_app, get_async_client
from .integrations import (
    verify_github_signature,
    github_comment_pr,
    github_create_check_run,
    jira_create as jira_create_api,
    jira_search as jira_search_api,
)


app = build_app("omni_elevator")


# Environment configuration
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_OWNER = os.getenv("GITHUB_OWNER", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")

JIRA_URL = os.getenv("JIRA_URL", "")  # e.g. https://your-domain.atlassian.net
JIRA_USER = os.getenv("JIRA_USER", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_PROJECT = os.getenv("JIRA_PROJECT", "")

# Zero-config service discovery (internal DNS names used if env not set)
OMNI_ADAPT_URL = os.getenv("OMNI_ADAPT_URL", "http://omni-adapt:8000")
RESOURCE_GUARD_URL = os.getenv("RESOURCE_GUARD_URL", "http://omni-resource-guard:8000")
ADAPT_GATE_THRESHOLD = float(os.getenv("ADAPT_GATE_THRESHOLD", "0.7"))


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok", "service": "omni-elevator"}


def _require_github_env():
    if not all([GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO]):
        raise HTTPException(status_code=500, detail="GitHub env not fully configured")


async def _github_create_check_run(head_sha: str, score: float, threshold: float, summary: str) -> Dict[str, Any]:
    if not all([GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO]):
        raise HTTPException(status_code=500, detail="GitHub env not fully configured")
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/check-runs"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "omni-elevator"
    }

    conclusion = "success" if score >= threshold else "failure"
    output = {
        "title": "Adaptability Gate",
        "summary": summary,
        "text": f"score: {score:.3f}, threshold: {threshold:.3f}"
    }
    payload = {
        "name": "Adaptability Gate",
        "head_sha": head_sha,
        "status": "completed",
        "conclusion": conclusion,
        "output": output,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code >= 300:
            raise HTTPException(status_code=resp.status_code, detail=f"GitHub Checks error: {resp.text}")
        return resp.json()


async def _resource_guard_pressure() -> float:
    # Query resource-guard for predicted conflicts and derive a simple pressure factor
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            rg = await client.post(f"{RESOURCE_GUARD_URL}/predict", json={"window": "5m"})
            if rg.status_code < 300:
                data = rg.json()
                conflicts = data.get("conflicts", [])
                # Simple mapping: 0 conflicts -> 0.2, each conflict bumps by 0.2 up to 0.9
                pressure = min(0.9, 0.2 + 0.2 * len(conflicts))
                return pressure
    except Exception:
        pass
    return 0.3


async def _adapt_evaluate(head_sha: Optional[str], scenario: str = "latency_budget") -> Dict[str, Any]:
    # Use resource_guard to set resource_pressure; low noise by default
    pressure = await _resource_guard_pressure()
    payload = {
        "scenario": scenario,
        "trials": 8,
        "budget_seconds": 30,
        "noise_level": 0.1,
        "resource_pressure": pressure,
        "notes": f"auto-elevator-check for {head_sha}" if head_sha else "auto-elevator-check",
    }
    async with httpx.AsyncClient(timeout=45.0) as client:
        resp = await client.post(f"{OMNI_ADAPT_URL}/evaluate", json=payload)
        if resp.status_code >= 300:
            raise HTTPException(status_code=resp.status_code, detail=f"Adapt evaluate error: {resp.text}")
        return resp.json()


@app.post("/webhook/github")
async def github_webhook(
    request: Request,
    x_github_event: Optional[str] = Header(default=None, alias="X-GitHub-Event"),
    x_hub_signature_256: Optional[str] = Header(default=None, alias="X-Hub-Signature-256"),
):
    raw_body = await request.body()
    try:
        verify_github_signature(GITHUB_WEBHOOK_SECRET, raw_body, x_hub_signature_256)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if x_github_event == "pull_request":
        action = payload.get("action")
        pr = payload.get("pull_request", {})
        number = pr.get("number") or payload.get("number")
        title = pr.get("title")
        head_sha = pr.get("head", {}).get("sha")
        user_login = pr.get("user", {}).get("login")

        if number is None:
            raise HTTPException(status_code=400, detail="No PR number in payload")

        # 1) Objavi hiter PR komentar (ne-obvezujoče)
        try:
            _require_github_env()
            comment = (
                f"✅ Webhook preverjen (HMAC OK). Dogodek: {action}.\n"
                f"PR: #{number} — '{title}'. Avtor: @{user_login}.\n"
                f"Commit: {head_sha}.\n\n"
                f"Zaganjam Adaptability Gate (Checks API) s pragom {ADAPT_GATE_THRESHOLD:.2f}."
            )
            await github_comment_pr(GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, int(number), comment)
        except Exception:
            pass

        # 2) Zaženi Adaptability oceno in ustvari Check Run
        adapt = await _adapt_evaluate(head_sha=head_sha)
        score = float(adapt.get("adaptability_score", 0.0))
        summary = (
            f"Adaptability score: {score:.3f} (threshold {ADAPT_GATE_THRESHOLD:.3f}).\n"
            f"Submetrics: {adapt.get('submetrics')}.\n"
            f"Scenario: {adapt.get('scenario')} — duration: {adapt.get('duration_sec')}s."
        )
        try:
            _require_github_env()
            check = await github_create_check_run(GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, head_sha, score, ADAPT_GATE_THRESHOLD, summary)
        except Exception as e:
            # Če Checks API ni na voljo, vrnemo rezultat brez blokade
            return {"status": "validated", "gate": {"score": score, "threshold": ADAPT_GATE_THRESHOLD, "checks_error": str(e)}}

        return {"status": "validated", "gate": {"score": score, "threshold": ADAPT_GATE_THRESHOLD, "check_run_id": check.get("id")}, "action": action}

    # Ignore other events for now
    return {"status": "ignored", "event": x_github_event}


@app.post("/jira/create")
async def jira_create(issue: Dict[str, Any]):
    """
    Body example:
    {
      "summary": "Napaka v storitvi X",
      "description": "Koraki za reprodukcijo...",
      "issuetype": "Task"  // ali "Bug"
    }
    """
    if not all([JIRA_URL, JIRA_PROJECT, JIRA_USER, JIRA_API_TOKEN]):
        raise HTTPException(status_code=500, detail="JIRA env not fully configured")

    fields = {
        "project": {"key": JIRA_PROJECT},
        "summary": issue.get("summary", "Auto-created by omni-elevator"),
        "description": issue.get("description", "Ustvarjeno avtomatsko."),
        "issuetype": {"name": issue.get("issuetype", "Task")},
    }
    try:
        return await jira_create_api(JIRA_URL, JIRA_PROJECT, JIRA_USER, JIRA_API_TOKEN, fields["summary"], fields["description"], fields["issuetype"]["name"]) 
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"JIRA API error: {e.response.text}")


@app.post("/jira/search")
async def jira_search(body: Dict[str, Any]):
    """
    Body example:
    { "jql": "project = ABC AND statusCategory != Done ORDER BY created DESC", "maxResults": 20 }
    """
    if not all([JIRA_URL, JIRA_USER, JIRA_API_TOKEN]):
        raise HTTPException(status_code=500, detail="JIRA env not fully configured")

    jql = body.get("jql", f"project = {JIRA_PROJECT}")
    max_results = body.get("maxResults", 25)
    start_at = body.get("startAt", 0)
    try:
        return await jira_search_api(JIRA_URL, JIRA_USER, JIRA_API_TOKEN, jql, max_results, start_at)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"JIRA API error: {e.response.text}")


@app.get("/selftest")
async def selftest():
    """Avtomatska validacija: preveri skrivnosti in dosegljivost ključnih storitev."""
    results: Dict[str, Any] = {"secrets": {}, "connectivity": {}}

    # Secrets presence
    results["secrets"]["GITHUB_WEBHOOK_SECRET"] = bool(GITHUB_WEBHOOK_SECRET)
    results["secrets"]["GITHUB_TOKEN"] = bool(GITHUB_TOKEN)
    results["secrets"]["JIRA"] = all([JIRA_URL, JIRA_USER, JIRA_API_TOKEN])

    # Connectivity tests
    try:
        client = get_async_client()
        a = await client.get(f"{OMNI_ADAPT_URL}/benchmarks")
        results["connectivity"]["omni-adapt"] = a.status_code
    except Exception as e:
        results["connectivity"]["omni-adapt"] = str(e)

    try:
        client = get_async_client()
        rl = await client.get("https://api.github.com/rate_limit", headers={"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else None)
        results["connectivity"]["github"] = getattr(rl, "status_code", 0)
    except Exception as e:
        results["connectivity"]["github"] = str(e)

    ok = all([
        results["secrets"]["GITHUB_WEBHOOK_SECRET"],
        results["secrets"]["GITHUB_TOKEN"],
        results["connectivity"].get("omni-adapt") == 200,
    ])
    return {"ok": ok, **results}


@app.get("/lifeline")
async def lifeline():
    """Varnostni mehanizem 'vzdrževalec življenja': minimalna potrditev delovanja kritičnih odvisnosti."""
    try:
        pressure = await _resource_guard_pressure()
        return {"status": "alive", "resource_pressure": pressure}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"lifeline failed: {e}")

import httpx
from .common import build_app
from pydantic import BaseModel

app = build_app("omni_elevator")


class RepoSpec(BaseModel):
    repo_url: str | None = None          # npr. https://github.com/org/repo
    branch: str | None = "main"
    pr_number: int | None = None
    archive_url: str | None = None       # .zip / .tar.gz
    sha: str | None = None


class CheckPlan(BaseModel):
    run_static: bool = True
    run_tests: bool = True
    run_security: bool = True
    run_chaos: bool = True
    budget_usd: float = 1.0


@app.post("/webhook/github")
async def github_webhook(payload: dict):
    # Minimal stub – v praksi dodamo preverjanje podpisa X-Hub-Signature-256
    action = payload.get("action")
    event = payload.get("pull_request") or payload.get("push")
    return {"status": "received", "action": action, "has_event": event is not None}


@app.post("/ingest_repo")
async def ingest(repo: RepoSpec):
    # Stub: tu bi prenesli tarball/zip in ga razpakirali v delovni prostor
    return {"status": "queued", "repo": repo.model_dump(exclude_none=True)}


@app.post("/run_checks")
async def run_checks(plan: CheckPlan):
    # Stub: orkestracija – v praksi bi klicali orodja v DIND (DOCKER_HOST=omni-dind:2375)
    steps = []
    if plan.run_static:
        steps.append("static_analysis")
    if plan.run_tests:
        steps.append("unit_integration_tests")
    if plan.run_security:
        steps.append("security_scan")
    if plan.run_chaos:
        steps.append("chaos_experiments")
    return {"status": "planned", "steps": steps, "budget_usd": plan.budget_usd}


@app.post("/chaos")
async def chaos_scenarios(spec: dict):
    # Stub: kontrola Pumba/chaos runnerja preko DOCKER_HOST=omni-dind:2375
    return {"status": "scheduled", "scenarios": ["kill-random", "net-emulate-latency"], "spec": spec}