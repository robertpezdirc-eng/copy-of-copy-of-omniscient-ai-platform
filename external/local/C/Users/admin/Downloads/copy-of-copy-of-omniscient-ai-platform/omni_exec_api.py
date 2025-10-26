#!/usr/bin/env python3
"""
OMNI Exec API (Flask)
- Cloud-ready mikroservis za sinhrono in asinkrono izvajanje ukazov/sekvenc
- Async prek Cloud Tasks (produkcija) ali lokalni fallback (thread)
- Status opravil v Google Cloud Storage (če je nastavljen bucket) ali v pomnilniku
"""
import os
import json
import time
import uuid
import threading
from datetime import datetime
from typing import Optional, Dict, Any
from flask import Flask, request, jsonify
from flask_cors import CORS

# Google Cloud Logging (neobvezno)
try:
    from google.cloud import logging as gcloud_logging  # type: ignore
    _gcl_client = gcloud_logging.Client()
    _gcl_client.setup_logging()
except Exception:
    _gcl_client = None

# Google Cloud Tasks (neobvezno)
try:
    from google.cloud import tasks_v2  # type: ignore
except Exception:  # pragma: no cover
    tasks_v2 = None  # type: ignore

# Google Cloud Storage (neobvezno)
try:
    from google.cloud import storage  # type: ignore
except Exception:  # pragma: no cover
    storage = None  # type: ignore

app = Flask(__name__)
# Enable CORS for Exec API (configure allowed origins via env)
_allowed = os.getenv("OMNI_FRONTEND_ORIGIN") or "*"
_extra = os.getenv("OMNI_FRONTEND_EXTRA_ORIGINS", "")
_origins = "*" if _allowed == "*" else [o for o in (_allowed + " " + _extra).split() if o]
try:
    CORS(app, resources={r"/api/*": {"origins": _origins}})
except Exception:
    pass


SERVICE_NAME = os.getenv("SERVICE_NAME", "omni-exec-api")
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
REGION = os.getenv("REGION", "europe-west1")

# Async konfiguracija (Cloud Tasks)
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID")
CLOUD_TASKS_LOCATION = os.getenv("CLOUD_TASKS_LOCATION", "europe-west1")
CLOUD_TASKS_QUEUE = os.getenv("CLOUD_TASKS_QUEUE", "omni-exec-queue")
CLOUD_RUN_SERVICE_URL = os.getenv("CLOUD_RUN_SERVICE_URL")  # npr. https://omni-exec-api-xxxxx-uc.a.run.app
TASKS_SERVICE_ACCOUNT_EMAIL = os.getenv("TASKS_SERVICE_ACCOUNT_EMAIL")  # SA za OIDC token
USE_LOCAL_ASYNC = os.getenv("USE_LOCAL_ASYNC", "0") == "1"

# Status storage (GCS ali v pomnilniku)
GCS_BUCKET = os.getenv("OMNI_STATUS_BUCKET")
_storage_client = storage.Client() if (storage and GCS_BUCKET) else None

# Lokalni spomin kot fallback
_TASKS: Dict[str, Dict[str, Any]] = {}


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": SERVICE_NAME,
        "env": ENVIRONMENT,
        "region": REGION,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/status")
def api_status():
    return {
        "ok": True,
        "tasks_total": len(_TASKS),
        "running": [tid for tid, t in _TASKS.items() if t.get("status") == "running"],
        "completed": [tid for tid, t in _TASKS.items() if str(t.get("status", "")).startswith("done")],
        "uses_gcs": bool(_storage_client),
        "uses_cloud_tasks": bool(tasks_v2 and PROJECT_ID and CLOUD_RUN_SERVICE_URL and TASKS_SERVICE_ACCOUNT_EMAIL),
    }


@app.post("/api/execute")
def api_execute():
    payload = request.get_json(silent=True) or {}
    command = (payload.get("command") or payload.get("prompt") or "").strip()
    strategy = payload.get("strategy")

    if not command:
        return jsonify({"ok": False, "error": "Missing 'command'"}), 400

    task_id = _init_job(command, strategy)

    # Sinhrona izvedba (demo)
    try:
        result_text = _run_command(command, strategy)
        _mark_job_done(task_id, {"text": result_text})
        return {"ok": True, "task_id": task_id, "result": {"text": result_text}}
    except Exception as e:  # pragma: no cover
        _mark_job_error(task_id, str(e))
        return jsonify({"ok": False, "task_id": task_id, "error": str(e)}), 500


@app.post("/api/execute_async")
def api_execute_async():
    payload = request.get_json(silent=True) or {}
    command = (payload.get("command") or payload.get("prompt") or "").strip()
    strategy = payload.get("strategy")

    if not command:
        return jsonify({"ok": False, "error": "Missing 'command'"}), 400

    task_id = _init_job(command, strategy)

    # Če je na voljo Cloud Tasks konfiguracija, objavi opravilo
    if tasks_v2 and PROJECT_ID and CLOUD_RUN_SERVICE_URL and TASKS_SERVICE_ACCOUNT_EMAIL and not USE_LOCAL_ASYNC:
        try:
            _enqueue_cloud_task(task_id, command, strategy)
            return {"ok": True, "task_id": task_id, "enqueued": True, "mode": "cloud_tasks"}
        except Exception as e:  # pragma: no cover
            _mark_job_error(task_id, f"Cloud Tasks enqueue failed: {e}")
            return jsonify({"ok": False, "task_id": task_id, "error": str(e)}), 500
    
    # Lokalni fallback (thread)
    threading.Thread(target=_worker_execute, args=(task_id, command, strategy), daemon=True).start()
    return {"ok": True, "task_id": task_id, "enqueued": True, "mode": "local_thread"}


@app.post("/api/_task_execute")
def task_execute_handler():
    # Handler za Cloud Tasks: izvede opravilo v ozadju
    payload = request.get_json(force=True)
    task_id = payload.get("task_id")
    command = payload.get("command")
    strategy = payload.get("strategy")
    if not task_id or not command:
        return jsonify({"ok": False, "error": "Missing task_id/command"}), 400

    _worker_execute(task_id, command, strategy)
    return {"ok": True, "task_id": task_id}


@app.get("/api/job/<task_id>")
def api_job_status(task_id: str):
    job = _load_job(task_id)
    if not job:
        return jsonify({"ok": False, "error": "Not found"}), 404
    return {"ok": True, "job": job}


# -------------------------
# Pomožne funkcije
# -------------------------

def _init_job(command: str, strategy: Optional[str]) -> str:
    task_id = str(uuid.uuid4())
    job = {
        "id": task_id,
        "status": "running",
        "created": time.time(),
        "command": command,
        "strategy": strategy,
        "result": None,
    }
    _TASKS[task_id] = job
    _save_job(task_id, job)
    return task_id


def _mark_job_done(task_id: str, result: Dict[str, Any]):
    job = _TASKS.get(task_id) or {"id": task_id}
    job.update({"status": "done_ok", "result": result, "completed": time.time()})
    _TASKS[task_id] = job
    _save_job(task_id, job)


def _mark_job_error(task_id: str, error_msg: str):
    job = _TASKS.get(task_id) or {"id": task_id}
    job.update({"status": "done_error", "result": {"error": error_msg}, "completed": time.time()})
    _TASKS[task_id] = job
    _save_job(task_id, job)


def _run_command(command: str, strategy: Optional[str]) -> str:
    # Slash bližnjice -> strategije
    if command.startswith("/"):
        head, *rest = command.split(maxsplit=1)
        rem = rest[0] if rest else ""
        m = {
            "/ensemble": "ENSEMBLE INTELLECT",
            "/meta": "META-AGENT",
            "/fusion": "MULTIMODAL FUSION ENGINE",
            "/self": "SELF-OPTIMIZING LOOP",
            "/hyper": "HYPER PROMPT PIPELINE",
        }
        strategy = m.get(head.lower(), strategy)
        command = rem
    # Demo izvedba – v praksi pokliči orkestrator/LLM/pipeline
    time.sleep(1.0)
    if strategy:
        return f"[strategy={strategy}] {command} => izvedeno"
    return f"{command} => izvedeno"


def _worker_execute(task_id: str, command: str, strategy: Optional[str]):
    try:
        result_text = _run_command(command, strategy)
        _mark_job_done(task_id, {"text": result_text})
    except Exception as e:  # pragma: no cover
        _mark_job_error(task_id, str(e))


def _enqueue_cloud_task(task_id: str, command: str, strategy: Optional[str]):
    if not tasks_v2:
        raise RuntimeError("google-cloud-tasks ni nameščen")
    if not (PROJECT_ID and CLOUD_TASKS_LOCATION and CLOUD_TASKS_QUEUE and CLOUD_RUN_SERVICE_URL and TASKS_SERVICE_ACCOUNT_EMAIL):
        raise RuntimeError("Manjka Cloud Tasks konfiguracija")

    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(PROJECT_ID, CLOUD_TASKS_LOCATION, CLOUD_TASKS_QUEUE)

    url = CLOUD_RUN_SERVICE_URL.rstrip("/") + "/api/_task_execute"
    payload = json.dumps({"task_id": task_id, "command": command, "strategy": strategy}).encode()

    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": url,
            "headers": {"Content-Type": "application/json"},
            "body": payload,
            "oidc_token": {"service_account_email": TASKS_SERVICE_ACCOUNT_EMAIL},
        }
    }

    response = client.create_task(request={"parent": parent, "task": task})
    return response.name


def _save_job(task_id: str, job: Dict[str, Any]):
    if _storage_client and GCS_BUCKET:
        try:
            bucket = _storage_client.bucket(GCS_BUCKET)
            blob = bucket.blob(f"jobs/{task_id}.json")
            blob.cache_control = "no-store"
            blob.upload_from_string(json.dumps(job), content_type="application/json")
            return
        except Exception:
            pass  # fallback na memory
    _TASKS[task_id] = job


def _load_job(task_id: str) -> Optional[Dict[str, Any]]:
    if _storage_client and GCS_BUCKET:
        try:
            bucket = _storage_client.bucket(GCS_BUCKET)
            blob = bucket.blob(f"jobs/{task_id}.json")
            if blob.exists():
                data = blob.download_as_text()
                return json.loads(data)
        except Exception:
            pass
    return _TASKS.get(task_id)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8082))
    app.run(host="0.0.0.0", port=port)