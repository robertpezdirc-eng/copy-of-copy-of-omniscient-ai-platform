import asyncio
import logging
from typing import Callable, Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, time as dt_time

from learning.feedback_store import FeedbackStore
from adapters.message_broker import get_broker

logger = logging.getLogger("infra.saga")

@dataclass
class SagaStep:
    name: str
    execute: Callable[[Dict[str, Any]], asyncio.Future]
    compensate: Callable[[Dict[str, Any]], asyncio.Future]

@dataclass
class SagaResult:
    success: bool
    steps_completed: List[str]
    steps_compensated: List[str]
    error: Optional[str] = None

class SagaOrchestrator:
    def __init__(self) -> None:
        self.store = FeedbackStore()

    async def run(self, steps: List[SagaStep], context: Dict[str, Any]) -> SagaResult:
        broker = await get_broker()
        completed: List[str] = []
        compensated: List[str] = []
        try:
            for step in steps:
                logger.info(f"Executing saga step: {step.name}")
                await broker.publish("saga.events", {"type": "step_start", "name": step.name, "context": context})
                await step.execute(context)
                completed.append(step.name)
                await broker.publish("saga.events", {"type": "step_done", "name": step.name, "context": context})
            await broker.publish("saga.events", {"type": "saga_success", "context": context})
            self.store.insert_event({
                "agent_type": "saga",
                "provider": "local",
                "model": "orchestrator",
                "task_type": "transaction",
                "success": True,
                "reward": 1.0,
                "latency_ms": 0,
                "meta": {"steps": completed},
            })
            return SagaResult(success=True, steps_completed=completed, steps_compensated=compensated)
        except Exception as e:
            logger.error(f"Saga failed at step {completed[-1] if completed else 'start'}: {e}")
            await broker.publish("saga.events", {"type": "saga_failed", "error": str(e), "context": context})
            # Rollback in reverse order
            for step_name in reversed(completed):
                step = next(s for s in steps if s.name == step_name)
                try:
                    await broker.publish("saga.events", {"type": "compensate_start", "name": step.name, "context": context})
                    await step.compensate(context)
                    compensated.append(step.name)
                    await broker.publish("saga.events", {"type": "compensate_done", "name": step.name, "context": context})
                except Exception as ce:
                    logger.error(f"Compensation error for {step.name}: {ce}")
            self.store.insert_event({
                "agent_type": "saga",
                "provider": "local",
                "model": "orchestrator",
                "task_type": "transaction",
                "success": False,
                "reward": 0.0,
                "latency_ms": 0,
                "meta": {"error": str(e), "compensated": compensated},
            })
            return SagaResult(success=False, steps_completed=completed, steps_compensated=compensated, error=str(e))

# Vzorčni scenarij: "stranka plača -> agent dobi licenco -> agent se zažene vedno popoldne"
class LicenseActivationScenario:
    def __init__(self) -> None:
        self.store = FeedbackStore()

    async def process_payment(self, ctx: Dict[str, Any]) -> None:
        # Simuliraj plačilo (uspeh ali napaka po parametru)
        if ctx.get("simulate_payment_fail"):
            raise RuntimeError("payment_failed")
        self.store.insert_event({
            "agent_type": "billing",
            "provider": "local",
            "model": "payment",
            "task_type": "billing",
            "success": True,
            "reward": 1.0,
            "latency_ms": 0,
            "meta": {"tenant_id": ctx.get("tenant_id"), "amount": ctx.get("amount")},
        })

    async def refund_payment(self, ctx: Dict[str, Any]) -> None:
        self.store.insert_event({
            "agent_type": "billing",
            "provider": "local",
            "model": "refund",
            "task_type": "billing",
            "success": True,
            "reward": 0.5,
            "latency_ms": 0,
            "meta": {"tenant_id": ctx.get("tenant_id"), "amount": ctx.get("amount")},
        })

    async def grant_license(self, ctx: Dict[str, Any]) -> None:
        if ctx.get("simulate_license_fail"):
            raise RuntimeError("license_issue")
        self.store.set_policy_state(None, {"agent": {"openai": "gpt-4o"}})

    async def revoke_license(self, ctx: Dict[str, Any]) -> None:
        # Preprosto počistimo agent prefs
        state = self.store.get_policy_state()
        self.store.set_policy_state(state.get("provider_priority"), {})

    async def schedule_afternoon_start(self, ctx: Dict[str, Any]) -> None:
        if ctx.get("simulate_schedule_fail"):
            raise RuntimeError("schedule_error")
        # Zabeleži časovni slot 15:00 lokalno
        slot = dt_time(hour=15, minute=0)
        self.store.insert_event({
            "agent_type": "scheduler",
            "provider": "local",
            "model": "afternoon",
            "task_type": "schedule",
            "success": True,
            "reward": 1.0,
            "latency_ms": 0,
            "meta": {"scheduled_time": slot.isoformat()},
        })

    async def cancel_schedule(self, ctx: Dict[str, Any]) -> None:
        self.store.insert_event({
            "agent_type": "scheduler",
            "provider": "local",
            "model": "cancel",
            "task_type": "schedule",
            "success": True,
            "reward": 0.5,
            "latency_ms": 0,
            "meta": {},
        })

    def build_saga(self) -> List[SagaStep]:
        return [
            SagaStep("payment", self.process_payment, self.refund_payment),
            SagaStep("license", self.grant_license, self.revoke_license),
            SagaStep("schedule", self.schedule_afternoon_start, self.cancel_schedule),
        ]