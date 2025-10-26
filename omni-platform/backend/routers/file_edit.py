from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any
from pathlib import Path
import time
from .access_controller import require_api_key
from learning.feedback_store import FeedbackStore

router = APIRouter(prefix="/files", tags=["files"])

class FileCreateRequest(BaseModel):
    path: str
    content: str

class FileRewriteRequest(BaseModel):
    path: str
    content: str

class FileUpdateRequest(BaseModel):
    path: str
    old_str: str
    new_str: str


def _get_edit_root() -> Path:
    # backend/routers -> backend -> OMNI-Platform root
    return Path(__file__).resolve().parents[2]


def _resolve_safe(path_str: str) -> Path:
    root = _get_edit_root()
    candidate = (root / path_str).resolve()
    if not str(candidate).startswith(str(root)):
        raise ValueError("path_outside_root")
    return candidate


@router.post("/create")
async def files_create(req: FileCreateRequest, auth: Dict[str, Any] = Depends(require_api_key)):
    fb = FeedbackStore()
    started = time.time()
    try:
        target = _resolve_safe(req.path)
        if target.exists():
            return {"ok": False, "error": "exists"}
        target.parent.mkdir(parents=True, exist_ok=True)
        data = req.content.encode("utf-8")
        with open(target, "wb") as f:
            f.write(data)
        latency_ms = int((time.time() - started) * 1000)
        fb.insert_event({
            "agent_type": "omni-brain",
            "provider": "local",
            "model": "fs",
            "task_type": "file-edit",
            "success": True,
            "reward": min(1.0, len(data) / 5000.0),
            "latency_ms": latency_ms,
            "meta": {"op": "create", "path": req.path},
        })
        return {"ok": True, "path": str(target), "bytes_written": len(data), "latency_ms": latency_ms}
    except Exception as e:
        latency_ms = int((time.time() - started) * 1000)
        fb.insert_event({
            "agent_type": "omni-brain",
            "provider": "local",
            "model": "fs",
            "task_type": "file-edit",
            "success": False,
            "reward": -0.5,
            "latency_ms": latency_ms,
            "meta": {"op": "create", "path": req.path, "error": str(e)},
        })
        return {"ok": False, "error": str(e)}


class FileReadRequest(BaseModel):
    path: str


@router.get("/health")
async def files_health():
    """
    Health check endpoint za file-edit storitve.
    Preveri dostopnost in osnovne funkcionalnosti.
    """
    try:
        # Preveri dostop do root direktorija
        root = _get_edit_root()
        if not root.exists():
            return {"status": "unhealthy", "error": "root_directory_not_accessible"}
        
        # Preveri pisalne pravice (poskusi ustvariti temp datoteko)
        test_file = root / "tmp_health_check.txt"
        try:
            with open(test_file, "w") as f:
                f.write("health_check")
            test_file.unlink()  # Pobriši test datoteko
        except Exception as e:
            return {"status": "unhealthy", "error": f"write_permission_denied: {str(e)}"}
        
        # Preveri FeedbackStore povezavo
        try:
            fb = FeedbackStore()
            # Poskusi osnovni query
            fb.get_recent_events(limit=1)
        except Exception as e:
            return {"status": "degraded", "warning": f"feedback_store_issue: {str(e)}"}
        
        return {
            "status": "healthy",
            "root_directory": str(root),
            "permissions": "read_write",
            "feedback_store": "connected",
            "endpoints": [
                "/files/create",
                "/files/rewrite", 
                "/files/update",
                "/files/read",
                "/files/health"
            ]
        }
    except Exception as e:
        return {"status": "unhealthy", "error": f"unexpected_error: {str(e)}"}


@router.post("/read")
async def files_read(req: FileReadRequest, auth: Dict[str, Any] = Depends(require_api_key)):
    """
    Prebere vsebino datoteke z varnostnimi omejitvami.
    """
    fb = FeedbackStore()
    started = time.time()
    try:
        target = _resolve_safe(req.path)
        if not target.exists():
            return {"ok": False, "error": "not_found"}
        
        if not target.is_file():
            return {"ok": False, "error": "not_a_file"}
        
        # Preveri velikost datoteke (omejitev na 10MB)
        file_size = target.stat().st_size
        if file_size > 10 * 1024 * 1024:  # 10MB
            return {"ok": False, "error": "file_too_large"}
        
        # Preberi datoteko
        try:
            with open(target, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # Poskusi z binary načinom za ne-tekstovne datoteke
            with open(target, "rb") as f:
                raw_content = f.read()
                # Vrni base64 encoded za binary datoteke
                import base64
                content = base64.b64encode(raw_content).decode("ascii")
                is_binary = True
        else:
            is_binary = False
        
        latency_ms = int((time.time() - started) * 1000)
        
        # Zabeleži uspešno operacijo
        fb.insert_event({
            "agent_type": "omni-brain",
            "provider": "local",
            "model": "fs",
            "task_type": "file-read",
            "success": True,
            "reward": 0.8,
            "latency_ms": latency_ms,
            "meta": {
                "op": "read", 
                "path": req.path, 
                "size_bytes": file_size,
                "is_binary": is_binary
            },
        })
        
        return {
            "ok": True, 
            "path": str(target), 
            "content": content,
            "size_bytes": file_size,
            "is_binary": is_binary,
            "latency_ms": latency_ms
        }
        
    except Exception as e:
        latency_ms = int((time.time() - started) * 1000)
        fb.insert_event({
            "agent_type": "omni-brain",
            "provider": "local",
            "model": "fs",
            "task_type": "file-read",
            "success": False,
            "reward": -0.5,
            "latency_ms": latency_ms,
            "meta": {"op": "read", "path": req.path, "error": str(e)},
        })
        return {"ok": False, "error": str(e)}


@router.post("/rewrite")
async def files_rewrite(req: FileRewriteRequest, auth: Dict[str, Any] = Depends(require_api_key)):
    fb = FeedbackStore()
    started = time.time()
    try:
        target = _resolve_safe(req.path)
        if not target.exists():
            return {"ok": False, "error": "not_found"}
        data = req.content.encode("utf-8")
        with open(target, "wb") as f:
            f.write(data)
        latency_ms = int((time.time() - started) * 1000)
        fb.insert_event({
            "agent_type": "omni-brain",
            "provider": "local",
            "model": "fs",
            "task_type": "file-edit",
            "success": True,
            "reward": min(1.0, len(data) / 5000.0),
            "latency_ms": latency_ms,
            "meta": {"op": "rewrite", "path": req.path},
        })
        return {"ok": True, "path": str(target), "bytes_written": len(data), "latency_ms": latency_ms}
    except Exception as e:
        latency_ms = int((time.time() - started) * 1000)
        fb.insert_event({
            "agent_type": "omni-brain",
            "provider": "local",
            "model": "fs",
            "task_type": "file-edit",
            "success": False,
            "reward": -0.5,
            "latency_ms": latency_ms,
            "meta": {"op": "rewrite", "path": req.path, "error": str(e)},
        })
        return {"ok": False, "error": str(e)}


@router.post("/update")
async def files_update(req: FileUpdateRequest, auth: Dict[str, Any] = Depends(require_api_key)):
    fb = FeedbackStore()
    started = time.time()
    try:
        target = _resolve_safe(req.path)
        if not target.exists():
            return {"ok": False, "error": "not_found"}
        text = target.read_text(encoding="utf-8")
        idx = text.find(req.old_str)
        if idx == -1:
            return {"ok": False, "error": "search_not_found"}
        new_text = text.replace(req.old_str, req.new_str, 1)
        target.write_text(new_text, encoding="utf-8")
        latency_ms = int((time.time() - started) * 1000)
        fb.insert_event({
            "agent_type": "omni-brain",
            "provider": "local",
            "model": "fs",
            "task_type": "file-edit",
            "success": True,
            "reward": 0.5,
            "latency_ms": latency_ms,
            "meta": {"op": "update", "path": req.path},
        })
        return {"ok": True, "path": str(target), "latency_ms": latency_ms}
    except Exception as e:
        latency_ms = int((time.time() - started) * 1000)
        fb.insert_event({
            "agent_type": "omni-brain",
            "provider": "local",
            "model": "fs",
            "task_type": "file-edit",
            "success": False,
            "reward": -0.5,
            "latency_ms": latency_ms,
            "meta": {"op": "update", "path": req.path, "error": str(e)},
        })
        return {"ok": False, "error": str(e)}