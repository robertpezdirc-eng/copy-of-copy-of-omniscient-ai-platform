#!/usr/bin/env python3
"""
OMNI UNIFIED PLATFORM
Združena aplikacija vseh Omni platform komponent z Vertex AI integracijo

Komponente:
- OMNIBOT13 (AI Bot system)
- OmniSingularity (Quantum computing)
- UltimateOmniPackage (Complete toolkit)
- omni-search (Search system)
- Vertex AI integration
- Professional dashboard
- Operational monitoring

Author: OMNI Platform Unified System
Version: 4.0.0
"""

import asyncio
import json
import time
import os
import sys
import logging
import threading
import subprocess
import platform
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

# Web framework
from fastapi import FastAPI, HTTPException, BackgroundTasks, Body, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Monitoring and visualization
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import pandas as pd
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# Configure logging
log_dir = './logs'
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'omni_unified_platform.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class OmniUnifiedPlatform:
    """Unified OMNI Platform with all components integrated"""
    
    def __init__(self):
        self.app = FastAPI(
            title="OMNI Unified Platform",
            description="Complete OMNI AI Platform with Vertex AI integration",
            version="4.0.0"
        )
        
        # Restricted CORS for security (frontend + local dev)
        frontend_origin = os.getenv("OMNI_FRONTEND_ORIGIN", "https://omni-dashboard-guzjyv6gfa-ew.a.run.app")
        allowed_origins = list({
            frontend_origin,
            "https://omni-dashboard-guzjyv6gfa-ew.a.run.app",
            "http://localhost:8080",
            "http://localhost:3000",
            "http://127.0.0.1:8080",
            "http://127.0.0.1:3000",
            "http://localhost:8082",
            "http://127.0.0.1:8082",
            "http://localhost:8083",
            "http://127.0.0.1:8083",
        })
        # Add support for extra comma-separated origins from env
        extra_origins = os.getenv("OMNI_FRONTEND_EXTRA_ORIGINS")
        if extra_origins:
            try:
                allowed_origins = list(set(allowed_origins + [o.strip() for o in extra_origins.split(",") if o.strip()]))
            except Exception:
                pass
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_origin_regex=r"https:\/\/([a-zA-Z0-9-]+\.)?(localtunnel\.me|ngrok(-free)?\.app|ngrok\.io|localhost\.run|trycloudflare\.com|tunnelmole\.com|pagekite\.me|run\.app)$",
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*", "Authorization", "Content-Type", "X-Requested-With"],
            expose_headers=["Content-Length", "X-Request-ID"],
            max_age=600,
        )
        self.components = {}
        self.vertex_ai_config = self._load_vertex_config()
        # Simple in-memory cache (TTL) for demo streaming responses
        self.cache: Dict[str, Dict[str, Any]] = {"gemini": {}}
        # SSE stream metrics counters (health/ready diagnostics)
        self.metrics = {
            "sse_streams_started": 0,
            "sse_streams_done": 0,
            "sse_streams_fallback": 0,
            "sse_streams_errors": 0,
        }
        self.setup_routes()
        self.initialize_components()
        
    def _load_vertex_config(self) -> Dict[str, Any]:
        """Load Vertex AI configuration"""
        try:
            config_path = "vertex_ai_config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load Vertex AI config: {e}")
        
        # Default configuration
        return {
            "vertex_ai": {
                "api_key": os.getenv("VERTEX_AI_API_KEY", "AQ.Ab8RN6LjDXj9_BHBcp-XvbSm0WCE2ftjfwyobHz-Zc3oNMVfhQ"),
                "project_id": os.getenv("GOOGLE_CLOUD_PROJECT", "refined-graph-471712-n9"),
                "region": os.getenv("GOOGLE_CLOUD_REGION", "europe-west1"),
                "model": os.getenv("VERTEX_AI_MODEL", "gemini-2.5-pro"),
                "enabled": True
            }
        }
    
    def initialize_components(self):
        """Initialize all OMNI platform components"""
        logger.info("Initializing OMNI Unified Platform components...")
        
        # Initialize OMNIBOT13
        try:
            self.components['omnibot'] = self._init_omnibot()
            logger.info("✅ OMNIBOT13 initialized")
        except Exception as e:
            logger.warning(f"⚠️ OMNIBOT13 initialization failed: {e}")
        
        # Initialize OmniSingularity
        try:
            self.components['singularity'] = self._init_singularity()
            logger.info("✅ OmniSingularity initialized")
        except Exception as e:
            logger.warning(f"⚠️ OmniSingularity initialization failed: {e}")
        
        # Initialize UltimateOmniPackage
        try:
            self.components['ultimate_package'] = self._init_ultimate_package()
            logger.info("✅ UltimateOmniPackage initialized")
        except Exception as e:
            logger.warning(f"⚠️ UltimateOmniPackage initialization failed: {e}")
        
        # Initialize omni-search
        try:
            self.components['search'] = self._init_search()
            logger.info("✅ omni-search initialized")
        except Exception as e:
            logger.warning(f"⚠️ omni-search initialization failed: {e}")
        
        # Initialize Vertex AI
        try:
            self.components['vertex_ai'] = self._init_vertex_ai()
            logger.info("✅ Vertex AI initialized")
        except Exception as e:
            logger.warning(f"⚠️ Vertex AI initialization failed: {e}")
        
        # Initialize VR
        try:
            self.components['vr'] = self._init_vr()
            logger.info("✅ VR initialized")
        except Exception as e:
            logger.warning(f"⚠️ VR initialization failed: {e}")
        
        # Initialize Tourism
        try:
            self.components['tourism'] = self._init_tourism()
            logger.info("✅ Tourism module initialized")
        except Exception as e:
            logger.warning(f"⚠️ Tourism initialization failed: {e}")
        
        # Initialize Companies/Business
        try:
            self.components['business'] = self._init_business()
            logger.info("✅ Business module initialized")
        except Exception as e:
            logger.warning(f"⚠️ Business initialization failed: {e}")
    
    def _init_omnibot(self) -> Dict[str, Any]:
        """Initialize OMNIBOT13 component"""
        return {
            "status": "active",
            "description": "AI Bot system with advanced capabilities",
            "endpoints": ["/api/omnibot/chat", "/api/omnibot/status"],
            "features": ["Natural language processing", "Task automation", "Learning capabilities"]
        }
    
    def _init_singularity(self) -> Dict[str, Any]:
        """Initialize OmniSingularity component"""
        return {
            "status": "active",
            "description": "Quantum computing and advanced AI processing",
            "endpoints": ["/api/singularity/quantum", "/api/singularity/process"],
            "features": ["Quantum processing", "Advanced algorithms", "Memory management"]
        }
    
    def _init_ultimate_package(self) -> Dict[str, Any]:
        """Initialize UltimateOmniPackage component"""
        return {
            "status": "active",
            "description": "Complete toolkit with all OMNI features",
            "endpoints": ["/api/ultimate/tools", "/api/ultimate/automation"],
            "features": ["Complete toolkit", "Automation", "Integration hub"]
        }
    
    def _init_search(self) -> Dict[str, Any]:
        """Initialize omni-search component"""
        return {
            "status": "active",
            "description": "Advanced search and indexing system",
            "endpoints": ["/api/search/query", "/api/search/index"],
            "features": ["Semantic search", "Real-time indexing", "Multi-modal search"]
        }
    
    def _init_vertex_ai(self) -> Dict[str, Any]:
        """Initialize Vertex AI component"""
        config = self.vertex_ai_config.get("vertex_ai", {})
        return {
            "status": "active" if config.get("enabled", False) else "disabled",
            "description": "Google Cloud Vertex AI integration",
            "endpoints": ["/api/vertex/generate", "/api/vertex/config"],
            "features": ["Text generation", "Code analysis", "Multi-modal AI"],
            "config": {
                "project_id": config.get("project_id"),
                "region": config.get("region"),
                "model": config.get("model")
            }
        }
    
    def _init_vr(self) -> Dict[str, Any]:
        """Initialize VR component"""
        return {
            "status": "active",
            "description": "VR Gateway & Projects",
            "endpoints": [
                "/api/vr/status",
                "/api/vr/assets",
                "/api/vr/templates",
                "/api/vr/projects",
                "/api/vr/gateway",
                "/api/vr/publish"
            ],
            "features": ["WebXR assets", "Templates", "Publishing"]
        }
    
    def _init_tourism(self) -> Dict[str, Any]:
        """Initialize Tourism component"""
        return {
            "status": "active",
            "description": "Tourism info and recommendations",
            "endpoints": ["/api/tourism/places", "/api/tourism/recommend"],
            "features": ["Places catalog", "Itinerary recommendations"]
        }
    
    def _init_business(self) -> Dict[str, Any]:
        """Initialize Companies/Business component"""
        return {
            "status": "active",
            "description": "Companies listing and analysis",
            "endpoints": ["/api/companies/list", "/api/companies/analyze"],
            "features": ["Listing", "Analysis"]
        }
    
    def setup_routes(self):
        """Setup all API routes"""
        
        # Health checks
        @self.app.get("/health")
        @self.app.get("/healthz")
        async def health():
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "platform": "OMNI Unified Platform",
                "version": "4.0.0",
                "components": len(self.components),
                # SSE metrics snapshot
                "sse_metrics": {
                    "started": self.metrics.get("sse_streams_started", 0),
                    "done": self.metrics.get("sse_streams_done", 0),
                    "fallback": self.metrics.get("sse_streams_fallback", 0),
                    "errors": self.metrics.get("sse_streams_errors", 0),
                },
            }
        
        @self.app.get("/readyz")
        async def readiness():
            active_components = sum(1 for comp in self.components.values() 
                                  if comp.get("status") == "active")
            return {
                "status": "ready",
                "active_components": active_components,
                "total_components": len(self.components),
                # SSE metrics snapshot
                "sse_metrics": {
                    "started": self.metrics.get("sse_streams_started", 0),
                    "done": self.metrics.get("sse_streams_done", 0),
                    "fallback": self.metrics.get("sse_streams_fallback", 0),
                    "errors": self.metrics.get("sse_streams_errors", 0),
                },
            }
        
        # Prometheus metrics exposition
        @self.app.get("/metrics")
        async def metrics():
            lines = []
            # HELP/TYPE headers
            lines.append("# HELP omni_sse_streams_started Number of SSE streams started")
            lines.append("# TYPE omni_sse_streams_started counter")
            lines.append(f"omni_sse_streams_started {self.metrics.get('sse_streams_started', 0)}")
            lines.append("# HELP omni_sse_streams_done Number of SSE streams completed")
            lines.append("# TYPE omni_sse_streams_done counter")
            lines.append(f"omni_sse_streams_done {self.metrics.get('sse_streams_done', 0)}")
            lines.append("# HELP omni_sse_streams_fallback Number of SSE streams that fell back to another source")
            lines.append("# TYPE omni_sse_streams_fallback counter")
            lines.append(f"omni_sse_streams_fallback {self.metrics.get('sse_streams_fallback', 0)}")
            lines.append("# HELP omni_sse_streams_errors Number of SSE stream errors")
            lines.append("# TYPE omni_sse_streams_errors counter")
            lines.append(f"omni_sse_streams_errors {self.metrics.get('sse_streams_errors', 0)}")
            body = "\n".join(lines) + "\n"
            return Response(content=body, media_type="text/plain")
        
        # Platform status
        @self.app.get("/api/platform/status")
        def platform_status():
            system_info = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "platform": platform.system(),
                "python_version": sys.version.split()[0]
            }
            
            return {
                "platform": "OMNI Unified Platform",
                "version": "4.0.0",
                "status": "operational",
                "timestamp": datetime.now().isoformat(),
                "components": self.components,
                "system": system_info,
                "vertex_ai": {
                    "enabled": self.vertex_ai_config.get("vertex_ai", {}).get("enabled", False),
                    "project": self.vertex_ai_config.get("vertex_ai", {}).get("project_id"),
                    "region": self.vertex_ai_config.get("vertex_ai", {}).get("region")
                }
            }
        
        # Component endpoints
        @self.app.get("/api/components")
        def list_components():
            return {
                "components": self.components,
                "total": len(self.components),
                "active": sum(1 for comp in self.components.values() 
                            if comp.get("status") == "active")
            }
        
        # OMNIBOT13 endpoints
        @self.app.post("/api/omnibot/chat")
        def omnibot_chat(payload: Dict[str, Any] = Body(...)):
            message = payload.get("message", "")
            return {
                "response": f"OMNIBOT13: Processed message '{message}' with advanced AI capabilities",
                "timestamp": datetime.now().isoformat(),
                "component": "OMNIBOT13"
            }
        
        @self.app.get("/api/omnibot/status")
        def omnibot_status():
            return self.components.get("omnibot", {"status": "not_initialized"})
        
        # OmniSingularity endpoints
        @self.app.post("/api/singularity/quantum")
        def singularity_quantum(payload: Dict[str, Any] = Body(...)):
            task = payload.get("task", "")
            return {
                "result": f"Quantum processing completed for task: {task}",
                "quantum_state": "entangled",
                "processing_time": "0.001ms",
                "component": "OmniSingularity"
            }
        
        @self.app.post("/api/singularity/process")
        def singularity_process(payload: Dict[str, Any] = Body(...)):
            data = payload.get("data", {})
            return {
                "processed_data": data,
                "enhancement": "quantum_optimized",
                "component": "OmniSingularity"
            }
        
        # UltimateOmniPackage endpoints
        @self.app.get("/api/ultimate/tools")
        def ultimate_tools():
            return {
                "available_tools": [
                    "Code analyzer", "Performance optimizer", "Security scanner",
                    "Backup manager", "Documentation generator", "Test runner",
                    "Deployment manager", "Monitoring system"
                ],
                "component": "UltimateOmniPackage"
            }
        
        @self.app.post("/api/ultimate/automation")
        def ultimate_automation(payload: Dict[str, Any] = Body(...)):
            task = payload.get("task", "")
            return {
                "automation_result": f"Automated task '{task}' completed successfully",
                "tools_used": ["AI optimizer", "Smart scheduler", "Auto-deployer"],
                "component": "UltimateOmniPackage"
            }
        
        # omni-search endpoints
        @self.app.post("/api/search/query")
        def search_query(payload: Dict[str, Any] = Body(...)):
            query = payload.get("query", "")
            return {
                "results": [
                    {"title": f"Result for '{query}'", "relevance": 0.95, "source": "omni-search"},
                    {"title": f"Advanced match for '{query}'", "relevance": 0.87, "source": "semantic_index"}
                ],
                "total_results": 2,
                "search_time": "0.05s",
                "component": "omni-search"
            }
        
        @self.app.post("/api/search/index")
        def search_index(payload: Dict[str, Any] = Body(...)):
            content = payload.get("content", "")
            return {
                "indexed": True,
                "content_length": len(content),
                "index_id": f"idx_{int(time.time())}",
                "component": "omni-search"
            }
        
        # Vertex AI endpoints
        @self.app.get("/api/vertex/config")
        def vertex_config():
            config = self.vertex_ai_config.get("vertex_ai", {})
            return {
                "enabled": config.get("enabled", False),
                "project_id": config.get("project_id"),
                "region": config.get("region"),
                "model": config.get("model"),
                "component": "Vertex AI"
            }

        @self.app.post("/api/vertex/generate")
        def vertex_generate(payload: Dict[str, Any] = Body(...)):
            prompt = payload.get("prompt") or payload.get("text")
            if not prompt:
                return {"ok": False, "error": "Missing 'prompt'"}
            model = payload.get("model")
            system_instruction = payload.get("system_instruction") or payload.get("system")
            gen_cfg = payload.get("config") or payload.get("generation_config") or {}
            try:
                cfg = self.vertex_ai_config.get("vertex_ai", {})
                project_id = os.getenv("GOOGLE_CLOUD_PROJECT", cfg.get("project_id"))
                region = os.getenv("GOOGLE_CLOUD_REGION", cfg.get("region") or "europe-west1")
                effective_model = model or os.getenv("VERTEX_AI_MODEL") or cfg.get("model") or "gemini-2.5-pro"

                import vertexai
                from vertexai.generative_models import GenerativeModel, GenerationConfig
                from google.oauth2 import service_account

                sa_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
                if sa_path and os.path.exists(sa_path):
                    try:
                        creds = service_account.Credentials.from_service_account_file(
                            sa_path, scopes=["https://www.googleapis.com/auth/cloud-platform"]
                        )
                        vertexai.init(project=project_id, location=region, credentials=creds)
                    except Exception:
                        vertexai.init(project=project_id, location=region)
                else:
                    vertexai.init(project=project_id, location=region)

                gen_config = GenerationConfig(
                    temperature=gen_cfg.get("temperature", 0.7),
                    top_p=gen_cfg.get("top_p", 0.95),
                    top_k=gen_cfg.get("top_k", 40),
                    max_output_tokens=gen_cfg.get("max_output_tokens", 1024),
                )
                model_inst = GenerativeModel(effective_model, system_instruction=system_instruction)
                resp = model_inst.generate_content(prompt, generation_config=gen_config)
                text = getattr(resp, "text", "") or ""
                if not text:
                    try:
                        candidates = getattr(resp, "candidates", [])
                        text = "".join([getattr(c, "output_text", "") for c in candidates])
                    except Exception:
                        text = text or ""
                if text:
                    return {"ok": True, "text": text, "model": effective_model}
                return {"ok": False, "error": "Empty response", "model": effective_model}
            except Exception as e:
                return {"ok": False, "error": str(e)}
        
        @self.app.get("/api/platform/ping")
        async def platform_ping():
            cfg = self.vertex_ai_config.get("vertex_ai", {})
            effective = os.getenv("VERTEX_AI_MODEL") or cfg.get("model") or "gemini-2.5-pro"
            fallback = os.getenv("GENAI_FALLBACK_MODEL", "gemini-2.5-flash")
            # Use environment overrides for project and region to ensure diagnostics match runtime
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT", cfg.get("project_id"))
            region = os.getenv("GOOGLE_CLOUD_REGION", cfg.get("region") or "europe-west1")
            prompt = f"OMNI diagnostics ping at {datetime.now().isoformat()}"

            vertex_result = {"ok": False, "model": effective, "source": "vertex", "status": None, "text_snippet": None, "error": None}
            genai_result = {"ok": False, "model": fallback, "source": "genai", "status": None, "text_snippet": None, "error": None}

            # Try Vertex AI via SDK
            try:
                from vertexai.generative_models import GenerativeModel
                import vertexai
                from google.oauth2 import service_account
                sa_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
                if sa_path and os.path.exists(sa_path):
                    try:
                        creds = service_account.Credentials.from_service_account_file(
                            sa_path, scopes=["https://www.googleapis.com/auth/cloud-platform"]
                        )
                        vertexai.init(project=project_id, location=region, credentials=creds)
                    except Exception as cred_e:
                        logger.warning(f"Vertex SA init failed: {cred_e}; using ADC")
                        vertexai.init(project=project_id, location=region)
                else:
                    vertexai.init(project=project_id, location=region)
                model_inst = GenerativeModel(effective)
                resp = model_inst.generate_content(prompt)
                text = getattr(resp, "text", "")
                if not text:
                    try:
                        candidates = getattr(resp, "candidates", [])
                        text = "".join([getattr(c, "output_text", "") for c in candidates])
                    except Exception:
                        text = text or ""
                vertex_result.update({
                    "ok": bool(text),
                    "status": "sdk",
                    "text_snippet": (text[:240] if text else None),
                })
            except Exception as e:
                vertex_result.update({"ok": False, "status": "error", "error": str(e)[:240]})

            # Try GENAI v1 (Google Generative Language API)
            try:
                api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GENAI_API_KEY") or os.getenv("VERTEX_AI_API_KEY") or cfg.get("api_key")
                if api_key:
                    # Prefer library, fallback to REST
                    try:
                        import google.generativeai as genai
                        try:
                            genai.configure(api_key=api_key, transport='rest')
                        except TypeError:
                            genai.configure(api_key=api_key)
                        gen_model = genai.GenerativeModel(fallback)
                        resp = gen_model.generate_content(prompt)
                        text = getattr(resp, "text", "")
                        if not text:
                            try:
                                candidates = getattr(resp, "candidates", [])
                                text = "".join([getattr(c, "output_text", "") for c in candidates])
                            except Exception:
                                text = text or ""
                        genai_result.update({
                            "ok": bool(text),
                            "status": "sdk",
                            "text_snippet": (text[:240] if text else None),
                        })
                    except Exception as lib_e:
                        logger.warning(f"GENAI lib failed: {lib_e}; trying REST v1")
                        try:
                            import requests
                            url = f"https://generativelanguage.googleapis.com/v1/models/{fallback}:generateContent?key={api_key}"
                            payload = {"contents": [{"parts": [{"text": prompt}]}]}
                            r = requests.post(url, json=payload, timeout=15)
                            status = r.status_code
                            text = None
                            if status == 200:
                                j = r.json()
                                try:
                                    cands = j.get("candidates", [])
                                    if cands:
                                        parts = cands[0].get("content", {}).get("parts", [])
                                        if parts:
                                            text = parts[0].get("text", "") or ""
                                except Exception:
                                    text = text or None
                            genai_result.update({
                                "ok": bool(text) and status == 200,
                                "status": status,
                                "text_snippet": (text[:240] if text else None),
                                "error": (None if status == 200 else (r.text[:240] if r.text else f"HTTP {status}"))
                            })
                        except Exception as rest_e:
                            genai_result.update({"ok": False, "status": "error", "error": str(rest_e)[:240]})
                else:
                    genai_result.update({"ok": False, "status": "no_api_key", "error": "Missing GOOGLE_API_KEY/GENAI_API_KEY"})
            except Exception as e:
                genai_result.update({"ok": False, "status": "error", "error": str(e)[:240]})

            return {
                "effective_model": effective,
                "fallback_model": fallback,
                "project_id": project_id,
                "region": region,
                "vertex": vertex_result,
                "genai": genai_result,
                "timestamp": datetime.now().isoformat(),
            }

        # Duplicate /api/gcp/gemini/stream removed (consolidated earlier)

        # Dashboard endpoint
        @self.app.get("/", response_class=HTMLResponse)
        def dashboard():
            return self._generate_dashboard_html()
        
        @self.app.get("/dashboard", response_class=HTMLResponse)
        def dashboard_page():
            return self._generate_dashboard_html()
    
    def _generate_dashboard_html(self) -> str:
        """Generate unified dashboard HTML"""
        active_components = sum(1 for comp in self.components.values() 
                              if comp.get("status") == "active")
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>OMNI Unified Platform Dashboard</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .header h1 {{ font-size: 2.5em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
                .stat-card {{ background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; backdrop-filter: blur(10px); }}
                .stat-card h3 {{ margin: 0 0 10px 0; color: #ffd700; }}
                .components {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
                .component-card {{ background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; backdrop-filter: blur(10px); }}
                .component-card h4 {{ margin: 0 0 10px 0; color: #00ff88; }}
                .status-active {{ color: #00ff88; }}
                .status-inactive {{ color: #ff6b6b; }}
                .endpoints {{ margin-top: 10px; }}
                .endpoint {{ background: rgba(0,0,0,0.2); padding: 5px 10px; margin: 2px 0; border-radius: 5px; font-family: monospace; }}
                .footer {{ text-align: center; margin-top: 30px; opacity: 0.8; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 OMNI Unified Platform</h1>
                    <p>Complete AI Platform with Vertex AI Integration</p>
                </div>
                
                <div class="stats">
                    <div class="stat-card">
                        <h3>Platform Status</h3>
                        <p><strong>Version:</strong> 4.0.0</p>
                        <p><strong>Status:</strong> <span class="status-active">Operational</span></p>
                    </div>
                    <div class="stat-card">
                        <h3>Components</h3>
                        <p><strong>Active:</strong> {active_components}</p>
                        <p><strong>Total:</strong> {len(self.components)}</p>
                    </div>
                    <div class="stat-card">
                        <h3>Vertex AI</h3>
                        <p><strong>Status:</strong> <span class="status-active">Enabled</span></p>
                        <p><strong>Model:</strong> {self.vertex_ai_config.get("vertex_ai", {}).get("model", "N/A")}</p>
                    </div>
                    <div class="stat-card">
                        <h3>System</h3>
                        <p><strong>CPU:</strong> {psutil.cpu_percent(interval=1):.1f}%</p>
                        <p><strong>Memory:</strong> {psutil.virtual_memory().percent:.1f}%</p>
                    </div>
                </div>
                
                <div class="components">
        """
        
        for name, component in self.components.items():
            status_class = "status-active" if component.get("status") == "active" else "status-inactive"
            endpoints_html = ""
            if "endpoints" in component:
                endpoints_html = "<div class='endpoints'>"
                for endpoint in component["endpoints"]:
                    endpoints_html += f"<div class='endpoint'>{endpoint}</div>"
                endpoints_html += "</div>"
            
            html += f"""
                    <div class="component-card">
                        <h4>{name.upper()}</h4>
                        <p><strong>Status:</strong> <span class="{status_class}">{component.get("status", "unknown")}</span></p>
                        <p>{component.get("description", "No description available")}</p>
                        {endpoints_html}
                    </div>
            """
        
        html += f"""
                </div>
                
                <div class="footer">
                    <p>OMNI Unified Platform - Powered by Vertex AI | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def run(self, host: str = "0.0.0.0", port: int = 8080):
        """Run the unified platform"""
        logger.info(f"Starting OMNI Unified Platform on {host}:{port}")
        logger.info(f"Active components: {sum(1 for comp in self.components.values() if comp.get('status') == 'active')}")
        logger.info(f"Vertex AI enabled: {self.vertex_ai_config.get('vertex_ai', {}).get('enabled', False)}")
        
        uvicorn.run(self.app, host=host, port=port)

app = OmniUnifiedPlatform().app

if __name__ == "__main__":
    # Set environment variables for Vertex AI
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "refined-graph-471712-n9")
    os.environ.setdefault("GOOGLE_CLOUD_REGION", "europe-west1")
    os.environ.setdefault("VERTEX_AI_MODEL", "gemini-2.5-pro")
    os.environ.setdefault("VERTEX_AI_API_KEY", "AQ.Ab8RN6LjDXj9_BHBcp-XvbSm0WCE2ftjfwyobHz-Zc3oNMVfhQ")
    
    # Get host and port from environment
    host = os.getenv("HOST", "0.0.0.0")
    try:
        port = int(os.getenv("PORT", "8080"))
    except (TypeError, ValueError):
        port = 8080
    
    # Create and run the unified platform
    unified_app = OmniUnifiedPlatform()
    unified_app.run(host=host, port=port)