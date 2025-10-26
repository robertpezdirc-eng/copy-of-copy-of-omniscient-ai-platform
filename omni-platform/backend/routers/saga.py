from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

from routers.access_controller import require_api_key
from infra.saga_orchestrator import SagaOrchestrator, LicenseActivationScenario
from adapters.message_broker import get_broker

router = APIRouter(prefix="/transactions", tags=["transactions", "saga"])

class LicenseActivationRequest(BaseModel):
    tenant_id: Optional[str] = None
    amount: Optional[float] = None
    simulate_payment_fail: bool = False
    simulate_license_fail: bool = False
    simulate_schedule_fail: bool = False

@router.get("/health")
async def health(_: None = Depends(require_api_key)):
    try:
        broker = await get_broker()
        await broker.publish("saga.health", {"ping": True})
        return JSONResponse({"status": "ok"})
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)}, status_code=500)

@router.post("/license_activation")
async def license_activation(req: LicenseActivationRequest, _: None = Depends(require_api_key)):
    orchestrator = SagaOrchestrator()
    scenario = LicenseActivationScenario()
    context = {
        "tenant_id": req.tenant_id,
        "amount": req.amount,
        "simulate_payment_fail": req.simulate_payment_fail,
        "simulate_license_fail": req.simulate_license_fail,
        "simulate_schedule_fail": req.simulate_schedule_fail,
    }
    steps = scenario.build_saga()
    result = await orchestrator.run(steps, context)
    status_code = 200 if result.success else 500
    return JSONResponse({
        "success": result.success,
        "steps_completed": result.steps_completed,
        "steps_compensated": result.steps_compensated,
        "error": result.error,
    }, status_code=status_code)