"""AutoML orchestration helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict
import random
import uuid


class AutoMLOrchestrator:
    """Simulate AutoML training lifecycle for demos/tests."""

    def __init__(self) -> None:
        self._jobs: Dict[str, Dict[str, Any]] = {}

    async def start_training(
        self,
        dataset_uri: str,
        problem_type: str,
        target_column: str,
        objective_metric: str = "accuracy",
        budget_hours: float = 1.0,
    ) -> Dict[str, Any]:
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        eta = now + timedelta(minutes=max(5, int(budget_hours * 10)))
        job = {
            "id": job_id,
            "dataset_uri": dataset_uri,
            "problem_type": problem_type,
            "target_column": target_column,
            "objective_metric": objective_metric,
            "status": "running",
            "created_at": now,
            "updated_at": now,
            "estimated_completion": eta,
            "model_artifact": None,
            "metrics": {},
        }
        self._jobs[job_id] = job
        return await self.get_job(job_id)

    async def get_job(self, job_id: str) -> Dict[str, Any]:
        job = self._jobs.get(job_id)
        if not job:
            raise KeyError(job_id)
        now = datetime.now(timezone.utc)
        if job["status"] == "running" and now >= job["estimated_completion"]:
            job["status"] = "succeeded"
            job["updated_at"] = now
            job["model_artifact"] = f"gs://omni-models/automl/{job_id}/model.keras"
            job["metrics"] = {
                job["objective_metric"]: round(random.uniform(0.82, 0.95), 4),
                "validation_loss": round(random.uniform(0.2, 0.6), 4),
            }
        return {
            "id": job["id"],
            "status": job["status"],
            "dataset_uri": job["dataset_uri"],
            "problem_type": job["problem_type"],
            "target_column": job["target_column"],
            "objective_metric": job["objective_metric"],
            "metrics": job["metrics"],
            "model_artifact": job["model_artifact"],
            "created_at": job["created_at"].isoformat(),
            "updated_at": job["updated_at"].isoformat(),
            "estimated_completion": job["estimated_completion"].isoformat(),
        }
