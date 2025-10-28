import hmac
import hashlib
from typing import Optional, Dict, Any

import httpx

from .common import get_async_client


def verify_github_signature(secret: str, payload: bytes, header_signature: Optional[str]) -> None:
    if not secret:
        raise ValueError("GITHUB_WEBHOOK_SECRET not configured")
    if not header_signature:
        raise ValueError("Missing X-Hub-Signature-256 header")
    try:
        sha_name, signature = header_signature.split("=", 1)
    except ValueError:
        raise ValueError("Invalid signature header format")
    if sha_name != "sha256":
        raise ValueError("Unsupported signature algorithm")
    mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
    expected = mac.hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise ValueError("Invalid signature")


async def github_comment_pr(token: str, owner: str, repo: str, pr_number: int, body: str) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "omni-elevator"
    }
    client = get_async_client()
    resp = await client.post(url, headers=headers, json={"body": body})
    resp.raise_for_status()
    return resp.json()


async def github_create_check_run(token: str, owner: str, repo: str, head_sha: str, score: float, threshold: float, summary: str) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/check-runs"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "omni-elevator"
    }
    conclusion = "success" if score >= threshold else "failure"
    payload = {
        "name": "Adaptability Gate",
        "head_sha": head_sha,
        "status": "completed",
        "conclusion": conclusion,
        "output": {
            "title": "Adaptability Gate",
            "summary": summary,
            "text": f"score: {score:.3f}, threshold: {threshold:.3f}"
        },
    }
    client = get_async_client()
    resp = await client.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()


def jira_auth_header(user: str, api_token: str) -> str:
    return httpx.BasicAuth(user, api_token).auth_header.decode()


async def jira_create(base_url: str, project_key: str, user: str, api_token: str, summary: str, description: str, issuetype: str = "Task") -> Dict[str, Any]:
    url = f"{base_url}/rest/api/3/issue"
    headers = {
        "Authorization": jira_auth_header(user, api_token),
        "Content-Type": "application/json"
    }
    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issuetype},
        }
    }
    client = get_async_client()
    resp = await client.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()


async def jira_search(base_url: str, user: str, api_token: str, jql: str, maxResults: int = 25, startAt: int = 0) -> Dict[str, Any]:
    url = f"{base_url}/rest/api/3/search"
    headers = {
        "Authorization": jira_auth_header(user, api_token),
        "Content-Type": "application/json"
    }
    payload = {"jql": jql, "maxResults": maxResults, "startAt": startAt}
    client = get_async_client()
    resp = await client.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()