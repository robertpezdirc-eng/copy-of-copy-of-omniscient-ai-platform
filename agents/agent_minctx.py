import os
from typing import List, Dict, Any

from fastapi import Body
from pydantic import BaseModel, Field

from .common import build_app


app = build_app("omni-minctx")


REPO_PATH = os.getenv("REPO_PATH", "/workspace")


def repo_tree(root: str, max_depth: int = 2, max_entries: int = 200) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    root = os.path.abspath(root)
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        if depth > max_depth:
            continue
        if any(p.startswith('.') for p in [rel] if p != '.'):  # skip hidden dirs at top
            continue
        entry = {
            "path": rel if rel != "." else "/",
            "dirs": sorted([d for d in dirnames if not d.startswith('.')])[:50],
            "files": sorted([f for f in filenames if not f.startswith('.')])[:50],
        }
        result.append(entry)
        if len(result) >= max_entries:
            break
    return result


class MinimalContextRequest(BaseModel):
    topic: str
    hints: List[str] = Field(default_factory=list)


@app.get("/context/minimal")
async def minimal(max_depth: int = 2):
    return {"root": os.path.abspath(REPO_PATH), "tree": repo_tree(REPO_PATH, max_depth=max_depth)}


@app.post("/context/summarize")
async def summarize(req: MinimalContextRequest):
    # Heuristic: return a reduced repo tree and echo topic/hints for external AI to decide
    tree = repo_tree(REPO_PATH, max_depth=2)
    summary = {
        "topic": req.topic,
        "hints": req.hints,
        "suggestion": "Focus on agents/, docker-compose.yml, and prometheus.yml for platform changes.",
    }
    return {"summary": summary, "tree": tree[:20]}