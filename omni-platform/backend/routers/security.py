from typing import Any, Dict, List, Optional
from fastapi import APIRouter
import os
import re
import json

router = APIRouter(prefix="/security", tags=["security"])

_SECRET_PATTERNS = [
    ("AWS Access Key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("AWS Secret Key", re.compile(r"(?i)aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40}")),
    ("Private Key", re.compile(r"-----BEGIN (RSA|DSA|EC) PRIVATE KEY-----")),
    ("JWT", re.compile(r"eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+")),
]

_INSECURE_CRYPTO = [re.compile(r"\bmd5\("), re.compile(r"\bsha1\(")]

_BANNED_LIBS = {
    "python": ["pycrypto"],
    "node": ["event-stream"],
}


def _safe_read(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def _walk_files(root: str) -> List[str]:
    files = []
    for base, _, fns in os.walk(root):
        for fn in fns:
            p = os.path.join(base, fn)
            files.append(p)
    return files


def _scan_dependencies(root: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {"python": {}, "node": {}}
    req = os.path.join(root, "requirements.txt")
    if os.path.exists(req):
        lines = _safe_read(req).splitlines()
        deps = []
        for ln in lines:
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            name = re.split(r"[<>=]", ln)[0].strip()
            pinned = any(ch in ln for ch in ["==", ">=", "<="])  # loose heuristic
            deps.append({"name": name, "spec": ln, "pinned": pinned, "banned": name in _BANNED_LIBS["python"]})
        out["python"]["dependencies"] = deps
    pkg = os.path.join(root, "package.json")
    if os.path.exists(pkg):
        try:
            data = json.loads(_safe_read(pkg) or "{}")
        except Exception:
            data = {}
        deps = []
        for section in ["dependencies", "devDependencies"]:
            for name, spec in (data.get(section, {}) or {}).items():
                pinned = not any(ch in str(spec) for ch in ["^", "~", ">", "<", "*"])  # semver loose
                deps.append({"name": name, "spec": spec, "pinned": pinned, "banned": name in _BANNED_LIBS["node"]})
        out["node"]["dependencies"] = deps
    return out


def _scan_docker(root: str) -> Dict[str, Any]:
    info: Dict[str, Any] = {"dockerfiles": []}
    for path in _walk_files(root):
        if os.path.basename(path).lower().startswith("dockerfile"):
            txt = _safe_read(path)
            base = None
            m = re.search(r"^\s*FROM\s+([\w./:-]+)", txt, re.MULTILINE)
            if m:
                base = m.group(1)
            user = None
            m2 = re.search(r"^\s*USER\s+(\w+)", txt, re.MULTILINE)
            if m2:
                user = m2.group(1)
            info["dockerfiles"].append({"path": path, "base": base, "user": user, "uses_latest": bool(base and ":latest" in base)})
    return info


def _scan_secrets_and_crypto(root: str) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    for path in _walk_files(root):
        txt = _safe_read(path)
        if not txt:
            continue
        for label, pat in _SECRET_PATTERNS:
            if pat.search(txt):
                findings.append({"path": path, "issue": "secret", "label": label})
        for pat in _INSECURE_CRYPTO:
            if pat.search(txt):
                findings.append({"path": path, "issue": "insecure_crypto", "label": "md5/sha1"})
    return findings


@router.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True}


@router.post("/scan/vulnerabilities")
def scan_vulnerabilities(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    root = (payload or {}).get("root") or os.getcwd()
    deps = _scan_dependencies(root)
    docker = _scan_docker(root)
    findings = _scan_secrets_and_crypto(root)
    score = 100
    # simple scoring: penalize secrets, insecure crypto, unpinned deps, latest docker base
    score -= 20 * sum(1 for f in findings if f["issue"] == "secret")
    score -= 10 * sum(1 for f in findings if f["issue"] == "insecure_crypto")
    py_deps = deps.get("python", {}).get("dependencies", [])
    node_deps = deps.get("node", {}).get("dependencies", [])
    score -= 2 * sum(1 for d in py_deps if not d.get("pinned"))
    score -= 2 * sum(1 for d in node_deps if not d.get("pinned"))
    score -= 5 * sum(1 for d in docker.get("dockerfiles", []) if d.get("uses_latest"))
    return {
        "root": root,
        "score": max(0, score),
        "dependencies": deps,
        "docker": docker,
        "findings": findings,
        "recommendations": [
            "Pin dependencies to exact versions where feasible",
            "Remove hardcoded secrets and use environment or vault",
            "Avoid md5/sha1; use sha256+ and strong KDFs",
            "Avoid FROM ...:latest; pin base image tags",
            "Use non-root USER in Dockerfiles",
        ],
    }


@router.post("/check/compliance")
def check_compliance(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    root = (payload or {}).get("root") or os.getcwd()
    frameworks = (payload or {}).get("frameworks") or ["GDPR", "SOC2"]
    files = set(_walk_files(root))
    exists = lambda name: any(name in p.replace("\\", "/") for p in files)
    signals = {
        "security_policy": exists("docs/security") or exists("SECURITY.md"),
        "incident_response": exists("docs/incident") or exists("INCIDENT.md"),
        "audit_logs": exists("logs/") or exists("audit"),
        "rbac": exists("rbac") or exists("auth") or exists("routers/security")
    }
    score = sum(25 for k, v in signals.items() if v)
    gaps = [k for k, v in signals.items() if not v]
    return {
        "root": root,
        "frameworks": frameworks,
        "signals": signals,
        "score": min(100, score),
        "gaps": gaps,
        "actions": [
            "Document security policies (SECURITY.md)",
            "Prepare incident response runbook",
            "Implement audit logging for sensitive actions",
            "Introduce tenant-scoped RBAC for all routers",
        ],
    }