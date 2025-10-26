from fastapi import APIRouter
try:
    import psutil  # type: ignore
except Exception:
    psutil = None

router = APIRouter(prefix="/agents", tags=["agents-monitor"]) 

@router.get("/health")
async def agents_health():
    cpu = psutil.cpu_percent(interval=0.25) if psutil else 0.0
    status = "healthy" if cpu < 85.0 else "degraded"
    degraded_reason = "cpu_high" if status == "degraded" else None
    return {"ok": True, "cpu": cpu, "status": status, "degraded_reason": degraded_reason}