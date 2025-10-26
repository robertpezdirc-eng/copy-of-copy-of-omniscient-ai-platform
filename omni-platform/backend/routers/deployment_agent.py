import os
import json
import time
import uuid
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/deployment", tags=["deployment"])

STORE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
JOBS_FILE = os.path.join(STORE_DIR, "provision_jobs.json")
BRAND_FILE = os.path.join(STORE_DIR, "branding_store.json")
GEO_JOBS_FILE = os.path.join(STORE_DIR, "geo_jobs.json")
DB_CONFIG_FILE = os.path.join(STORE_DIR, "db_config.json")
DB_SYNC_FILE = os.path.join(STORE_DIR, "db_sync_jobs.json")


def _ensure_store():
    os.makedirs(STORE_DIR, exist_ok=True)
    for path in (JOBS_FILE, BRAND_FILE, GEO_JOBS_FILE, DB_CONFIG_FILE, DB_SYNC_FILE):
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump({}, f)


def _load_json(path: str) -> Dict[str, Any]:
    _ensure_store()
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _save_json(path: str, data: Dict[str, Any]):
    _ensure_store()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


@router.post("/provision")
def provision_instance(payload: Dict[str, Any]) -> Dict[str, Any]:
    tenant_id = payload.get("tenant_id")
    strategy = payload.get("strategy", "kubernetes")  # "docker" or "kubernetes"
    region = payload.get("region", "eu-central")
    replicas = int(payload.get("replicas", 1))
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")

    jobs = _load_json(JOBS_FILE)
    job_id = uuid.uuid4().hex
    manifest: Dict[str, Any]
    if strategy == "docker":
        manifest = {
            "type": "docker-compose",
            "services": {
                f"app-{tenant_id}": {
                    "image": payload.get("image", "omniscient/platform:latest"),
                    "ports": [payload.get("port", 8000)],
                    "environment": payload.get("env", {}),
                    "deploy": {
                        "replicas": replicas,
                        "restart_policy": "always",
                    },
                }
            },
        }
    else:
        manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": f"app-{tenant_id}", "labels": {"tenant": tenant_id}},
            "spec": {
                "replicas": replicas,
                "selector": {"matchLabels": {"app": f"app-{tenant_id}"}},
                "template": {
                    "metadata": {"labels": {"app": f"app-{tenant_id}", "tenant": tenant_id}},
                    "spec": {
                        "containers": [{
                            "name": "app",
                            "image": payload.get("image", "omniscient/platform:latest"),
                            "ports": [{"containerPort": payload.get("port", 8000)}],
                            "env": [{"name": k, "value": str(v)} for k, v in (payload.get("env", {}) or {}).items()],
                        }],
                    },
                },
            },
        }
    job = {
        "id": job_id,
        "tenant_id": tenant_id,
        "strategy": strategy,
        "region": region,
        "status": "queued",
        "created_at": int(time.time() * 1000),
        "manifest": manifest,
    }
    jobs[job_id] = job
    _save_json(JOBS_FILE, jobs)
    return {"enqueued": True, "job": job}


@router.get("/status/{job_id}")
def provision_status(job_id: str) -> Dict[str, Any]:
    jobs = _load_json(JOBS_FILE)
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    # Simulate async progression
    if job.get("status") == "queued" and (int(time.time() * 1000) - job.get("created_at", 0)) > 2000:
        job["status"] = "provisioned"
        jobs[job_id] = job
        _save_json(JOBS_FILE, jobs)
    return {"job": job}


@router.post("/branding/update")
def update_branding(payload: Dict[str, Any]) -> Dict[str, Any]:
    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    branding = _load_json(BRAND_FILE)
    item = branding.get(tenant_id) or {"tenant_id": tenant_id}
    if "logo_url" in payload:
        item["logo_url"] = payload["logo_url"]
    if "primary_color" in payload:
        item["primary_color"] = payload["primary_color"]
    if "secondary_color" in payload:
        item["secondary_color"] = payload["secondary_color"]
    item["updated_at"] = int(time.time() * 1000)
    branding[tenant_id] = item
    _save_json(BRAND_FILE, branding)
    return {"updated": True, "branding": item}


@router.get("/branding/{tenant_id}")
def get_branding(tenant_id: str) -> Dict[str, Any]:
    branding = _load_json(BRAND_FILE)
    item = branding.get(tenant_id)
    if not item:
        return {"found": False}
    return {"found": True, "branding": item}


@router.post("/geo/provision")
def geo_provision(payload: Dict[str, Any]) -> Dict[str, Any]:
    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    regions = payload.get("regions") or ["eu-central-1", "us-east-1"]
    clouds = payload.get("clouds") or ["aws", "gcp"]
    strategy = payload.get("strategy", "kubernetes")
    services = payload.get("services") or ["api", "worker", "db"]

    jobs = _load_json(GEO_JOBS_FILE)
    job_id = uuid.uuid4().hex
    job = {
        "id": job_id,
        "tenant_id": tenant_id,
        "regions": regions,
        "clouds": clouds,
        "strategy": strategy,
        "services": services,
        "status": "queued",
        "created_at": int(time.time() * 1000),
    }
    jobs[job_id] = job
    _save_json(GEO_JOBS_FILE, jobs)
    return {"enqueued": True, "job": job}


@router.get("/geo/status/{job_id}")
def geo_status(job_id: str) -> Dict[str, Any]:
    jobs = _load_json(GEO_JOBS_FILE)
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if job.get("status") == "queued" and (int(time.time() * 1000) - job.get("created_at", 0)) > 2000:
        job["status"] = "provisioned"
        jobs[job_id] = job
        _save_json(GEO_JOBS_FILE, jobs)
    return {"job": job}


@router.post("/db/config")
def set_db_config(payload: Dict[str, Any]) -> Dict[str, Any]:
    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    engine = payload.get("engine", "cockroachdb")
    regions = payload.get("regions") or ["eu-central", "us-east"]
    replication_factor = int(payload.get("replication_factor", 3))

    store = _load_json(DB_CONFIG_FILE)
    cfg = {
        "tenant_id": tenant_id,
        "engine": engine,
        "regions": regions,
        "replication_factor": replication_factor,
        "updated_at": int(time.time() * 1000),
    }
    store[tenant_id] = cfg
    _save_json(DB_CONFIG_FILE, store)
    return {"updated": True, "config": cfg}


@router.get("/db/config/{tenant_id}")
def get_db_config(tenant_id: str) -> Dict[str, Any]:
    store = _load_json(DB_CONFIG_FILE)
    cfg = store.get(tenant_id)
    if not cfg:
        return {"found": False}
    return {"found": True, "config": cfg}


@router.post("/db/sync/start")
def db_sync_start(payload: Dict[str, Any]) -> Dict[str, Any]:
    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    mode = payload.get("mode", "bidirectional")
    batches = int(payload.get("batches", 1))

    jobs = _load_json(DB_SYNC_FILE)
    job_id = uuid.uuid4().hex
    job = {
        "id": job_id,
        "tenant_id": tenant_id,
        "mode": mode,
        "batches": batches,
        "status": "queued",
        "created_at": int(time.time() * 1000),
    }
    jobs[job_id] = job
    _save_json(DB_SYNC_FILE, jobs)
    return {"enqueued": True, "job": job}


@router.get("/db/sync/status/{job_id}")
def db_sync_status(job_id: str) -> Dict[str, Any]:
    jobs = _load_json(DB_SYNC_FILE)
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if job.get("status") == "queued" and (int(time.time() * 1000) - job.get("created_at", 0)) > 2000:
        job["status"] = "completed"
        jobs[job_id] = job
        _save_json(DB_SYNC_FILE, jobs)
    return {"job": job}