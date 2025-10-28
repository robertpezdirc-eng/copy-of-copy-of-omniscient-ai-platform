import os
import time
from typing import Dict, Any, List, Optional

import httpx
from pydantic import BaseModel, Field

from .common import build_app, get_async_client


app = build_app("omni_adapt")


PROM_URL = os.getenv("PROMETHEUS_URL", "http://omni-prometheus:9090")
RL_CORE_URL = os.getenv("RL_CORE_URL", "http://agent-rl-core:8000")


class EvaluateRequest(BaseModel):
    target_url: Optional[str] = Field(None, description="HTTP endpoint AI storitve za test")
    scenario: Optional[str] = Field(None, description="Ime vgrajenega scenarija")
    trials: int = Field(5, ge=1, le=50, description="Število poskusov/iteracij")
    budget_seconds: int = Field(60, ge=5, le=3600, description="Časovni proračun testa")
    noise_level: float = Field(0.0, ge=0, le=1, description="Raven šuma za robustnost")
    resource_pressure: float = Field(0.0, ge=0, le=1, description="Simuliran pritisk virov")
    notes: Optional[str] = None


@app.get("/benchmarks")
async def benchmarks() -> Dict[str, Any]:
    return {
        "benchmarks": [
            {
                "name": "domain_shift",
                "description": "Ocenjuje prilagoditev na domenske spremembe (drugačna porazdelitev).",
                "signals": ["accuracy_drop", "recovery_time", "sample_efficiency"],
            },
            {
                "name": "noise_robustness",
                "description": "Občutljivost na vhodni šum in nenatančne podatke.",
                "signals": ["stability", "latency_variance", "error_spike_resistance"],
            },
            {
                "name": "latency_budget",
                "description": "Delovanje pod omejitvami latence in CPU/GPU proračuna.",
                "signals": ["graceful_degradation", "p95_latency", "throughput"],
            },
            {
                "name": "failure_recovery",
                "description": "Hitrost in kvaliteta okrevanja po napaki/odklopu.",
                "signals": ["mttr", "state_resilience", "consistency"],
            },
            {
                "name": "data_sparsity",
                "description": "Učinkovitost učenja pri malo podatkih in s prenosom znanja.",
                "signals": ["sample_efficiency", "few_shot_quality", "overfit_risk"],
            },
        ]
    }


@app.post("/evaluate")
async def evaluate(req: EvaluateRequest) -> Dict[str, Any]:
    start_ts = time.time()

    # 1) Preprost aktivni ping tarče (če je podana), da zabeležimo osnovno latenco in stabilnost
    latencies: List[float] = []
    errors = 0
    if req.target_url:
        client = get_async_client()
        for i in range(req.trials):
            try:
                t0 = time.time()
                r = await client.get(req.target_url, timeout=10.0)
                r.raise_for_status()
                latencies.append(time.time() - t0)
            except Exception:
                errors += 1
            if time.time() - start_ts > req.budget_seconds:
                break

    # 2) Hevristično ocenimo pod-metrike prilagodljivosti
    # Opomba: to je stub, v prihodnje se poveže na realne metrike iz Prometheusa in eksperimente z RL core
    p95 = sorted(latencies)[int(0.95 * len(latencies)) - 1] if latencies else None
    stability = max(0.0, 1.0 - (errors / max(1, req.trials)))
    graceful_degradation = max(0.0, 1.0 - 0.5 * req.resource_pressure - 0.3 * req.noise_level)
    sample_efficiency = max(0.1, 1.0 - 0.1 * req.trials)  # manj poskusov -> boljša učinkovitost (igrano)

    submetrics = {
        "stability": stability,
        "graceful_degradation": graceful_degradation,
        "sample_efficiency": sample_efficiency,
        "p95_latency": p95 or -1,
        "errors": errors,
        "observations": len(latencies),
    }

    # 3) Izračun skupne ocene
    weights = {"stability": 0.35, "graceful_degradation": 0.35, "sample_efficiency": 0.30}
    score = (
        weights["stability"] * submetrics["stability"]
        + weights["graceful_degradation"] * submetrics["graceful_degradation"]
        + weights["sample_efficiency"] * submetrics["sample_efficiency"]
    )

    # 4) Poskus predloga politike iz RL jedra (neobvezno)
    rl_result = None
    try:
        client = get_async_client()
        payload = {
            "objective": "improve_adaptability",
            "hints": {"scenario": req.scenario, "resource_pressure": req.resource_pressure, "noise": req.noise_level},
        }
        rr = await client.post(f"{RL_CORE_URL}/train", json=payload, timeout=15.0)
        if rr.status_code < 300:
            rl_result = rr.json()
    except Exception:
        rl_result = None

    return {
        "adaptability_score": round(score, 3),
        "submetrics": submetrics,
        "rl_core": rl_result,
        "scenario": req.scenario,
        "duration_sec": round(time.time() - start_ts, 3),
        "target": req.target_url,
        "notes": req.notes,
    }


class PlanRequest(BaseModel):
    target: Optional[str] = None
    constraints: Dict[str, Any] = Field(default_factory=dict)


@app.post("/plan")
async def plan(req: PlanRequest) -> Dict[str, Any]:
    constraints = req.constraints or {}
    cost_sensitivity = constraints.get("cost_sensitivity", "medium")
    perf_target = constraints.get("p95_latency_ms", 300)

    recommendations = [
        {"action": "enable_dynamic_batching", "benefit": "latency/throughput balance", "risk": "complexity"},
        {"action": "graceful_degradation_strategies", "benefit": "robustness under load", "risk": "reduced_quality"},
        {"action": "canary_policy_updates", "benefit": "safer adaptations", "risk": "slower rollout"},
        {"action": "few_shot_finetune_on_shift", "benefit": "domain shift resilience", "risk": "cost/time"},
    ]

    finops = {
        "cost_sensitivity": cost_sensitivity,
        "estimated_monthly_cost_delta": {
            "low": "+$50-$150",
            "medium": "+$200-$600",
            "high": "+$800-$2000",
        }.get(cost_sensitivity, "unknown"),
        "perf_target_p95_ms": perf_target,
    }

    return {
        "target": req.target,
        "recommendations": recommendations,
        "finops": finops,
    }