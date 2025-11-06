"""Automated MLOps Pipeline for training, testing, and deployment."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import random
import uuid
import logging

logger = logging.getLogger(__name__)


class MLOpsPipeline:
    """Automated ML pipeline for training, testing, deploying, and monitoring models."""

    def __init__(self) -> None:
        self._pipelines: Dict[str, Dict[str, Any]] = {}
        self._metrics_history: Dict[str, List[Dict[str, Any]]] = {}

    async def create_pipeline(
        self,
        model_name: str,
        dataset_uri: str,
        target_metric: str = "accuracy",
        threshold: float = 0.85,
        auto_deploy: bool = True,
        schedule: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create an automated MLOps pipeline."""
        pipeline_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        pipeline = {
            "id": pipeline_id,
            "model_name": model_name,
            "dataset_uri": dataset_uri,
            "target_metric": target_metric,
            "threshold": threshold,
            "auto_deploy": auto_deploy,
            "schedule": schedule or "daily",
            "status": "active",
            "created_at": now,
            "last_run": None,
            "next_run": now + timedelta(days=1),
            "runs": [],
        }
        
        self._pipelines[pipeline_id] = pipeline
        self._metrics_history[pipeline_id] = []
        
        logger.info(f"Created MLOps pipeline {pipeline_id} for model {model_name}")
        return self._serialize_pipeline(pipeline_id)

    async def trigger_pipeline(self, pipeline_id: str) -> Dict[str, Any]:
        """Manually trigger a pipeline run."""
        pipeline = self._pipelines.get(pipeline_id)
        if not pipeline:
            raise KeyError(pipeline_id)
        
        run_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        run = {
            "id": run_id,
            "started_at": now,
            "status": "training",
            "steps": {
                "data_validation": {"status": "completed", "duration_ms": 1234},
                "training": {"status": "running", "duration_ms": None},
                "evaluation": {"status": "pending", "duration_ms": None},
                "deployment": {"status": "pending", "duration_ms": None},
            },
            "metrics": {},
            "artifacts": {},
        }
        
        pipeline["runs"].append(run)
        pipeline["last_run"] = now
        pipeline["next_run"] = self._calculate_next_run(now, pipeline["schedule"])
        
        logger.info(f"Triggered pipeline {pipeline_id}, run {run_id}")
        return {
            "pipeline_id": pipeline_id,
            "run_id": run_id,
            "status": "started",
            "started_at": now.isoformat(),
        }

    async def get_pipeline_status(self, pipeline_id: str) -> Dict[str, Any]:
        """Get pipeline status and latest runs."""
        pipeline = self._pipelines.get(pipeline_id)
        if not pipeline:
            raise KeyError(pipeline_id)
        
        # Simulate pipeline progress
        if pipeline["runs"]:
            latest_run = pipeline["runs"][-1]
            if latest_run["status"] == "training":
                # Simulate training completion
                latest_run["status"] = "evaluating"
                latest_run["steps"]["training"]["status"] = "completed"
                latest_run["steps"]["training"]["duration_ms"] = 45000
                latest_run["steps"]["evaluation"]["status"] = "running"
                
                # Generate training metrics
                latest_run["metrics"] = {
                    pipeline["target_metric"]: round(random.uniform(0.82, 0.96), 4),
                    "loss": round(random.uniform(0.1, 0.4), 4),
                    "val_loss": round(random.uniform(0.15, 0.45), 4),
                }
                
            elif latest_run["status"] == "evaluating":
                # Simulate evaluation and deployment
                metric_value = latest_run["metrics"][pipeline["target_metric"]]
                passed_threshold = metric_value >= pipeline["threshold"]
                
                latest_run["steps"]["evaluation"]["status"] = "completed"
                latest_run["steps"]["evaluation"]["duration_ms"] = 3500
                
                if pipeline["auto_deploy"] and passed_threshold:
                    latest_run["status"] = "deploying"
                    latest_run["steps"]["deployment"]["status"] = "running"
                else:
                    latest_run["status"] = "completed"
                    latest_run["deployment_approved"] = False
                    latest_run["reason"] = (
                        "Metric below threshold" if not passed_threshold 
                        else "Auto-deploy disabled"
                    )
                    
            elif latest_run["status"] == "deploying":
                # Simulate deployment completion
                latest_run["status"] = "deployed"
                latest_run["steps"]["deployment"]["status"] = "completed"
                latest_run["steps"]["deployment"]["duration_ms"] = 8000
                latest_run["artifacts"]["model_uri"] = (
                    f"gs://omni-models/{pipeline['model_name']}/{latest_run['id']}/model.pkl"
                )
                latest_run["artifacts"]["version"] = f"v{len(pipeline['runs'])}"
                
                # Store metrics for monitoring
                self._metrics_history[pipeline_id].append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "run_id": latest_run["id"],
                    "metrics": latest_run["metrics"],
                })
        
        return self._serialize_pipeline(pipeline_id)

    async def list_pipelines(self) -> List[Dict[str, Any]]:
        """List all MLOps pipelines."""
        return [self._serialize_pipeline(pid) for pid in self._pipelines.keys()]

    async def get_metrics_history(
        self, 
        pipeline_id: str, 
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get performance metrics history for monitoring."""
        pipeline = self._pipelines.get(pipeline_id)
        if not pipeline:
            raise KeyError(pipeline_id)
        
        history = self._metrics_history.get(pipeline_id, [])
        recent_history = history[-limit:]
        
        # Calculate trend
        if len(recent_history) >= 2:
            first_metric = recent_history[0]["metrics"].get(pipeline["target_metric"], 0)
            last_metric = recent_history[-1]["metrics"].get(pipeline["target_metric"], 0)
            trend = ((last_metric - first_metric) / first_metric * 100) if first_metric else 0
        else:
            trend = 0
        
        return {
            "pipeline_id": pipeline_id,
            "model_name": pipeline["model_name"],
            "target_metric": pipeline["target_metric"],
            "history": recent_history,
            "trend_percent": round(trend, 2),
            "current_threshold": pipeline["threshold"],
            "meets_threshold": (
                recent_history[-1]["metrics"].get(pipeline["target_metric"], 0) >= pipeline["threshold"]
                if recent_history else None
            ),
        }

    async def update_alert_threshold(
        self, 
        pipeline_id: str, 
        new_threshold: float
    ) -> Dict[str, Any]:
        """Update the performance threshold for alerts."""
        pipeline = self._pipelines.get(pipeline_id)
        if not pipeline:
            raise KeyError(pipeline_id)
        
        old_threshold = pipeline["threshold"]
        pipeline["threshold"] = new_threshold
        
        logger.info(
            f"Updated threshold for pipeline {pipeline_id} from {old_threshold} to {new_threshold}"
        )
        
        return self._serialize_pipeline(pipeline_id)

    def _serialize_pipeline(self, pipeline_id: str) -> Dict[str, Any]:
        """Serialize pipeline data for API response."""
        pipeline = self._pipelines[pipeline_id]
        
        # Get latest run summary
        latest_run = None
        if pipeline["runs"]:
            run = pipeline["runs"][-1]
            latest_run = {
                "id": run["id"],
                "status": run["status"],
                "started_at": run["started_at"].isoformat(),
                "metrics": run.get("metrics", {}),
                "artifacts": run.get("artifacts", {}),
            }
        
        return {
            "id": pipeline["id"],
            "model_name": pipeline["model_name"],
            "dataset_uri": pipeline["dataset_uri"],
            "target_metric": pipeline["target_metric"],
            "threshold": pipeline["threshold"],
            "auto_deploy": pipeline["auto_deploy"],
            "schedule": pipeline["schedule"],
            "status": pipeline["status"],
            "created_at": pipeline["created_at"].isoformat(),
            "last_run": pipeline["last_run"].isoformat() if pipeline["last_run"] else None,
            "next_run": pipeline["next_run"].isoformat(),
            "total_runs": len(pipeline["runs"]),
            "latest_run": latest_run,
        }

    def _calculate_next_run(self, last_run: datetime, schedule: str) -> datetime:
        """Calculate next scheduled run time."""
        if schedule == "hourly":
            return last_run + timedelta(hours=1)
        elif schedule == "daily":
            return last_run + timedelta(days=1)
        elif schedule == "weekly":
            return last_run + timedelta(weeks=1)
        else:
            return last_run + timedelta(days=1)
