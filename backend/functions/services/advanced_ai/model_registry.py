"""Lightweight in-memory model registry service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
import uuid


class ModelRegistryService:
    """Track model versions, stages, and traffic allocations."""

    def __init__(self) -> None:
        self._models: Dict[str, Dict[str, Any]] = {
            "revenue_forecaster": {
                "description": "Time-series revenue forecasting ensemble",
                "owner": "ml-platform",
                "active_version": "v1",
                "canary_version": None,
                "traffic": {"production": 100, "canary": 0},
                "versions": {
                    "v1": {
                        "version": "v1",
                        "status": "production",
                        "created_at": datetime(2025, 9, 12, tzinfo=timezone.utc),
                        "metrics": {"rmse": 420.7, "mape": 0.08},
                        "artifact_uri": "gs://omni-models/revenue_forecaster/v1/model.pkl",
                        "metadata": {"framework": "prophet", "notes": "Baseline ensemble"},
                    }
                },
            }
        }

    async def list_models(self) -> Dict[str, Any]:
        """Return a summary of all tracked models."""
        return {name: self._serialize_model(name, data) for name, data in self._models.items()}

    async def get_model(self, model_name: str) -> Dict[str, Any]:
        model = self._models.get(model_name)
        if not model:
            raise KeyError(model_name)
        return self._serialize_model(model_name, model)

    async def register_version(
        self,
        model_name: str,
        version: str,
        artifact_uri: str,
        metrics: Dict[str, float] | None = None,
        metadata: Dict[str, Any] | None = None,
        stage: str = "staging",
        created_by: str | None = None,
    ) -> Dict[str, Any]:
        model = self._models.setdefault(
            model_name,
            {
                "description": "",
                "owner": created_by or "unknown",
                "active_version": None,
                "canary_version": None,
                "traffic": {"production": 100, "canary": 0},
                "versions": {},
            },
        )

        entry = {
            "version": version,
            "status": stage,
            "created_at": datetime.now(timezone.utc),
            "metrics": metrics or {},
            "artifact_uri": artifact_uri,
            "metadata": metadata or {},
            "created_by": created_by or "unknown",
            "run_id": str(uuid.uuid4()),
        }
        model["versions"][version] = entry

        if stage == "production":
            model["active_version"] = version
            model["traffic"] = {"production": 100, "canary": 0}
            model["canary_version"] = None
        elif stage == "canary":
            model["canary_version"] = version
            model["traffic"]["canary"] = max(model["traffic"].get("canary", 0), 10)
            model["traffic"]["production"] = 100 - model["traffic"]["canary"]

        return await self.get_model(model_name)

    async def promote_version(
        self,
        model_name: str,
        version: str,
        canary_percent: int | None = None,
    ) -> Dict[str, Any]:
        model = self._models.get(model_name)
        if not model or version not in model["versions"]:
            raise KeyError(version)
        model["active_version"] = version
        model["versions"][version]["status"] = "production"
        if canary_percent is not None:
            canary_percent = max(0, min(100, canary_percent))
            model["traffic"]["production"] = 100 - canary_percent
            model["traffic"]["canary"] = canary_percent
            model["canary_version"] = None if canary_percent == 0 else model.get("canary_version")
        else:
            model["traffic"] = {"production": 100, "canary": 0}
            model["canary_version"] = None
        return await self.get_model(model_name)

    async def update_canary_split(
        self,
        model_name: str,
        canary_version: str,
        canary_percent: int,
    ) -> Dict[str, Any]:
        model = self._models.get(model_name)
        if not model or canary_version not in model["versions"]:
            raise KeyError(canary_version)
        canary_percent = max(0, min(100, canary_percent))
        model["canary_version"] = canary_version if canary_percent > 0 else None
        model["traffic"] = {"production": 100 - canary_percent, "canary": canary_percent}
        model["versions"][canary_version]["status"] = "canary" if canary_percent > 0 else "staging"
        return await self.get_model(model_name)

    def _serialize_model(self, name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        versions = [self._serialize_version(v) for v in data["versions"].values()]
        versions.sort(key=lambda item: item["created_at"], reverse=True)
        return {
            "name": name,
            "description": data.get("description", ""),
            "owner": data.get("owner", "unknown"),
            "active_version": data.get("active_version"),
            "canary_version": data.get("canary_version"),
            "traffic": data.get("traffic", {"production": 100, "canary": 0}),
            "versions": versions,
        }

    def _serialize_version(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "version": entry.get("version"),
            "status": entry.get("status"),
            "created_at": entry.get("created_at", datetime.now(timezone.utc)).isoformat(),
            "metrics": entry.get("metrics", {}),
            "artifact_uri": entry.get("artifact_uri"),
            "metadata": entry.get("metadata", {}),
            "created_by": entry.get("created_by", "unknown"),
            "run_id": entry.get("run_id"),
        }
