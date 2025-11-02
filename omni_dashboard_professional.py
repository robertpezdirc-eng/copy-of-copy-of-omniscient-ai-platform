# Global Google Cloud manager instance (initialized safely below)
# google_cloud_manager will be initialized with a stub to avoid import issues

# Initialize enterprise dashboard at module import for Uvicorn
# Export FastAPI app so that `uvicorn omni_dashboard_professional:app` works
from typing import Dict, Any, List, Tuple, Optional
import os
import base64
import tempfile
import json
import time
import threading
import platform
from datetime import datetime
import psutil
import requests
import sqlite3
import asyncio
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

# Force UTF-8 stdout/stderr to avoid UnicodeEncodeError on Windows consoles
try:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Resolve dashboard class (fallback to operational dashboard if professional is unavailable)
try:
    from omni_operational_dashboard import OmniOperationalDashboard as OmniProfessionalDashboard
except Exception as e:
    from fastapi import FastAPI
    class OmniProfessionalDashboard:
        def __init__(self):
            self.app = FastAPI(title="Omni Dashboard (fallback)")
            @self.app.get("/")
            async def root():
                return {"ok": True, "message": "Fallback Omni Dashboard", "error": str(e)}
        def run(self, host: str = "0.0.0.0", port: int = 8080):
            import uvicorn
            uvicorn.run(self.app, host=host, port=port)

# Initialize cloud manager safely (stubbed until dynamic GCS integration is configured below)
class _GlobalCloudManagerStub:
    connected = False
    def get_google_cloud_status(self):
        return {"google_cloud_connected": False, "connected_services": []}

google_cloud_manager = _GlobalCloudManagerStub()

# Initialize enterprise dashboard at module import for Uvicorn
# Export FastAPI app so that `uvicorn omni_dashboard_professional:app` works

dashboard = OmniProfessionalDashboard()
app = dashboard.app
# Agentic orchestration router
try:
    from orchestration.agentic_orchestrator import router as orchestration_router
    app.include_router(orchestration_router)
except Exception as e:
    # Avoid crashing on import failure; log and continue
    print(f"[Orchestration] Router not loaded: {e}")

# Health and readiness endpoints
@app.get("/healthz")
async def healthz():
    try:
        uptime = time.time() - getattr(dashboard, "start_time", time.time())
    except Exception:
        uptime = 0
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": uptime,
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "memory_percent": psutil.virtual_memory().percent,
            "threads": threading.active_count(),
            "platform": platform.system()
        }
    }

@app.get("/readyz")
async def readyz():
    dynamic_cloud_configured = bool('cloud_manager' in globals() and globals().get('cloud_manager'))
    dynamic_cloud_connected = bool('cloud_manager' in globals() and globals().get('cloud_manager') and getattr(globals().get('cloud_manager'), 'connected', False))
    ready_checks = {
        "app_initialized": app is not None,
        "dashboard_initialized": dashboard is not None,
        "cloud_configured": bool(os.getenv("GCS_BUCKET")) or dynamic_cloud_configured,
        "google_cloud_connected": dynamic_cloud_connected,
    }
    overall_ready = all(ready_checks.values()) if ready_checks else True
    return {
        "ready": overall_ready,
        "checks": ready_checks,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    return await healthz()

@app.get("/api/health")
async def api_health():
    try:
        uptime = time.time() - getattr(dashboard, "start_time", time.time())
    except Exception:
        uptime = 0
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": uptime,
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "memory_percent": psutil.virtual_memory().percent,
            "threads": threading.active_count()
        }
    }

# Platform status endpoint
@app.get("/api/platform/status")
def api_platform_status():
    try:
        summary = {}
        try:
            summary = dashboard._get_metrics_summary()
        except Exception:
            summary = {"overall_health": "unknown"}
        try:
            overall_health = dashboard._calculate_overall_health()
        except Exception:
            overall_health = "unknown"
        try:
            quantum = dashboard.get_quantum_status()
        except Exception:
            quantum = {"available": False}
        try:
            openai = dashboard.get_openai_status()
        except Exception:
            openai = {"available": False}
        try:
            cloud = get_google_cloud_status()
        except Exception:
            cloud = {"google_cloud_connected": False}
        readiness_checks = {
            "app_initialized": app is not None,
            "dashboard_initialized": dashboard is not None,
            "cloud_configured": bool(os.getenv("GCS_BUCKET")),
            "google_cloud_connected": bool(cloud.get("google_cloud_connected")) or bool(cloud.get("connected_services")),
        }
        latest_metrics = None
        try:
            latest_metrics = dashboard.metrics_history[-1]._asdict() if hasattr(dashboard.metrics_history[-1], "_asdict") else None
        except Exception:
            latest_metrics = None
        return {
            "timestamp": datetime.now().isoformat(),
            "ready": all(readiness_checks.values()),
            "checks": readiness_checks,
            "summary": summary,
            "overall_health": overall_health,
            "quantum": quantum,
            "openai": openai,
            "cloud": cloud,
            "latest_metrics": latest_metrics,
        }
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.now().isoformat()}

# Optionally set up GCP credentials from base64 JSON in env (Cloud Run-friendly)
b64_key = os.getenv("GCP_SERVICE_ACCOUNT_KEY_B64") or os.getenv("GCP_SERVICE_ACCOUNT_KEY")
if b64_key:
    try:
        creds_path = os.path.join(tempfile.gettempdir(), "gcp_creds.json")
        with open(creds_path, "wb") as f:
            f.write(base64.b64decode(b64_key))
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
        print(f"[GCS] Credentials written to {creds_path}")
    except Exception as e:
        print(f"[GCS] Failed to write credentials: {e}")

# Initialize Cloud Storage integration if bucket is provided via env
cloud_manager = None
bucket = os.getenv("GCS_BUCKET")
prefix = os.getenv("GCS_PREFIX", "")
try:
    from omni_platform.googlecloud.storage_integration import CloudStorageManager
    if bucket:
        cloud_manager = CloudStorageManager(bucket_name=bucket, prefix=prefix, polling_interval=int(os.getenv("GCS_POLL_INTERVAL", "15")))
        if cloud_manager.connect():
            cloud_manager.start_indexing()
            print(f"[GCS] Connected to bucket '{bucket}' with prefix '{prefix}'")
        else:
            print(f"[GCS] Could not connect to bucket '{bucket}': {cloud_manager.error}")
    else:
        print("[GCS] No bucket configured. Set env GCS_BUCKET to enable cloud indexing.")
except Exception as e:
    print(f"[GCS] Cloud storage integration not available: {e}")

from fastapi import Body, Query
from fastapi.responses import HTMLResponse, RedirectResponse

# Preusmeri glavno stran na profesionalni dashboard UI (/command)
@app.get("/", response_class=HTMLResponse)
async def root_redirect():
    return RedirectResponse(url="/command")

# ---------------------- Command Line UI ----------------------
@app.get("/command", response_class=HTMLResponse)
async def command_ui():
    return """
<!doctype html>
<html lang=\"sl\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>OMNI Command</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; background:#0b0f17; color:#e5e7eb; margin:0; }
    .wrap { max-width: 880px; margin: 48px auto; padding: 0 16px; }
    h1 { font-size: 20px; font-weight: 600; color:#93c5fd; margin: 0 0 12px; }
    .bar { display:flex; gap:8px; }
    input[type=text] { flex:1; background:#111827; color:#e5e7eb; border:1px solid #1f2937; border-radius:8px; padding:12px 14px; outline:none; }
    input[type=text]:focus { border-color:#2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,0.25); }
    button { background:#2563eb; color:white; border:none; border-radius:8px; padding:12px 16px; cursor:pointer; }
    button:disabled { opacity:0.6; cursor:not-allowed; }
    .out { margin-top:16px; background:#0f172a; border:1px solid #1f2937; border-radius:8px; padding:12px; white-space:pre-wrap; }
    .hint { color:#9ca3af; font-size: 12px; margin: 8px 2px 16px; }
    .trace { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size:12px; color:#9ca3af; margin-top:8px; }
    .ok { color:#34d399; }
    .err { color:#f87171; }
    code{ background:#111827; padding:2px 6px; border-radius:6px; }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <h1>OMNI Ukazna vrstica</h1>
    <div class=\"hint\">Uporabi: <code>/ensemble</code>, <code>/meta</code>, <code>/fusion</code>, <code>/self</code>, <code>/hyper</code> + besedilo. Brez predpone pošlje privzeto strategijo.</div>
    <div class=\"bar\">
      <input id=\"cmd\" type=\"text\" placeholder=\"Vpiši ukaz ali vprašanje in pritisni Enter...\" />
      <button id=\"go\">Pošlji</button>
    </div>
    <div id=\"out\" class=\"out\">Pripravljen.</div>
    <div id=\"trace\" class=\"trace\"></div>
  </div>
<script>
const el = (id)=>document.getElementById(id);
const out = el('out');
const trace = el('trace');
// Async Exec API integration
const execApiBase = (window.OMNI_EXEC_API_BASE || window.OMNI_API_BASE || 'http://localhost:8082');
async function sendAsync(){
  const v = el('cmd').value.trim();
  if(!v){ return; }
  out.textContent = '⏳ Pošiljam v Exec API...'; trace.textContent = '';
  try {
    const res = await fetch(execApiBase + '/api/execute_async', {
      method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ command: v })
    });
    const data = await res.json();
    if(data && data.ok){
      const jobId = data.task_id; setJob(jobId, 'queued'); pollJob(jobId);
    } else {
      out.innerHTML = '<span class=\'err\'>✖</span> ' + ((data && data.error) || 'Napaka pri pošiljanju');
    }
  } catch (e) {
    out.innerHTML = '<span class=\'err\'>✖</span> ' + e;
  }
}
function setJob(id, state){
  const jobid = document.getElementById('jobid');
  const jobstate = document.getElementById('jobstate');
  if(jobid) jobid.textContent = id || '-';
  if(jobstate) jobstate.textContent = state || '';
}
async function pollJob(jobId){
  try {
    const res = await fetch(execApiBase + '/api/job/' + encodeURIComponent(jobId));
    const data = await res.json();
    if(!data.ok){ setJob(jobId, 'napaka'); return; }
    const job = data.job || {};
    setJob(jobId, job.status || '');
    if((job.status||'').startsWith('done')){
      if(job.result && job.result.text){ out.innerHTML = '<span class=\'ok\'>✔</span> ' + job.result.text; }
      else if(job.result && job.result.error){ out.innerHTML = '<span class=\'err\'>✖</span> ' + job.result.error; }
      return;
    }
    setTimeout(()=>pollJob(jobId), 1500);
  } catch (e) {
    setJob(jobId, 'napaka');
  }
}
async function run(){
  const v = el('cmd').value.trim();
  if(!v){ return; }
  out.textContent = '⏳ Pošiljam...'; trace.textContent = '';
  el('go').disabled = true;
  try {
    const res = await fetch('/api/command', {
      method:'POST',
      headers: { 'Content-Type':'application/json' },
      body: JSON.stringify({ command: v })
    });
    const data = await res.json();
    if(data.ok){
      const text = data.reply || data.text || JSON.stringify(data, null, 2);
      out.innerHTML = '<span class=\'ok\'>✔</span> ' + (text || '(prazno)');
    } else {
      out.innerHTML = '<span class=\'err\'>✖</span> ' + (data.error || 'Napaka');
    }
    if (data.trace) trace.textContent = 'trace: ' + JSON.stringify(data.trace);
  } catch (e) {
    out.innerHTML = '<span class=\'err\'>✖</span> ' + e;
  } finally {
    el('go').disabled = false;
  }
}
el('go').onclick = run;
(function(){
  const bar = document.querySelector('.bar');
  if (bar && !document.getElementById('goAsync')) {
    const btn = document.createElement('button');
    btn.id = 'goAsync';
    btn.textContent = 'Pošlji v Exec API';
    bar.appendChild(btn);
    btn.addEventListener('click', sendAsync);
  }
  const wrap = document.querySelector('.wrap');
  if (wrap && !document.getElementById('jobui')) {
    const div = document.createElement('div');
    div.className = 'hint';
    div.id = 'jobui';
    div.innerHTML = 'Async job: <span id="jobid">-</span> <span id="jobstate"></span>';
    const traceEl = document.getElementById('trace');
    wrap.insertBefore(div, traceEl);
  }
})();
el('cmd').addEventListener('keydown', (e)=>{ if(e.key==='Enter'){ run(); }});
</script>
</body>
</html>
"""

@app.post("/api/command")
def api_command(payload: Dict[str, Any] = Body(...)):
    cmd = (payload.get("command") or payload.get("input") or "").strip()
    if not cmd:
        return {"ok": False, "error": "Missing 'command'"}
    prompt = cmd
    strategy = None
    # Podpora slash bližnjicam
    if cmd.startswith("/"):
        parts = cmd.split(None, 1)
        head = parts[0].lower()
        prompt = parts[1] if len(parts) > 1 else ""
        if head in ("/ensemble", "/e"): strategy = "ENSEMBLE INTELLECT"
        elif head in ("/meta", "/m"): strategy = "META-AGENT"
        elif head in ("/fusion", "/f"): strategy = "MULTIMODAL FUSION ENGINE"
        elif head in ("/self", "/s"): strategy = "SELF-OPTIMIZING LOOP"
        elif head in ("/hyper", "/h"): strategy = "HYPER PROMPT PIPELINE"
        elif head.startswith("/strategy"):
            if "=" in head:
                strategy = head.split("=",1)[1].replace("-"," ").upper()
    payload2 = {"prompt": prompt}
    if strategy:
        payload2["strategy"] = strategy
    try:
        # Uporabi obstoječi orkestrator za generiranje odgovora
        result = _orchestrate_generate(payload2)
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)}


# Cloud file APIs: connect, list, upload, preview, process
@app.post("/api/cloud/connect")
def api_cloud_connect(payload: Dict[str, str] = Body(...)):
    global cloud_manager  # reuse module-level variable
    bucket_name = payload.get("bucket")
    prefix_local = payload.get("prefix", "")
    if not bucket_name:
        return {"ok": False, "error": "Missing 'bucket' in payload"}
    try:
        # Accept dynamic credentials via Base64 to avoid server restart
        key_b64 = payload.get("key_base64") or payload.get("service_account_base64")
        project_id = payload.get("project_id") or payload.get("gcp_project")
        region = payload.get("region") or payload.get("gcp_region")
        if key_b64:
            import base64, tempfile
            creds_path = os.path.join(tempfile.gettempdir(), "gcp_creds_dynamic.json")
            with open(creds_path, "wb") as f:
                f.write(base64.b64decode(key_b64))
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
        if project_id:
            os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
        if region:
            os.environ["GOOGLE_CLOUD_REGION"] = region
        # Import CloudStorageManager at call-time to avoid import issues at module import
        from omni_platform.googlecloud.storage_integration import CloudStorageManager
        cloud_manager = CloudStorageManager(bucket_name=bucket_name, prefix=prefix_local, polling_interval=int(os.getenv("GCS_POLL_INTERVAL", "15")))
        ok = cloud_manager.connect()
        if ok:
            cloud_manager.start_indexing()
            return {"ok": True, "bucket": bucket_name, "prefix": prefix_local, "count": len(cloud_manager.get_index())}
        return {"ok": False, "error": cloud_manager.error}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/cloud/files")
def api_cloud_files(limit: int = Query(200, ge=1, le=5000)):
    if not cloud_manager or not cloud_manager.connected:
        return {"ok": False, "error": "Cloud not connected"}
    files = cloud_manager.get_index()
    return {"ok": True, "bucket": cloud_manager.bucket_name, "prefix": cloud_manager.prefix, "count": min(len(files), limit), "files": files[:limit]}

@app.post("/api/cloud/upload")
def api_cloud_upload(payload: Dict[str, str] = Body(...)):
    if not cloud_manager or not cloud_manager.connected:
        return {"ok": False, "error": "Cloud not connected"}
    name = payload.get("name")
    content = payload.get("content", "")
    content_type = payload.get("content_type", "text/plain")
    if not name:
        return {"ok": False, "error": "Missing 'name'"}
    data = content.encode("utf-8")
    ok = cloud_manager.upload_bytes(name, data, content_type=content_type)
    if ok:
        cloud_manager.index_once()
        return {"ok": True, "name": name}
    return {"ok": False, "error": "Upload failed"}

@app.get("/api/cloud/preview")
def api_cloud_preview(name: str = Query(...)):
    if not cloud_manager or not cloud_manager.connected:
        return {"ok": False, "error": "Cloud not connected"}
    url = cloud_manager.generate_signed_url(name, expiration_seconds=int(os.getenv("GCS_SIGNED_URL_TTL", "3600")))
    if url:
        return {"ok": True, "name": name, "url": url}
    return {"ok": False, "error": "Signed URL not available; check credentials"}

@app.post("/api/cloud/process")
def api_cloud_process(payload: Dict[str, str] = Body(...)):
    if not cloud_manager or not cloud_manager.connected:
        return {"ok": False, "error": "Cloud not connected"}
    name = payload.get("name")
    operation = payload.get("operation", "uppercase")
    if not name:
        return {"ok": False, "error": "Missing 'name'"}
    data = cloud_manager.download_bytes(name)
    if data is None:
        return {"ok": False, "error": "File not found or read error"}
    result_bytes = data
    result_ct = "application/octet-stream"
    try:
        if operation == "uppercase":
            result_bytes = data.decode("utf-8", errors="ignore").upper().encode("utf-8")
            result_ct = "text/plain"
        elif operation == "identity":
            pass
        else:
            return {"ok": False, "error": f"Unsupported operation '{operation}'"}
        out_name = f"{name}.processed"
        ok = cloud_manager.upload_bytes(out_name, result_bytes, content_type=result_ct)
        if ok:
            cloud_manager.index_once()
            return {"ok": True, "name": name, "operation": operation, "output": out_name}
        return {"ok": False, "error": "Processing upload failed"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/find")
@app.get("/api/najdi")  # Czech alias
async def find_in_repository(
    query: str = Query(..., description="Search query for filenames or content"),
    search_type: str = Query("both", description="Search type: 'filename', 'content', or 'both'"),
    max_results: int = Query(50, description="Maximum number of results to return"),
    file_extensions: str = Query("", description="Comma-separated file extensions to include (e.g., 'py,js,html')")
):
    """
    Search for files and content in the repository
    Supports both filename and content search with configurable limits
    """
    try:
        import os
        import re
        from pathlib import Path
        
        # Define directories to ignore
        ignore_dirs = {
            '.git', '.venv', '__pycache__', 'node_modules', '.pytest_cache', 
            'build', 'dist', '.tmp', 'logs', '.firebase', 'published'
        }
        
        # Parse file extensions filter
        allowed_extensions = set()
        if file_extensions.strip():
            allowed_extensions = {ext.strip().lower() for ext in file_extensions.split(',')}
        
        results = []
        base_path = Path(".")
        
        def should_ignore_path(path: Path) -> bool:
            """Check if path should be ignored"""
            return any(ignore_dir in path.parts for ignore_dir in ignore_dirs)
        
        def matches_extension(file_path: Path) -> bool:
            """Check if file matches allowed extensions"""
            if not allowed_extensions:
                return True
            return file_path.suffix.lower().lstrip('.') in allowed_extensions
        
        # Search through files
        for root, dirs, files in os.walk(base_path):
            root_path = Path(root)
            
            # Skip ignored directories
            if should_ignore_path(root_path):
                continue
            
            # Remove ignored directories from dirs to prevent walking into them
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                file_path = root_path / file
                
                # Skip if doesn't match extension filter
                if not matches_extension(file_path):
                    continue
                
                # Skip large files (> 1MB) for content search
                try:
                    if file_path.stat().st_size > 1024 * 1024:
                        continue
                except:
                    continue
                
                relative_path = str(file_path.relative_to(base_path))
                
                # Filename search
                if search_type in ["filename", "both"]:
                    if query.lower() in file.lower():
                        results.append({
                            "type": "filename",
                            "file": relative_path,
                            "match": file,
                            "line": None,
                            "content": None
                        })
                
                # Content search
                if search_type in ["content", "both"] and len(results) < max_results:
                    try:
                        # Try to read as text file
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            for line_num, line in enumerate(f, 1):
                                if query.lower() in line.lower():
                                    results.append({
                                        "type": "content",
                                        "file": relative_path,
                                        "match": query,
                                        "line": line_num,
                                        "content": line.strip()[:200]  # Limit content preview
                                    })
                                    
                                    # Stop if we have enough results
                                    if len(results) >= max_results:
                                        break
                    except:
                        # Skip files that can't be read as text
                        continue
                
                # Stop if we have enough results
                if len(results) >= max_results:
                    break
            
            # Stop if we have enough results
            if len(results) >= max_results:
                break
        
        return {
            "ok": True,
            "query": query,
            "search_type": search_type,
            "total_results": len(results),
            "max_results": max_results,
            "results": results[:max_results]
        }
        
    except Exception as e:
        return {"ok": False, "error": str(e)}

# Start monitoring on app startup to mimic previous run() side-effects
@app.on_event("startup")
def on_startup():
    # Skip heavy monitoring at startup to prevent shutdowns in constrained environments
    print("[OMNI] Startup: skipping heavy monitoring init (enable later via API if needed)")

def initialize_google_cloud_integration(api_key: str = None) -> bool:
    """Initialize Google Cloud integration for OMNI Singularity"""
    global google_cloud_manager

    try:
        # Configure API key
        api_key = api_key or "AIzaSyAyKCIUE1b8SQF9g-Ok2WDB_zvtkCkYC8M"

        if google_cloud_manager.configure_api_key(api_key):
            if google_cloud_manager.initialize_google_cloud_services():
                print("Google Cloud integration ready for OMNI Singularity!")
                return True
            else:
                print("Google Cloud integration partially available")
                return False
        else:
            print("Failed to configure Google Cloud API key")
            return False

    except Exception as e:
        print(f"Google Cloud integration failed: {e}")
        return False

def upload_omni_data_to_cloud(data: Any, filename: str) -> bool:
    """Upload OMNI Singularity data to Google Cloud"""
    return google_cloud_manager.integrator.upload_quantum_data(data, filename)

def query_google_gemini(prompt: str) -> str:
    """Query Google Gemini AI"""
    return google_cloud_manager.integrator.query_gemini_ai(prompt)

def get_google_cloud_status() -> Dict[str, Any]:
    """Get Google Cloud integration status"""
    return google_cloud_manager.get_google_cloud_status()

# Main execution
if __name__ == "__main__":
    # Read host/port from environment for platform compatibility (Railway, Cloud Run)
    host = os.getenv("HOST", "0.0.0.0")
    try:
        port = int(os.getenv("PORT", "8080"))
    except (TypeError, ValueError):
        port = 8080

    dashboard = OmniProfessionalDashboard()

    # Health and readiness endpoints for direct-run server
    @dashboard.app.get("/healthz")
    async def healthz_main():
        try:
            uptime = time.time() - getattr(dashboard, "start_time", time.time())
        except Exception:
            uptime = 0
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": uptime,
            "system": {
                "cpu_percent": psutil.cpu_percent(interval=None),
                "memory_percent": psutil.virtual_memory().percent,
                "threads": threading.active_count(),
                "platform": platform.system()
            }
        }

    @dashboard.app.get("/readyz")
    async def readyz_main():
        ready_checks = {
            "app_initialized": dashboard.app is not None,
            "dashboard_initialized": dashboard is not None,
            "cloud_configured": bool(os.getenv("GCS_BUCKET")),
        }
        overall_ready = all(ready_checks.values()) if ready_checks else True
        return {
            "ready": overall_ready,
            "checks": ready_checks,
            "timestamp": datetime.now().isoformat()
        }

    @dashboard.app.get("/health")
    async def health_main():
        return await healthz_main()

    @dashboard.app.get("/api/health")
    async def api_health_main():
        try:
            uptime = time.time() - getattr(dashboard, "start_time", time.time())
        except Exception:
            uptime = 0
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": uptime,
            "system": {
                "cpu_percent": psutil.cpu_percent(interval=None),
                "memory_percent": psutil.virtual_memory().percent,
                "threads": threading.active_count()
            }
        }

    # Optionally set up GCP credentials from base64 JSON in env (Railway-friendly)
    import base64, tempfile
    b64_key = os.getenv("GCP_SERVICE_ACCOUNT_KEY_B64") or os.getenv("GCP_SERVICE_ACCOUNT_KEY")
    if b64_key:
        try:
            creds_path = os.path.join(tempfile.gettempdir(), "gcp_creds.json")
            with open(creds_path, "wb") as f:
                f.write(base64.b64decode(b64_key))
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
            print(f"[GCS] Credentials written to {creds_path}")
        except Exception as e:
            print(f"[GCS] Failed to write credentials: {e}")

    # Initialize Cloud Storage integration if bucket is provided via env
    cloud_manager = None
    bucket = os.getenv("GCS_BUCKET")
    prefix = os.getenv("GCS_PREFIX", "")
    try:
        from omni_platform.googlecloud.storage_integration import CloudStorageManager
        if bucket:
            cloud_manager = CloudStorageManager(bucket_name=bucket, prefix=prefix, polling_interval=int(os.getenv("GCS_POLL_INTERVAL", "15")))
            if cloud_manager.connect():
                cloud_manager.start_indexing()
                print(f"[GCS] Connected to bucket '{bucket}' with prefix '{prefix}'")
            else:
                print(f"[GCS] Could not connect to bucket '{bucket}': {cloud_manager.error}")
        else:
            print("[GCS] No bucket configured. Set env GCS_BUCKET to enable cloud indexing.")
    except Exception as e:
        print(f"[GCS] Cloud storage integration not available: {e}")

    # Cloud file APIs: connect, list, upload, preview, process
    from fastapi import Body, Query
    from typing import Dict

    @dashboard.app.post("/api/cloud/connect")
    def api_cloud_connect(payload: Dict[str, str] = Body(...)):
        global cloud_manager  # reuse module-level variable
        bucket_name = payload.get("bucket")
        prefix_local = payload.get("prefix", "")
        if not bucket_name:
            return {"ok": False, "error": "Missing 'bucket' in payload"}
        try:
            cloud_manager = CloudStorageManager(bucket_name=bucket_name, prefix=prefix_local, polling_interval=int(os.getenv("GCS_POLL_INTERVAL", "15")))
            ok = cloud_manager.connect()
            if ok:
                cloud_manager.start_indexing()
                return {"ok": True, "bucket": bucket_name, "prefix": prefix_local, "count": len(cloud_manager.get_index())}
            return {"ok": False, "error": cloud_manager.error}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @dashboard.app.get("/api/cloud/files")
    def api_cloud_files(limit: int = Query(200, ge=1, le=5000)):
        if not cloud_manager or not cloud_manager.connected:
            return {"ok": False, "error": "Cloud not connected"}
        files = cloud_manager.get_index()
        return {"ok": True, "bucket": cloud_manager.bucket_name, "prefix": cloud_manager.prefix, "count": min(len(files), limit), "files": files[:limit]}

    @dashboard.app.post("/api/cloud/upload")
    def api_cloud_upload(payload: Dict[str, str] = Body(...)):
        if not cloud_manager or not cloud_manager.connected:
            return {"ok": False, "error": "Cloud not connected"}
        name = payload.get("name")
        content = payload.get("content", "")
        content_type = payload.get("content_type", "text/plain")
        if not name:
            return {"ok": False, "error": "Missing 'name'"}
        data = content.encode("utf-8")
        ok = cloud_manager.upload_bytes(name, data, content_type=content_type)
        if ok:
            cloud_manager.index_once()
            return {"ok": True, "name": name}
        return {"ok": False, "error": "Upload failed"}

    @dashboard.app.get("/api/cloud/preview")
    def api_cloud_preview(name: str = Query(...)):
        if not cloud_manager or not cloud_manager.connected:
            return {"ok": False, "error": "Cloud not connected"}
        url = cloud_manager.generate_signed_url(name, expiration_seconds=int(os.getenv("GCS_SIGNED_URL_TTL", "3600")))
        if url:
            return {"ok": True, "name": name, "url": url}
        return {"ok": False, "error": "Signed URL not available; check credentials"}

    @dashboard.app.post("/api/cloud/process")
    def api_cloud_process(payload: Dict[str, str] = Body(...)):
        if not cloud_manager or not cloud_manager.connected:
            return {"ok": False, "error": "Cloud not connected"}
        name = payload.get("name")
        operation = payload.get("operation", "uppercase")
        if not name:
            return {"ok": False, "error": "Missing 'name'"}
        data = cloud_manager.download_bytes(name)
        if data is None:
            return {"ok": False, "error": "File not found or read error"}
        result_bytes = data
        result_ct = "application/octet-stream"
        try:
            if operation == "uppercase":
                result_bytes = data.decode("utf-8", errors="ignore").upper().encode("utf-8")
                result_ct = "text/plain"
            elif operation == "identity":
                pass
            else:
                return {"ok": False, "error": f"Unsupported operation '{operation}'"}
            out_name = f"{name}.processed"
            ok = cloud_manager.upload_bytes(out_name, result_bytes, content_type=result_ct)
            if ok:
                cloud_manager.index_once()
                return {"ok": True, "name": name, "operation": operation, "output": out_name}
            return {"ok": False, "error": "Processing upload failed"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @dashboard.app.post("/api/ai/generate")
    def api_ai_generate_main(payload: Dict[str, Any] = Body(...)):
        model_type = (payload.get("model_type") or payload.get("provider") or "auto").lower()
        prompt = payload.get("prompt") or payload.get("text")
        if not prompt:
            return {"ok": False, "error": "Missing 'prompt'"}

        # Agentic orchestration relies on functions defined later in this module,
        # which are not available when running via the __main__ dashboard runner.
        if model_type == "auto" or payload.get("strategy") or payload.get("session_id") or payload.get("session"):
            return {
                "ok": False,
                "error": "Agentic orchestration not available in __main__ mode. Use direct provider via 'model_type' or run with the global app context.",
            }

        model = payload.get("model")
        system_instruction = payload.get("system_instruction") or payload.get("system")
        gen_cfg = payload.get("config") or payload.get("generation_config") or {}
        if "temperature" in payload and "temperature" not in gen_cfg:
            gen_cfg["temperature"] = payload["temperature"]

        if model_type in ("openai", "oai"):
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return {"ok": False, "error": "Missing OPENAI_API_KEY"}
            mname = model or os.getenv("OPENAI_MODEL") or os.getenv("OPENAI_DEFAULT_MODEL") or "gpt-4o-mini"
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})
            body = {"model": mname, "messages": messages}
            if "temperature" in gen_cfg:
                body["temperature"] = gen_cfg["temperature"]
            try:
                resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=60)
                if resp.status_code >= 400:
                    return {"ok": False, "error": f"OpenAI HTTP {resp.status_code}", "details": resp.text}
                data = resp.json()
                text = data.get("choices", [{}])[0].get("message", {}).get("content") or ""
                return {"ok": True, "reply": text, "model": mname, "provider": "openai"}
            except Exception as e:
                return {"ok": False, "error": str(e)}
        elif model_type in ("vertex", "gemini", "gcp"):
            return {"ok": False, "error": "Vertex direct call not available in __main__ mode. Use /api/vertex/generate or run with the global app context."}
        else:
            return {"ok": False, "error": f"Unknown model_type '{model_type}'"}

    dashboard.run(host=host, port=port)

from typing import Optional

_vertex_init_done = False

def ensure_vertex_initialized():
    """Lenobna inicializacija Vertex AI (pokliče vertexai.init enkrat)."""
    global _vertex_init_done
    try:
        from vertexai import init as vertex_init
    except Exception as e:
        raise RuntimeError(f"Vertex AI SDK ni na voljo: {e}")
    if not _vertex_init_done:
        project = (
            os.getenv("VERTEX_PROJECT_ID")
            or os.getenv("GOOGLE_CLOUD_PROJECT")
            or os.getenv("GCP_PROJECT")
            or os.getenv("PROJECT_ID")
        )
        location = (
            os.getenv("VERTEX_LOCATION")
            or os.getenv("GOOGLE_CLOUD_REGION")
            or os.getenv("GCP_REGION")
            or "us-central1"
        )
        vertex_init(project=project, location=location)
        _vertex_init_done = True


def vertex_generate_text(
    prompt: str,
    model_name: Optional[str] = None,
    system_instruction: Optional[str] = None,
    generation_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Pokliče Vertex AI (Gemini) in vrne besedilo."""
    ensure_vertex_initialized()
    try:
        try:
            from vertexai.generative_models import GenerativeModel, GenerationConfig
        except Exception:
            from vertexai.preview.generative_models import GenerativeModel, GenerationConfig
        mname = model_name or os.getenv("VERTEX_MODEL") or os.getenv("GEMINI_MODEL") or "gemini-1.5-flash"
        gen_model = GenerativeModel(mname)
        inputs = [prompt] if not system_instruction else [system_instruction, prompt]
        allowed = {"temperature", "max_output_tokens", "top_p", "top_k", "candidate_count"}
        cfg_kwargs = {k: v for k, v in (generation_config or {}).items() if k in allowed}
        cfg = GenerationConfig(**cfg_kwargs) if cfg_kwargs else None
        resp = gen_model.generate_content(inputs, generation_config=cfg)
        text = getattr(resp, "text", None)
        return {"ok": True, "text": text, "model": mname}
    except Exception as e:
        return {"ok": False, "error": f"Vertex generate error: {e}"}

@app.get("/api/vertex/config")
def vertex_config():
    present_env = {
        "VERTEX_PROJECT_ID": bool(os.getenv("VERTEX_PROJECT_ID")),
        "VERTEX_LOCATION": bool(os.getenv("VERTEX_LOCATION")),
        "VERTEX_MODEL": bool(os.getenv("VERTEX_MODEL")),
        "GEMINI_MODEL": bool(os.getenv("GEMINI_MODEL")),
        "GOOGLE_APPLICATION_CREDENTIALS": bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")),
    }
    return {
        "ok": True,
        "project_id": (
            os.getenv("VERTEX_PROJECT_ID")
            or os.getenv("GOOGLE_CLOUD_PROJECT")
            or os.getenv("GCP_PROJECT")
            or os.getenv("PROJECT_ID")
        ),
        "location": (
            os.getenv("VERTEX_LOCATION")
            or os.getenv("GOOGLE_CLOUD_REGION")
            or os.getenv("GCP_REGION")
            or "us-central1"
        ),
        "default_model": os.getenv("VERTEX_MODEL") or os.getenv("GEMINI_MODEL") or "gemini-1.5-flash",
        "present_env": present_env,
    }

@app.post("/api/vertex/generate")
def api_vertex_generate(payload: Dict[str, Any] = Body(...)):
    prompt = payload.get("prompt") or payload.get("text")
    if not prompt:
        return {"ok": False, "error": "Missing 'prompt'"}
    model = payload.get("model")
    system_instruction = payload.get("system_instruction") or payload.get("system")
    gen_cfg = payload.get("config") or payload.get("generation_config") or {}
    return vertex_generate_text(prompt, model, system_instruction, gen_cfg)

@app.post("/api/gemini/generate")
def api_gemini_generate(payload: Dict[str, Any] = Body(...)):
    prompt = payload.get("prompt") or payload.get("text")
    model = payload.get("model")
    if not prompt:
        return {"ok": False, "error": "Missing 'prompt'"}
    try:
        result = vertex_generate_text(prompt, model)
        if result.get("ok"):
            return {"ok": True, "reply": result.get("text"), "model": result.get("model")}
        return result
    except Exception as e:
        return {"ok": False, "error": f"Gemini generate error: {e}"}

# Structured JSON output endpoint
@app.post("/api/gemini/structured")
def api_gemini_structured(payload: Dict[str, Any] = Body(...)):
    instructions = payload.get("instructions") or payload.get("prompt")
    schema = payload.get("schema") or {}
    model_name = payload.get("model") or os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    if not instructions:
        return {"ok": False, "error": "Missing 'instructions'"}
    try:
        ensure_vertex_initialized()
        try:
            from vertexai.generative_models import GenerativeModel, GenerationConfig
        except Exception:
            from vertexai.preview.generative_models import GenerativeModel, GenerationConfig
        gen_model = GenerativeModel(model_name)
        gen_config = GenerationConfig(response_mime_type="application/json")
        sys_prompt = (
            "Return a JSON object that matches this schema and fills in fields based on the instructions.\n"
            + "Schema:\n" + json.dumps(schema)
        )
        resp = gen_model.generate_content([sys_prompt, instructions], generation_config=gen_config)
        text = getattr(resp, "text", None)
        parsed = None
        if text:
            try:
                parsed = json.loads(text)
            except Exception:
                parsed = None
        return {"ok": True, "model": model_name, "text": text, "json": parsed}
    except Exception as e:
        return {"ok": False, "error": f"Gemini structured error: {e}"}

# Lightweight cron endpoint for Cloud Scheduler
@app.post("/api/gemini/cron")
def api_gemini_cron(payload: Dict[str, Any] = Body(None)):
    prompt = (payload or {}).get("prompt") or "Heartbeat: summarize system status briefly."
    try:
        result = vertex_generate_text(prompt)
        if result.get("ok"):
            return {"ok": True, "result": result.get("text")}
        return result
    except Exception as e:
        return {"ok": False, "error": f"Gemini cron error: {e}"}

@app.post("/api/gcp/gemini")
def api_gcp_gemini(payload: Dict[str, Any] = Body(...)):
    try:
        prompt = payload.get("prompt") if isinstance(payload, dict) else None
        model = payload.get("model") if isinstance(payload, dict) else None
        if not prompt:
            return {"ok": False, "error": "Missing 'prompt'"}
        result = vertex_generate_text(prompt, model)
        if result.get("ok"):
            return {"ok": True, "reply": result.get("text"), "model": result.get("model")}
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/gemini/query")
def api_gemini_query(payload: Dict[str, Any] = Body(...)):
    """Alias endpoint to mirror /api/gemini/generate for compatibility with clients expecting /api/gemini/query."""
    prompt = payload.get("prompt") or payload.get("text")
    model = payload.get("model")
    if not prompt:
        return {"ok": False, "error": "Missing 'prompt'"}
    try:
        result = vertex_generate_text(prompt, model)
        if result.get("ok"):
            return {"ok": True, "reply": result.get("text"), "model": result.get("model")}
        return result
    except Exception as e:
        return {"ok": False, "error": f"Gemini query error: {e}"}

# ---------------------- OpenAI integration (no SDK dependency) ----------------------

def openai_generate_text(
    prompt: str,
    model: Optional[str] = None,
    system_instruction: Optional[str] = None,
    generation_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"ok": False, "error": "Missing OPENAI_API_KEY"}
    mname = model or os.getenv("OPENAI_MODEL") or os.getenv("OPENAI_DEFAULT_MODEL") or "gpt-4o-mini"
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})
    cfg = generation_config or {}
    body = {
        "model": mname,
        "messages": messages,
    }
    for k in ["temperature", "max_tokens", "top_p", "frequency_penalty", "presence_penalty", "stop"]:
        if k in cfg:
            body[k] = cfg[k]
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=60)
        if resp.status_code >= 400:
            try:
                return {"ok": False, "status": resp.status_code, "error": resp.json()}
            except Exception:
                return {"ok": False, "status": resp.status_code, "error": resp.text}
        data = resp.json()
        text = data.get("choices", [{}])[0].get("message", {}).get("content")
        return {"ok": True, "text": text, "model": mname}
    except Exception as e:
        return {"ok": False, "error": f"OpenAI request failed: {e}"}

@app.get("/api/openai/config")
def openai_config():
    return {
        "ok": True,
        "present_env": {
            "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
            "OPENAI_MODEL": bool(os.getenv("OPENAI_MODEL")) or bool(os.getenv("OPENAI_DEFAULT_MODEL")),
        },
        "default_model": os.getenv("OPENAI_MODEL") or os.getenv("OPENAI_DEFAULT_MODEL") or "gpt-4o-mini",
    }

@app.post("/api/openai/generate")
def api_openai_generate(payload: Dict[str, Any] = Body(...)):
    prompt = payload.get("prompt") or payload.get("text")
    if not prompt:
        return {"ok": False, "error": "Missing 'prompt'"}
    model = payload.get("model")
    system_instruction = payload.get("system_instruction") or payload.get("system")
    gen_cfg = payload.get("config") or payload.get("generation_config") or {}
    return openai_generate_text(prompt, model, system_instruction, gen_cfg)

# ---------------------- Unified AI Orchestrator ----------------------
@app.post("/api/ai/generate")
def api_ai_generate(payload: Dict[str, Any] = Body(...)):
    model_type = (payload.get("model_type") or payload.get("provider") or "auto").lower()

    # Orchestrated path: auto selection, memory, chaining/verify, fallback
    if model_type == "auto" or payload.get("strategy") or payload.get("session_id") or payload.get("session"):
        return _orchestrate_generate(payload)

    # Direct pass-through path for explicit providers
    prompt = payload.get("prompt") or payload.get("text")
    if not prompt:
        return {"ok": False, "error": "Missing 'prompt'"}
    model = payload.get("model")
    system_instruction = payload.get("system_instruction") or payload.get("system")
    gen_cfg = payload.get("config") or payload.get("generation_config") or {}
    if "temperature" in payload and "temperature" not in gen_cfg:
        gen_cfg["temperature"] = payload["temperature"]

    if model_type in ("openai", "oai"):
        result = openai_generate_text(prompt, model, system_instruction, gen_cfg)
    elif model_type in ("vertex", "gemini", "gcp"):
        result = vertex_generate_text(prompt, model, system_instruction, gen_cfg)
    else:
        return {"ok": False, "error": f"Unknown model_type '{model_type}'"}

    if result.get("ok"):
        reply = result.get("text") or result.get("reply")
        return {"ok": True, "reply": reply, "model": result.get("model"), "provider": model_type}
    return result

@app.post("/api/openai/query")
def api_openai_query(payload: Dict[str, Any] = Body(...)):
    prompt = payload.get("prompt") or payload.get("text")
    if not prompt:
        return {"ok": False, "error": "Missing 'prompt'"}
    model = payload.get("model")
    system_instruction = payload.get("system_instruction") or payload.get("system")
    gen_cfg = payload.get("config") or payload.get("generation_config") or {}
    return openai_generate_text(prompt, model, system_instruction, gen_cfg)

# ============================================================================
# AI TITAN ENGINE - Advanced Orchestration Strategies
# ============================================================================

# Global thread pool for parallel execution
_titan_executor = ThreadPoolExecutor(max_workers=5)

# SQLite database for self-optimizing loop
def _init_titan_db():
    """Initialize SQLite database for AI TITAN ENGINE performance tracking."""
    db_path = os.getenv("TITAN_DB_PATH") or os.path.join(tempfile.gettempdir(), "ai_titan.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS performance_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy TEXT,
                provider TEXT,
                prompt_hash TEXT,
                confidence REAL,
                response_time REAL,
                success INTEGER,
                timestamp REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prompt_optimizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_prompt TEXT,
                optimized_prompt TEXT,
                improvement_score REAL,
                timestamp REAL
            )
        """)
        conn.commit()
        print("[AI TITAN] Database initialized successfully")
    except Exception as e:
        print(f"[AI TITAN] Database init error: {e}")
    finally:
        conn.close()

# Initialize on module load
_init_titan_db()

def _log_performance(strategy: str, provider: str, prompt: str, confidence: float, response_time: float, success: bool):
    """Log performance metrics for self-optimizing loop."""
    try:
        db_path = os.getenv("TITAN_DB_PATH") or os.path.join(tempfile.gettempdir(), "ai_titan.db")
        conn = sqlite3.connect(db_path)
        prompt_hash = str(hash(prompt))[:16]
        conn.execute(
            "INSERT INTO performance_log (strategy, provider, prompt_hash, confidence, response_time, success, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (strategy, provider, prompt_hash, confidence, response_time, int(success), time.time())
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[AI TITAN] Performance logging error: {e}")

def _hyper_prompt_optimize(prompt: str) -> str:
    """HYPER PROMPT PIPELINE - Optimize prompt using mini-LLM."""
    try:
        optimization_prompt = f"""
Rewrite this prompt to maximize clarity, depth, and reasoning for AI models.
Make it more specific, structured, and effective while preserving the original intent.

Original prompt: {prompt}

Optimized prompt:"""
        
        # Use GPT-4o-mini for prompt optimization
        result = openai_generate_text(
            optimization_prompt,
            model="gpt-4o-mini",
            system_instruction="You are a prompt optimization expert. Rewrite prompts to be maximally effective.",
            generation_config={"max_tokens": 500, "temperature": 0.3}
        )
        
        if result.get("ok") and result.get("reply"):
            optimized = result["reply"].strip()
            # Log optimization
            try:
                db_path = os.getenv("TITAN_DB_PATH") or os.path.join(tempfile.gettempdir(), "ai_titan.db")
                conn = sqlite3.connect(db_path)
                conn.execute(
                    "INSERT INTO prompt_optimizations (original_prompt, optimized_prompt, improvement_score, timestamp) VALUES (?, ?, ?, ?)",
                    (prompt, optimized, 0.8, time.time())  # Default improvement score
                )
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"[AI TITAN] Optimization logging error: {e}")
            
            print(f"[AI TITAN] Prompt optimized: {len(prompt)} -> {len(optimized)} chars")
            return optimized
        else:
            print("[AI TITAN] Prompt optimization failed, using original")
            return prompt
    except Exception as e:
        print(f"[AI TITAN] Prompt optimization error: {e}")
        return prompt

def _ensemble_intellect(prompt: str, system_instruction: Optional[str] = None, gen_cfg: Dict[str, Any] = None) -> Dict[str, Any]:
    """ENSEMBLE INTELLECT - Combine OpenAI, Gemini, and Vertex with mini-LLM refinement."""
    start_time = time.time()
    gen_cfg = gen_cfg or {}
    
    try:
        # Parallel execution of all three models
        futures = []
        
        # OpenAI - Logic and structure
        futures.append(_titan_executor.submit(
            _call_provider, "openai", prompt, None, system_instruction, gen_cfg
        ))
        
        # Gemini - Creativity and vision
        futures.append(_titan_executor.submit(
            _call_provider, "gemini", prompt, None, system_instruction, gen_cfg
        ))
        
        # Vertex - Facts and analysis
        futures.append(_titan_executor.submit(
            _call_provider, "vertex", prompt, None, system_instruction, gen_cfg
        ))
        
        # Collect results
        results = []
        for i, future in enumerate(futures):
            try:
                result = future.result(timeout=30)  # 30 second timeout
                if result.get("ok"):
                    results.append({
                        "provider": ["openai", "gemini", "vertex"][i],
                        "reply": result.get("reply", ""),
                        "confidence": result.get("confidence", 0.5)
                    })
            except Exception as e:
                print(f"[AI TITAN] Provider {['openai', 'gemini', 'vertex'][i]} failed: {e}")
        
        if not results:
            return {"ok": False, "error": "All providers failed in ensemble"}
        
        # Combine results using mini-LLM
        combination_prompt = f"""
Combine and refine these 3 AI responses into one powerful unified response.
Highlight facts from analysis, creativity from vision, and reasoning from logic.

Response 1 (Logic/Structure): {results[0]['reply'] if len(results) > 0 else 'N/A'}

Response 2 (Creativity/Vision): {results[1]['reply'] if len(results) > 1 else 'N/A'}

Response 3 (Facts/Analysis): {results[2]['reply'] if len(results) > 2 else 'N/A'}

Create a unified, comprehensive response that combines the best of all three:"""
        
        final_result = openai_generate_text(
            combination_prompt,
            model="gpt-4o-mini",
            system_instruction="You are an expert at synthesizing multiple AI responses into one superior answer.",
            generation_config={"max_tokens": 1500, "temperature": 0.4}
        )
        
        response_time = time.time() - start_time
        
        if final_result.get("ok"):
            confidence = sum(r["confidence"] for r in results) / len(results) * 1.2  # Ensemble boost
            confidence = min(confidence, 1.0)
            
            _log_performance("ensemble_intellect", "combined", prompt, confidence, response_time, True)
            
            return {
                "ok": True,
                "reply": final_result["reply"],
                "strategy": "ensemble_intellect",
                "confidence": confidence,
                "providers_used": [r["provider"] for r in results],
                "response_time": response_time,
                "trace": f"Ensemble of {len(results)} providers combined via mini-LLM"
            }
        else:
            # Fallback to best individual result
            best_result = max(results, key=lambda x: x["confidence"])
            _log_performance("ensemble_intellect", best_result["provider"], prompt, best_result["confidence"], response_time, False)
            return {
                "ok": True,
                "reply": best_result["reply"],
                "strategy": "ensemble_intellect_fallback",
                "confidence": best_result["confidence"],
                "provider": best_result["provider"],
                "response_time": response_time,
                "trace": "Ensemble failed, using best individual result"
            }
            
    except Exception as e:
        response_time = time.time() - start_time
        _log_performance("ensemble_intellect", "error", prompt, 0.0, response_time, False)
        return {"ok": False, "error": f"Ensemble intellect failed: {e}"}

def _meta_agent_structure(prompt: str, system_instruction: Optional[str] = None, gen_cfg: Dict[str, Any] = None) -> Dict[str, Any]:
    """META-AGENT STRUCTURE - Models converse in chain: Logic -> Verify -> Create."""
    start_time = time.time()
    gen_cfg = gen_cfg or {}
    
    try:
        trace = []
        
        # Step 1: Logic Agent (OpenAI) - Analysis and solution
        logic_prompt = f"[LOGIC AGENT] Analyze this request and propose a structured solution:\n\n{prompt}"
        logic_result = _call_provider("openai", logic_prompt, None, 
                                    "You are 'Logic', the analytical agent. Provide structured, logical solutions.", gen_cfg)
        
        if not logic_result.get("ok"):
            return {"ok": False, "error": "Logic agent failed"}
        
        logic_response = logic_result["reply"]
        trace.append(f"Logic: {logic_response[:100]}...")
        
        # Step 2: Verify Agent (Vertex) - Fact-check and add references
        verify_prompt = f"""[VERIFY AGENT] Review this analysis and add factual verification:

Logic Agent's Analysis: {logic_response}

Original Request: {prompt}

Verify facts, add references, and improve accuracy:"""
        
        verify_result = _call_provider("vertex", verify_prompt, None,
                                     "You are 'Verify', the fact-checking agent. Verify information and add reliable references.", gen_cfg)
        
        if not verify_result.get("ok"):
            verified_response = logic_response  # Fallback
            trace.append("Verify: Failed, using Logic response")
        else:
            verified_response = verify_result["reply"]
            trace.append(f"Verify: {verified_response[:100]}...")
        
        # Step 3: Create Agent (Gemini) - Enhance style, tone, and presentation
        create_prompt = f"""[CREATE AGENT] Enhance this verified analysis with better style and presentation:

Verified Analysis: {verified_response}

Original Request: {prompt}

Improve style, tone, clarity, and visual presentation:"""
        
        create_result = _call_provider("gemini", create_prompt, None,
                                     "You are 'Create', the creative agent. Enhance style, tone, and presentation while preserving accuracy.", gen_cfg)
        
        response_time = time.time() - start_time
        
        if create_result.get("ok"):
            final_response = create_result["reply"]
            trace.append(f"Create: {final_response[:100]}...")
            
            # Calculate combined confidence
            confidences = [r.get("confidence", 0.5) for r in [logic_result, verify_result, create_result] if r.get("ok")]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
            
            _log_performance("meta_agent", "combined", prompt, avg_confidence, response_time, True)
            
            return {
                "ok": True,
                "reply": final_response,
                "strategy": "meta_agent_structure",
                "confidence": avg_confidence,
                "agents_used": ["Logic", "Verify", "Create"],
                "response_time": response_time,
                "trace": " -> ".join(trace)
            }
        else:
            # Fallback to verified response
            _log_performance("meta_agent", "partial", prompt, 0.7, response_time, False)
            return {
                "ok": True,
                "reply": verified_response,
                "strategy": "meta_agent_partial",
                "confidence": 0.7,
                "agents_used": ["Logic", "Verify"],
                "response_time": response_time,
                "trace": " -> ".join(trace) + " (Create failed)"
            }
            
    except Exception as e:
        response_time = time.time() - start_time
        _log_performance("meta_agent", "error", prompt, 0.0, response_time, False)
        return {"ok": False, "error": f"Meta-agent structure failed: {e}"}

def _multimodal_fusion_engine(prompt: str, system_instruction: Optional[str] = None, gen_cfg: Dict[str, Any] = None) -> Dict[str, Any]:
    """MULTIMODAL FUSION ENGINE - Gemini for images, OpenAI for explanation, Vertex for JSON structure."""
    start_time = time.time()
    gen_cfg = gen_cfg or {}
    
    try:
        trace = []
        
        # Step 1: Gemini - Generate visual/creative content
        visual_prompt = f"[VISUAL ENGINE] Create visual description or diagram for:\n\n{prompt}"
        visual_result = _call_provider("gemini", visual_prompt, None,
                                     "You are the visual engine. Create detailed visual descriptions, diagrams, or creative content.", gen_cfg)
        
        if not visual_result.get("ok"):
            return {"ok": False, "error": "Visual engine failed"}
        
        visual_content = visual_result["reply"]
        trace.append(f"Visual: Generated {len(visual_content)} chars")
        
        # Step 2: OpenAI - Explain and elaborate
        explain_prompt = f"""[EXPLANATION ENGINE] Provide detailed explanation for this visual content:

Visual Content: {visual_content}

Original Request: {prompt}

Provide comprehensive explanation and context:"""
        
        explain_result = _call_provider("openai", explain_prompt, None,
                                      "You are the explanation engine. Provide clear, detailed explanations and context.", gen_cfg)
        
        if not explain_result.get("ok"):
            explanation = "Explanation unavailable"
            trace.append("Explain: Failed")
        else:
            explanation = explain_result["reply"]
            trace.append(f"Explain: Generated {len(explanation)} chars")
        
        # Step 3: Vertex - Structure as JSON/API format
        structure_prompt = f"""[STRUCTURE ENGINE] Convert this content into structured JSON format:

Visual Content: {visual_content}

Explanation: {explanation}

Original Request: {prompt}

Create structured JSON with appropriate fields and organization:"""
        
        structure_result = _call_provider("vertex", structure_prompt, None,
                                        "You are the structure engine. Convert content into well-organized JSON or structured formats.", gen_cfg)
        
        response_time = time.time() - start_time
        
        # Combine all results
        combined_result = {
            "visual_content": visual_content,
            "explanation": explanation,
            "structured_data": structure_result.get("reply", "{}") if structure_result.get("ok") else "{}"
        }
        
        # Create final response
        final_response = f"""MULTIMODAL FUSION RESULT:

VISUAL CONTENT:
{visual_content}

EXPLANATION:
{explanation}

STRUCTURED DATA:
{combined_result['structured_data']}"""
        
        # Calculate confidence
        confidences = [r.get("confidence", 0.5) for r in [visual_result, explain_result, structure_result] if r.get("ok")]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        
        _log_performance("multimodal_fusion", "combined", prompt, avg_confidence, response_time, True)
        
        return {
            "ok": True,
            "reply": final_response,
            "strategy": "multimodal_fusion_engine",
            "confidence": avg_confidence,
            "engines_used": ["Visual", "Explanation", "Structure"],
            "response_time": response_time,
            "trace": " -> ".join(trace),
            "multimodal_data": combined_result
        }
        
    except Exception as e:
        response_time = time.time() - start_time
        _log_performance("multimodal_fusion", "error", prompt, 0.0, response_time, False)
        return {"ok": False, "error": f"Multimodal fusion engine failed: {e}"}

def _self_optimizing_loop(prompt: str, strategy: str) -> Tuple[str, str]:
    """SELF-OPTIMIZING LOOP - Learn from past results and adapt."""
    try:
        db_path = os.getenv("TITAN_DB_PATH") or os.path.join(tempfile.gettempdir(), "ai_titan.db")
        conn = sqlite3.connect(db_path)
        
        # Get performance history for similar prompts
        prompt_hash = str(hash(prompt))[:16]
        cursor = conn.execute("""
            SELECT strategy, provider, AVG(confidence), AVG(response_time), COUNT(*) as usage_count
            FROM performance_log 
            WHERE prompt_hash = ? OR strategy = ?
            GROUP BY strategy, provider
            ORDER BY AVG(confidence) DESC, AVG(response_time) ASC
            LIMIT 5
        """, (prompt_hash, strategy))
        
        history = cursor.fetchall()
        conn.close()
        
        if history:
            # Find best performing strategy/provider combination
            best_strategy, best_provider, best_conf, best_time, usage = history[0]
            
            # Adapt based on learning
            if best_conf > 0.8 and usage > 3:
                print(f"[AI TITAN] Self-optimization: Using proven {best_strategy} with {best_provider} (conf: {best_conf:.2f})")
                return best_strategy, best_provider
            elif best_conf < 0.5 and usage > 2:
                # Avoid poor performing combinations
                print(f"[AI TITAN] Self-optimization: Avoiding {best_strategy} with {best_provider} (poor performance)")
                return "ensemble_intellect", "combined"  # Fallback to ensemble
        
        # No sufficient history, use default strategy
        return strategy, "auto"
        
    except Exception as e:
        print(f"[AI TITAN] Self-optimization error: {e}")
        return strategy, "auto"

def _hyper_prompt_pipeline(prompt: str) -> str:
    """HYPER PROMPT PIPELINE - Optimizacija prompta z mini-LLM"""
    try:
        # Use mini-LLM (GPT-4o-mini) to optimize the prompt
        optimization_prompt = f"""Rewrite this prompt to maximize clarity and depth for reasoning models.
Make it more specific, structured, and effective while preserving the original intent.

Original prompt:
{prompt}

Optimized prompt:"""
        
        # Use OpenAI with mini model for optimization
        gen_cfg = {"temperature": 0.3, "max_tokens": 500}
        result = openai_generate_text(optimization_prompt, "gpt-4o-mini", None, gen_cfg)
        
        if result.get("ok") and result.get("text"):
            optimized = result.get("text").strip()
            print(f"[AI TITAN] Hyper Prompt Pipeline: Optimized prompt length {len(prompt)} -> {len(optimized)}")
            return optimized
        else:
            print(f"[AI TITAN] Hyper Prompt Pipeline: Optimization failed, using original")
            return prompt
            
    except Exception as e:
        print(f"[AI TITAN] Hyper Prompt Pipeline error: {e}")
        return prompt

# Simple in-memory conversation memory (per session)
_memory_store: Dict[str, Any] = {}


def _update_memory(session_id: str, role: str, content: str, max_items: int = 20):
    # Optional SQLite persistent store when ORCH_MEMORY_BACKEND=sqlite
    backend = os.getenv("ORCH_MEMORY_BACKEND", "memory").lower()
    ttl = float(os.getenv("MEMORY_TTL_SECONDS", "86400"))  # 1 day default
    if backend == "sqlite" and session_id:
        import sqlite3, tempfile
        db_path = os.getenv("MEMORY_SQLITE_PATH") or os.path.join(tempfile.gettempdir(), "orch_memory.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("CREATE TABLE IF NOT EXISTS memory(session_id TEXT, role TEXT, content TEXT, ts REAL)")
            conn.execute(
                "INSERT INTO memory(session_id, role, content, ts) VALUES (?, ?, ?, ?)",
                (session_id, role, content, time.time()),
            )
            conn.commit()
        finally:
            conn.close()
        return
    # Fallback to in-memory store
    if not session_id:
        return
    session = _memory_store.setdefault(session_id, [])
    session.append({"role": role, "content": content, "ts": time.time()})
    if len(session) > max_items:
        del session[:-max_items]


def _get_memory_context(session_id: str, max_chars: int = 1500) -> str:
    backend = os.getenv("ORCH_MEMORY_BACKEND", "memory").lower()
    ttl = float(os.getenv("MEMORY_TTL_SECONDS", "86400"))  # 1 day default
    if backend == "sqlite" and session_id:
        import sqlite3, tempfile
        db_path = os.getenv("MEMORY_SQLITE_PATH") or os.path.join(tempfile.gettempdir(), "orch_memory.db")
        if not os.path.exists(db_path):
            return ""
        now = time.time()
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("CREATE TABLE IF NOT EXISTS memory(session_id TEXT, role TEXT, content TEXT, ts REAL)")
            # Cleanup expired
            conn.execute("DELETE FROM memory WHERE ts < ?", (now - ttl,))
            conn.commit()
            rows = conn.execute(
                "SELECT role, content FROM memory WHERE session_id=? ORDER BY ts DESC LIMIT 20",
                (session_id,),
            ).fetchall()
        finally:
            conn.close()
        chunks, total = [], 0
        for role, content in reversed(rows):  # oldest to newest
            piece = f"{role}: {content}\n"
            total += len(piece)
            if total > max_chars:
                break
            chunks.append(piece)
        return "".join(chunks)
    # In-memory fallback
    if not session_id or session_id not in _memory_store:
        return ""
    chunks = []
    total = 0
    for m in _memory_store.get(session_id, [])[-10:]:
        piece = f"{m['role']}: {m['content']}\n"
        total += len(piece)
        if total > max_chars:
            break
        chunks.append(piece)
    return "".join(chunks)


def _select_provider(prompt: str, metadata: Dict[str, Any]) -> str:
    p = (prompt or "").lower()
    profile = (metadata.get("profile") or metadata.get("user_profile") or {}).get("preference") if isinstance(metadata.get("profile"), dict) else metadata.get("profile")
    preferred = (metadata.get("preferred_provider") or metadata.get("preferred"))

    # Honor explicit preference first if provided
    if isinstance(preferred, str) and preferred.lower() in ("openai", "oai", "vertex", "gemini"):
        return "openai" if preferred.lower() in ("openai", "oai") else ("gemini" if preferred.lower() == "gemini" else "vertex")

    # Heuristics for modality/length/tech
    if any(k in p for k in ["image:", "<img", "base64", "draw", "picture", "diagram", "graph", "audio", "transcribe", "video", "multimodal"]):
        return "gemini"  # good for multimodal
    if len(p) > 800 or any(k in p for k in ["kubernetes", "terraform", "protobuf", "sql", "optimizer", "stack trace", "exception", "bigquery", "vertex ai"]):
        return "vertex"

    # Profile-based routing hints
    if isinstance(profile, str):
        pl = profile.lower()
        if pl in ("speed", "latency", "fast"):
            return "openai"
        if pl in ("cost", "economy", "cheap"):
            return "openai"
        if pl in ("google", "gcp", "vertex"):
            return "vertex"
        if pl in ("creative", "multimodal", "vision"):
            return "gemini"

    return "openai"


def _score_confidence(text: str) -> float:
    if not text:
        return 0.0
    t = text.lower()
    penalties = 0
    for k in ["i don't know", "not sure", "unknown", "can't", "cannot", "unsure"]:
        if k in t:
            penalties += 1
    length_bonus = min(len(text) / 800.0, 1.0)
    base = 0.5 * length_bonus + 0.5 * (1.0 - min(penalties * 0.2, 0.8))
    return max(0.0, min(1.0, base))


def _grade_answer_self_eval(text: str, prompt: Optional[str] = None, provider_hint: Optional[str] = None) -> float:
    """Ask a model to rate answer quality from 0.0 to 1.0. Fallback to heuristic on parse errors."""
    if not text:
        return 0.0
    si = (
        "You are a strict evaluator. Rate the ANSWER quality for correctness, relevance, and clarity on a 0.0-1.0 scale. "
        "Respond with ONLY a float number, no words."
    )
    eval_prompt = "QUESTION:\n" + (prompt or "(no question provided)") + "\n\nANSWER:\n" + text + "\n\nScore:"
    provider = provider_hint or os.getenv("EVAL_PROVIDER", "openai")
    try:
        res = _call_provider(provider, eval_prompt, None, si, {"temperature": 0.0})
        raw = (res.get("text") or res.get("reply") or "").strip()
        import re
        m = re.search(r"([01]?(?:\.\d+)?|1\.0+)", raw)
        if m:
            val = float(m.group(1))
            return max(0.0, min(1.0, val))
    except Exception:
        pass
    return _score_confidence(text)


def _call_provider(provider: str, prompt: str, model: Optional[str], system_instruction: Optional[str], gen_cfg: Dict[str, Any]) -> Dict[str, Any]:
    if provider in ("openai", "oai"):
        return openai_generate_text(prompt, model, system_instruction, gen_cfg)
    # Treat gemini as vertex provider under the hood
    return vertex_generate_text(prompt, model, system_instruction, gen_cfg)


def _orchestrate_generate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """AI TITAN ENGINE - Orchestrator z vsemi naprednimi strategijami"""
    prompt = payload.get("prompt") or payload.get("text")
    system_instruction = payload.get("system_instruction") or payload.get("system")
    gen_cfg = payload.get("config") or payload.get("generation_config") or {}
    model = payload.get("model")
    session_id = payload.get("session_id") or payload.get("session")
    strategy = (payload.get("strategy") or "direct").lower()  # direct | verify | hybrid | ensemble | meta_agent | multimodal | self_optimizing

    if not prompt:
        return {"ok": False, "error": "Missing 'prompt'"}

    # Build context from memory if present
    memory_context = _get_memory_context(session_id)
    full_prompt = prompt if not memory_context else f"Context:\n{memory_context}\n\nUser:\n{prompt}"

    # AI TITAN ENGINE - Strategije
    trace = []
    
    try:
        if strategy == "ensemble":
            # ENSEMBLE INTELLECT - Trije modeli hkrati z mini-LLM združevanjem
            result = _ensemble_intellect(full_prompt, system_instruction, gen_cfg)
            trace.append({"step": "ensemble_intellect", "providers": ["openai", "gemini", "vertex"], "ok": result.get("ok")})
            
        elif strategy == "meta_agent":
            # META-AGENT STRUKTURA - Logic/Verify/Create agenti
            result = _meta_agent_structure(full_prompt, system_instruction, gen_cfg)
            trace.append({"step": "meta_agent_structure", "agents": ["Logic", "Verify", "Create"], "ok": result.get("ok")})
            
        elif strategy == "multimodal":
            # MULTIMODAL FUSION ENGINE - Slike/diagrame/JSON
            result = _multimodal_fusion_engine(full_prompt, system_instruction, gen_cfg)
            trace.append({"step": "multimodal_fusion", "modes": ["visual", "text", "structured"], "ok": result.get("ok")})
            
        elif strategy == "self_optimizing":
            # SELF-OPTIMIZING LOOP - Učenje iz zgodovine
            optimized_prompt, best_provider = _self_optimizing_loop(full_prompt, "direct")
            result = _call_provider(best_provider, optimized_prompt, model, system_instruction, gen_cfg)
            trace.append({"step": "self_optimizing", "provider": best_provider, "optimized": True, "ok": result.get("ok")})
            
        else:
            # Standardne strategije (direct, verify, hybrid)
            model_type = (payload.get("model_type") or payload.get("provider") or "auto").lower()
            if model_type == "auto":
                provider = _select_provider(full_prompt, payload)
            else:
                provider = model_type

            # HYPER PROMPT PIPELINE - Optimizacija prompta
            if payload.get("hyper_prompt", False):
                optimized_prompt = _hyper_prompt_pipeline(full_prompt)
                full_prompt = optimized_prompt
                trace.append({"step": "hyper_prompt_optimization", "optimized": True})

            # Primary generation
            primary = _call_provider(provider, full_prompt, model, system_instruction, gen_cfg)
            trace.append({"step": "primary", "provider": provider, "ok": primary.get("ok"), "model": primary.get("model")})

            result_text = primary.get("text") or primary.get("reply") or ""

            # Optional verification/improvement
            if strategy in ("verify", "hybrid") and primary.get("ok"):
                verify_si = "You are a verifier. Improve factual correctness, fix errors, and preserve meaning. Return the refined answer only."
                verify_prompt = f"Review and refine the following answer for correctness.\n\nAnswer:\n{result_text}"
                verifier = _call_provider("vertex", verify_prompt, None, verify_si, {"temperature": 0.2})
                trace.append({"step": "verify", "provider": "vertex", "ok": verifier.get("ok"), "model": verifier.get("model")})
                if verifier.get("ok") and (verifier.get("text") or verifier.get("reply")):
                    result_text = verifier.get("text") or verifier.get("reply")

            # Confidence and fallback
            conf = _score_confidence(result_text)
            fallback_threshold = float(os.getenv("ORCH_FALLBACK_THRESHOLD", "0.4"))
            if conf < fallback_threshold:
                fallback_provider = "vertex" if provider in ("openai", "oai") else "openai"
                fallback = _call_provider(fallback_provider, full_prompt, None, system_instruction, gen_cfg)
                trace.append({"step": "fallback", "provider": fallback_provider, "ok": fallback.get("ok"), "model": fallback.get("model")})
                if fallback.get("ok") and (fallback.get("text") or fallback.get("reply")):
                    result_text = fallback.get("text") or fallback.get("reply")
                    provider = fallback_provider

            result = {"ok": True, "reply": result_text, "text": result_text, "model": model or primary.get("model"), "provider": provider, "confidence": conf}

        # Update memory
        _update_memory(session_id, "user", prompt)
        _update_memory(session_id, "assistant", result.get("reply") or result.get("text", ""))

        # Add trace to result
        result["trace"] = trace
        result["strategy"] = strategy
        
        return result
        
    except Exception as e:
        return {"ok": False, "error": f"AI TITAN ENGINE error: {str(e)}", "trace": trace}

    result_text = primary.get("text") or primary.get("reply") or ""

    # Optional verification/improvement
    if strategy in ("verify", "hybrid") and primary.get("ok"):
        verify_si = "You are a verifier. Improve factual correctness, fix errors, and preserve meaning. Return the refined answer only."
        verify_prompt = f"Review and refine the following answer for correctness.\n\nAnswer:\n{result_text}"
        verifier = _call_provider("vertex", verify_prompt, None, verify_si, {"temperature": 0.2})
        trace.append({"step": "verify", "provider": "vertex", "ok": verifier.get("ok"), "model": verifier.get("model")})
        if verifier.get("ok") and (verifier.get("text") or verifier.get("reply")):
            result_text = verifier.get("text") or verifier.get("reply")

    # Confidence and fallback
    conf = _score_confidence(result_text)
    if conf < 0.4:
        fallback_provider = "vertex" if provider in ("openai", "oai") else "openai"
        fallback = _call_provider(fallback_provider, full_prompt, None, system_instruction, gen_cfg)
        trace.append({"step": "fallback", "provider": fallback_provider, "ok": fallback.get("ok"), "model": fallback.get("model")})
        if fallback.get("ok") and (fallback.get("text") or fallback.get("reply")):
            result_text = fallback.get("text") or fallback.get("reply")
            provider = fallback_provider

    # Update memory
    _update_memory(session_id, "user", prompt)
    _update_memory(session_id, "assistant", result_text)

    return {"ok": True, "reply": result_text, "model": model or primary.get("model"), "provider": provider, "confidence": conf, "trace": trace}

    result_text = primary.get("text") or primary.get("reply") or ""

    # Optional verification/improvement
    if strategy in ("verify", "hybrid") and primary.get("ok"):
        verify_si = "You are a verifier. Improve factual correctness, fix errors, and preserve meaning. Return the refined answer only."
        verify_prompt = f"Review and refine the following answer for correctness.\n\nAnswer:\n{result_text}"
        verifier = _call_provider("vertex", verify_prompt, None, verify_si, {"temperature": 0.2})
        trace.append({"step": "verify", "provider": "vertex", "ok": verifier.get("ok"), "model": verifier.get("model")})
        if verifier.get("ok") and (verifier.get("text") or verifier.get("reply")):
            result_text = verifier.get("text") or verifier.get("reply")

    # Confidence and fallback
    conf = _score_confidence(result_text)
    if conf < 0.4:
        fallback_provider = "vertex" if provider in ("openai", "oai") else "openai"
        fallback = _call_provider(fallback_provider, full_prompt, None, system_instruction, gen_cfg)
        trace.append({"step": "fallback", "provider": fallback_provider, "ok": fallback.get("ok"), "model": fallback.get("model")})
        if fallback.get("ok") and (fallback.get("text") or fallback.get("reply")):
            result_text = fallback.get("text") or fallback.get("reply")
            provider = fallback_provider

    # Update memory
    _update_memory(session_id, "user", prompt)
    _update_memory(session_id, "assistant", result_text)

    return {"ok": True, "reply": result_text, "model": model or primary.get("model"), "provider": provider, "confidence": conf, "trace": trace}

    result_text = primary.get("text") or primary.get("reply") or ""

    # Optional verification/improvement
    if strategy in ("verify", "hybrid") and primary.get("ok"):
        verify_si = "You are a verifier. Improve factual correctness, fix errors, and preserve meaning. Return the refined answer only."
        verify_prompt = f"Review and refine the following answer for correctness.\n\nAnswer:\n{result_text}"
        verifier = _call_provider("vertex", verify_prompt, None, verify_si, {"temperature": 0.2})
        trace.append({"step": "verify", "provider": "vertex", "ok": verifier.get("ok"), "model": verifier.get("model")})
        if verifier.get("ok") and (verifier.get("text") or verifier.get("reply")):
            result_text = verifier.get("text") or verifier.get("reply")

    # Confidence and fallback
    conf = _score_confidence(result_text)
    if conf < 0.4:
        fallback_provider = "vertex" if provider in ("openai", "oai") else "openai"
        fallback = _call_provider(fallback_provider, full_prompt, None, system_instruction, gen_cfg)
        trace.append({"step": "fallback", "provider": fallback_provider, "ok": fallback.get("ok"), "model": fallback.get("model")})
        if fallback.get("ok") and (fallback.get("text") or fallback.get("reply")):
            result_text = fallback.get("text") or fallback.get("reply")
            provider = fallback_provider

    # Update memory
    _update_memory(session_id, "user", prompt)
    _update_memory(session_id, "assistant", result_text)

    return {"ok": True, "reply": result_text, "model": model or primary.get("model"), "provider": provider, "confidence": conf, "trace": trace}

    result_text = primary.get("text") or primary.get("reply") or ""

    # Optional verification/improvement
    if strategy in ("verify", "hybrid") and primary.get("ok"):
        verify_si = "You are a verifier. Improve factual correctness, fix errors, and preserve meaning. Return the refined answer only."
        verify_prompt = f"Review and refine the following answer for correctness.\n\nAnswer:\n{result_text}"
        verifier = _call_provider("vertex", verify_prompt, None, verify_si, {"temperature": 0.2})
        trace.append({"step": "verify", "provider": "vertex", "ok": verifier.get("ok"), "model": verifier.get("model")})
        if verifier.get("ok") and (verifier.get("text") or verifier.get("reply")):
            result_text = verifier.get("text") or verifier.get("reply")

    # Confidence and fallback
    conf = _score_confidence(result_text)
    if conf < 0.4:
        fallback_provider = "vertex" if provider in ("openai", "oai") else "openai"
        fallback = _call_provider(fallback_provider, full_prompt, None, system_instruction, gen_cfg)
        trace.append({"step": "fallback", "provider": fallback_provider, "ok": fallback.get("ok"), "model": fallback.get("model")})
        if fallback.get("ok") and (fallback.get("text") or fallback.get("reply")):
            result_text = fallback.get("text") or fallback.get("reply")
            provider = fallback_provider

    # Update memory
    _update_memory(session_id, "user", prompt)
    _update_memory(session_id, "assistant", result_text)

    return {"ok": True, "reply": result_text, "model": model or primary.get("model"), "provider": provider, "confidence": conf, "trace": trace}

    result_text = primary.get("text") or primary.get("reply") or ""

    # Optional verification/improvement
    if strategy in ("verify", "hybrid") and primary.get("ok"):
        verify_si = "You are a verifier. Improve factual correctness, fix errors, and preserve meaning. Return the refined answer only."
        verify_prompt = f"Review and refine the following answer for correctness.\n\nAnswer:\n{result_text}"
        verifier = _call_provider("vertex", verify_prompt, None, verify_si, {"temperature": 0.2})
        trace.append({"step": "verify", "provider": "vertex", "ok": verifier.get("ok"), "model": verifier.get("model")})
        if verifier.get("ok") and (verifier.get("text") or verifier.get("reply")):
            result_text = verifier.get("text") or verifier.get("reply")

    # Confidence and fallback
    conf = _score_confidence(result_text)
    if conf < 0.4:
        fallback_provider = "vertex" if provider in ("openai", "oai") else "openai"
        fallback = _call_provider(fallback_provider, full_prompt, None, system_instruction, gen_cfg)
        trace.append({"step": "fallback", "provider": fallback_provider, "ok": fallback.get("ok"), "model": fallback.get("model")})
        if fallback.get("ok") and (fallback.get("text") or fallback.get("reply")):
            result_text = fallback.get("text") or fallback.get("reply")
            provider = fallback_provider

    # Update memory
    _update_memory(session_id, "user", prompt)
    _update_memory(session_id, "assistant", result_text)

    return {"ok": True, "reply": result_text, "model": model or primary.get("model"), "provider": provider, "confidence": conf, "trace": trace}

    result_text = primary.get("text") or primary.get("reply") or ""

    # Optional verification/improvement
    if strategy in ("verify", "hybrid") and primary.get("ok"):
        verify_si = "You are a verifier. Improve factual correctness, fix errors, and preserve meaning. Return the refined answer only."
        verify_prompt = f"Review and refine the following answer for correctness.\n\nAnswer:\n{result_text}"
        verifier = _call_provider("vertex", verify_prompt, None, verify_si, {"temperature": 0.2})
        trace.append({"step": "verify", "provider": "vertex", "ok": verifier.get("ok"), "model": verifier.get("model")})
        if verifier.get("ok") and (verifier.get("text") or verifier.get("reply")):
            result_text = verifier.get("text") or verifier.get("reply")

    # Confidence and fallback
    conf = _score_confidence(result_text)
    if conf < 0.4:
        fallback_provider = "vertex" if provider in ("openai", "oai") else "openai"
        fallback = _call_provider(fallback_provider, full_prompt, None, system_instruction, gen_cfg)
        trace.append({"step": "fallback", "provider": fallback_provider, "ok": fallback.get("ok"), "model": fallback.get("model")})
        if fallback.get("ok") and (fallback.get("text") or fallback.get("reply")):
            result_text = fallback.get("text") or fallback.get("reply")
            provider = fallback_provider

    # Update memory
    _update_memory(session_id, "user", prompt)
    _update_memory(session_id, "assistant", result_text)

    return {"ok": True, "reply": result_text, "model": model or primary.get("model"), "provider": provider, "confidence": conf, "trace": trace}

    result_text = primary.get("text") or primary.get("reply") or ""

    # Optional verification/improvement
    if strategy in ("verify", "hybrid") and primary.get("ok"):
        verify_si = "You are a verifier. Improve factual correctness, fix errors, and preserve meaning. Return the refined answer only."
        verify_prompt = f"Review and refine the following answer for correctness.\n\nAnswer:\n{result_text}"
        verifier = _call_provider("vertex", verify_prompt, None, verify_si, {"temperature": 0.2})
        trace.append({"step": "verify", "provider": "vertex", "ok": verifier.get("ok"), "model": verifier.get("model")})
        if verifier.get("ok") and (verifier.get("text") or verifier.get("reply")):
            result_text = verifier.get("text") or verifier.get("reply")

    # Confidence and fallback
    conf = _score_confidence(result_text)
    if conf < 0.4:
        fallback_provider = "vertex" if provider in ("openai", "oai") else "openai"
        fallback = _call_provider(fallback_provider, full_prompt, None, system_instruction, gen_cfg)
        trace.append({"step": "fallback", "provider": fallback_provider, "ok": fallback.get("ok"), "model": fallback.get("model")})
        if fallback.get("ok") and (fallback.get("text") or fallback.get("reply")):
            result_text = fallback.get("text") or fallback.get("reply")
            provider = fallback_provider

    # Update memory
    _update_memory(session_id, "user", prompt)
    _update_memory(session_id, "assistant", result_text)

    return {"ok": True, "reply": result_text, "model": model or primary.get("model"), "provider": provider, "confidence": conf, "trace": trace}

    result_text = primary.get("text") or primary.get("reply") or ""

    # Optional verification/improvement
    if strategy in ("verify", "hybrid") and primary.get("ok"):
        verify_si = "You are a verifier. Improve factual correctness, fix errors, and preserve meaning. Return the refined answer only."
        verify_prompt = f"Review and refine the following answer for correctness.\n\nAnswer:\n{result_text}"
        verifier = _call_provider("vertex", verify_prompt, None, verify_si, {"temperature": 0.2})
        trace.append({"step": "verify", "provider": "vertex", "ok": verifier.get("ok"), "model": verifier.get("model")})
        if verifier.get("ok") and (verifier.get("text") or verifier.get("reply")):
            result_text = verifier.get("text") or verifier.get("reply")

    # Confidence and fallback
    conf = _score_confidence(result_text)
    if conf < 0.4:
        fallback_provider = "vertex" if provider in ("openai", "oai") else "openai"
        fallback = _call_provider(fallback_provider, full_prompt, None, system_instruction, gen_cfg)
        trace.append({"step": "fallback", "provider": fallback_provider, "ok": fallback.get("ok"), "model": fallback.get("model")})
        if fallback.get("ok") and (fallback.get("text") or fallback.get("reply")):
            result_text = fallback.get("text") or fallback.get("reply")
            provider = fallback_provider

    # Update memory
    _update_memory(session_id, "user", prompt)
    _update_memory(session_id, "assistant", result_text)

    return {"ok": True, "reply": result_text, "model": model or primary.get("model"), "provider": provider, "confidence": conf, "trace": trace}

    result_text = primary.get("text") or primary.get("reply") or ""

    # Optional verification/improvement
    if strategy in ("verify", "hybrid") and primary.get("ok"):
        verify_si = "You are a verifier. Improve factual correctness, fix errors, and preserve meaning. Return the refined answer only."
        verify_prompt = f"Review and refine the following answer for correctness.\n\nAnswer:\n{result_text}"
        verifier = _call_provider("vertex", verify_prompt, None, verify_si, {"temperature": 0.2})
        trace.append({"step": "verify", "provider": "vertex", "ok": verifier.get("ok"), "model": verifier.get("model")})
        if verifier.get("ok") and (verifier.get("text") or verifier.get("reply")):
            result_text = verifier.get("text") or verifier.get("reply")

    # Confidence and fallback
    conf = _score_confidence(result_text)
    if conf < 0.4:
        fallback_provider = "vertex" if provider in ("openai", "oai") else "openai"
        fallback = _call_provider(fallback_provider, full_prompt, None, system_instruction, gen_cfg)
        trace.append({"step": "fallback", "provider": fallback_provider, "ok": fallback.get("ok"), "model": fallback.get("model")})
        if fallback.get("ok") and (fallback.get("text") or fallback.get("reply")):
            result_text = fallback.get("text") or fallback.get("reply")
            provider = fallback_provider

    # Update memory
    _update_memory(session_id, "user", prompt)
    _update_memory(session_id, "assistant", result_text)

    return {"ok": True, "reply": result_text, "model": model or primary.get("model"), "provider": provider, "confidence": conf, "trace": trace}

    result_text = primary.get("text") or primary.get("reply") or ""

    # Optional verification/improvement
    if strategy in ("verify", "hybrid") and primary.get("ok"):
        verify_si = "You are a verifier. Improve factual correctness, fix errors, and preserve meaning. Return the refined answer only."
        verify_prompt = f"Review and refine the following answer for correctness.\n\nAnswer:\n{result_text}"
        verifier = _call_provider("vertex", verify_prompt, None, verify_si, {"temperature": 0.2})
        trace.append({"step": "verify", "provider": "vertex", "ok": verifier.get("ok"), "model": verifier.get("model")})
        if verifier.get("ok") and (verifier.get("text") or verifier.get("reply")):
            result_text = verifier.get("text") or verifier.get("reply")

    # Confidence and fallback
    conf = _score_confidence(result_text)
    if conf < 0.4:
        fallback_provider = "vertex" if provider in ("openai", "oai") else "openai"
        fallback = _call_provider(fallback_provider, full_prompt, None, system_instruction, gen_cfg)
        trace.append({"step": "fallback", "provider": fallback_provider, "ok": fallback.get("ok"), "model": fallback.get("model")})
        if fallback.get("ok") and (fallback.get("text") or fallback.get("reply")):
            result_text = fallback.get("text") or fallback.get("reply")
            provider = fallback_provider

    # Update memory
    _update_memory(session_id, "user", prompt)
    _update_memory(session_id, "assistant", result_text)

    return {"ok": True, "reply": result_text, "model": model or primary.get("model"), "provider": provider, "confidence": conf, "trace": trace}