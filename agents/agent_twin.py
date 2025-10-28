import os
from typing import Dict, Any, List

import httpx
from fastapi import Body
from pydantic import BaseModel

from .common import build_app


app = build_app("omni-twin")


DEFAULT_SERVICES = {
    "omni-tasks": os.getenv("TASKS_URL", "http://omni-tasks:8000/health"),
    "omni-marketing": os.getenv("MARKETING_URL", "http://omni-marketing:8000/health"),
    "omni-feedback": os.getenv("FEEDBACK_URL", "http://omni-feedback:8000/health"),
    "omni-minctx": os.getenv("MINCTX_URL", "http://omni-minctx:8000/health"),
    "omni-pov": os.getenv("POV_URL", "http://omni-pov:8000/health"),
    "omni-value": os.getenv("VALUE_URL", "http://omni-value:8000/health"),
}


class HealRequest(BaseModel):
    services: Dict[str, str] = DEFAULT_SERVICES
    force_reload: bool = True


async def check_health(url: str) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(url)
        ok = r.status_code == 200
        return {"ok": ok, "status_code": r.status_code, "body": r.text[:200]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/diagnose")
async def diagnose():
    results: Dict[str, Any] = {}
    for name, url in DEFAULT_SERVICES.items():
        results[name] = await check_health(url)
    degraded = {k: v for k, v in results.items() if not v.get("ok")}
    return {
        "services": results,
        "degraded": list(degraded.keys()),
        "summary": "healthy" if not degraded else "degraded",
    }


@app.post("/heal")
async def heal(req: HealRequest = Body(...)):
    diag = {name: await check_health(url) for name, url in req.services.items()}
    degraded = [k for k, v in diag.items() if not v.get("ok")]

    actions: List[str] = []
    if degraded:
        actions.append(f"Detected degraded: {', '.join(degraded)}")
    if req.force_reload:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                await client.post(
                    os.getenv("FEEDBACK_REPORT_URL", "http://omni-feedback:8000/feedback"),
                    json={
                        "service": "omni-twin",
                        "severity": "warn",
                        "message": f"Self-heal triggered; degraded: {degraded}",
                        "regenerate_docs": True,
                        "force_reload": True,
                    },
                )
            actions.append("Triggered omni-feedback doc regen and reload flag.")
        except Exception as e:
            actions.append(f"Failed to call omni-feedback: {e}")

    actions.append("Recommend container restart for persistently failing services.")
    return {"diagnosis": diag, "actions": actions}