from typing import Any, Dict, Optional
from fastapi import APIRouter
import os
import re
import subprocess

router = APIRouter(prefix="/reliability", tags=["reliability"])


def _safe_run(cmd: str, cwd: Optional[str] = None, timeout: int = 60) -> Dict[str, Any]:
    try:
        p = subprocess.run(cmd, shell=True, cwd=cwd or os.getcwd(), capture_output=True, text=True, timeout=timeout)
        return {"code": p.returncode, "stdout": p.stdout[-4000:], "stderr": p.stderr[-4000:]}
    except Exception as e:
        return {"code": -1, "stdout": "", "stderr": str(e)}


@router.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True}


@router.post("/analyze")
def analyze_quality(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    root = (payload or {}).get("root") or os.getcwd()
    files = []
    for base, _, fns in os.walk(root):
        for fn in fns:
            p = os.path.join(base, fn)
            files.append(p)
    metrics = {
        "files": len(files),
        "python_files": sum(1 for p in files if p.endswith(".py")),
        "tests_present": any("tests" in p.replace("\\", "/").lower() for p in files),
        "type_hints": 0,
        "docstrings": 0,
    }
    # Detect functions with return type hints by looking for "-> <type>"
    type_hint_pat = re.compile(r"def\s+\w+\(.*\)\s*->\s*[^:\n]+")
    doc_pat = re.compile(r"\"\"\"|\'\'\'")
    for p in files:
        if p.endswith(".py"):
            try:
                txt = open(p, "r", encoding="utf-8", errors="ignore").read()
            except Exception:
                txt = ""
            if type_hint_pat.search(txt):
                metrics["type_hints"] += 1
            metrics["docstrings"] += len(doc_pat.findall(txt))
    score = 50
    if metrics["tests_present"]:
        score += 25
    score += min(25, metrics["type_hints"])
    return {"root": root, "metrics": metrics, "score": min(100, score)}


@router.post("/run-tests")
def run_tests(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    root = (payload or {}).get("root") or os.getcwd()
    # Attempt pytest, fallback to unit tests discovery
    res_pytest = _safe_run("python -m pytest -q", cwd=root, timeout=120)
    if res_pytest["code"] == 0 or ("no tests ran" in (res_pytest["stdout"]+res_pytest["stderr"]).lower()):
        return {"runner": "pytest", "result": res_pytest}
    # Fallback: run unittests discovery
    res_unit = _safe_run("python -m unittest discover -v", cwd=root, timeout=120)
    return {"runner": "unittest", "result": res_unit}