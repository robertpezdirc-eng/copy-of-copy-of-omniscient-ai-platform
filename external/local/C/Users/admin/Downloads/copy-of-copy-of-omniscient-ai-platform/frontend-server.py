#!/usr/bin/env python3
"""
Omni Platform Frontend Server
Serves the web interface for the Omni Platform
"""

import os
import json
import asyncio
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI(title="Omni Platform Frontend", version="1.0.0")

# Configuration
OMNI_API_BASE = os.getenv("OMNI_API_BASE", "http://localhost:8080")
FRONTEND_FILE = "omni-frontend.html"

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main frontend interface"""
    try:
        with open(FRONTEND_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        return HTMLResponse(content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Frontend file not found")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "omni-frontend",
        "version": "1.0.0"
    }

@app.get("/api/proxy/gemini")
async def proxy_gemini(request: Request):
    """Proxy requests to the Gemini API"""
    try:
        # Get query parameters
        prompt = request.query_params.get('prompt', '')
        model = request.query_params.get('model', 'gemini-2.0-flash')

        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")

        # Forward request to Omni API
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OMNI_API_BASE}/api/gcp/gemini",
                json={"prompt": prompt, "model": model},
                timeout=60.0
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "ok": False,
                    "error": f"API returned status {response.status_code}",
                    "details": response.text
                }

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")

@app.get("/api/system/status")
async def system_status():
    """Get comprehensive system status"""
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            # Check backend API health
            backend_response = await client.get(f"{OMNI_API_BASE}/readyz", timeout=10.0)

            return {
                "frontend": {
                    "status": "online",
                    "timestamp": datetime.utcnow().isoformat()
                },
                "backend": {
                    "status": "online" if backend_response.status_code == 200 else "offline",
                    "response_time": "N/A",
                    "url": OMNI_API_BASE
                },
                "gemini": {
                    "model": "gemini-2.0-flash",
                    "status": "available",
                    "region": "europe-west1"
                }
            }
    except Exception as e:
        return {
            "frontend": {
                "status": "online",
                "timestamp": datetime.utcnow().isoformat()
            },
            "backend": {
                "status": "error",
                "error": str(e)
            },
            "gemini": {
                "model": "gemini-2.0-flash",
                "status": "unknown"
            }
        }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"🚀 Starting Omni Platform Frontend Server on port {port}")
    print(f"📡 Backend API: {OMNI_API_BASE}")
    print(f"🌐 Frontend: http://localhost:{port}")

    uvicorn.run(app, host="0.0.0.0", port=port)