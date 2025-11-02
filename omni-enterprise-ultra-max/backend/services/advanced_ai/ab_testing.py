"""Simple in-memory A/B testing tracker.

Thread-safety: this service uses an asyncio.Lock to guard writes to the
in-memory experiments map to avoid race conditions under concurrent access.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List
import uuid
import asyncio


class ABTestingService:
    """Manage experiment metadata and metrics."""

    def __init__(self) -> None:
        self._experiments: Dict[str, Dict[str, Any]] = {}
        # Guard concurrent writes/updates to the in-memory store
        self._lock = asyncio.Lock()

    async def create_experiment(
        self,
        name: str,
        variants: List[str],
        primary_metric: str,
        owner: str | None = None,
    ) -> Dict[str, Any]:
        experiment_id = str(uuid.uuid4())
        normalized_variants = [v.lower() for v in variants]
        async with self._lock:
            self._experiments[experiment_id] = {
                "id": experiment_id,
                "name": name,
                "variants": normalized_variants,
                "primary_metric": primary_metric,
                "owner": owner or "growth-team",
                "created_at": datetime.now(timezone.utc),
                "status": "running",
                "metrics": defaultdict(lambda: {"impressions": 0, "conversions": 0, "value": 0.0}),
                "notes": [],
            }
            # Initialize metrics entries for each variant so views include all variants from the start
            for v in normalized_variants:
                _ = self._experiments[experiment_id]["metrics"][v]
        return await self.get_experiment(experiment_id)

    async def record_event(
        self,
        experiment_id: str,
        variant: str,
        event_type: str,
        value: float | None = None,
    ) -> Dict[str, Any]:
        async with self._lock:
            experiment = self._require_experiment(experiment_id)
            if experiment["status"] != "running":
                # Ignore events for completed experiments
                return await self.get_experiment(experiment_id)
            variant = variant.lower()
            if variant not in experiment["variants"]:
                raise KeyError(variant)
            metrics = experiment["metrics"][variant]
            if event_type == "impression":
                metrics["impressions"] += 1
            elif event_type == "conversion":
                metrics["conversions"] += 1
                if value is not None:
                    metrics["value"] += float(value)
            else:
                experiment["notes"].append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event": event_type,
                    "variant": variant,
                    "value": value,
                })
        return await self.get_experiment(experiment_id)

    async def finalize_experiment(
        self,
        experiment_id: str,
        winning_variant: str | None = None,
        summary: str | None = None,
    ) -> Dict[str, Any]:
        async with self._lock:
            experiment = self._require_experiment(experiment_id)
            experiment["status"] = "completed"
            experiment["completed_at"] = datetime.now(timezone.utc)
            experiment["winner"] = winning_variant.lower() if winning_variant else None
            if summary:
                experiment["notes"].append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event": "summary",
                    "details": summary,
                })
        return await self.get_experiment(experiment_id)

    async def get_experiment(self, experiment_id: str) -> Dict[str, Any]:
        experiment = self._require_experiment(experiment_id)
        view = {
            "id": experiment["id"],
            "name": experiment["name"],
            "variants": [],
            "primary_metric": experiment["primary_metric"],
            "owner": experiment["owner"],
            "status": experiment["status"],
            "created_at": experiment["created_at"].isoformat(),
            "completed_at": experiment.get("completed_at", None),
            "winner": experiment.get("winner"),
            "notes": experiment.get("notes", []),
        }
        for variant, metrics in experiment["metrics"].items():
            impressions = metrics["impressions"] or 1
            conversion_rate = metrics["conversions"] / impressions
            avg_value = metrics["value"] / metrics["conversions"] if metrics["conversions"] else 0.0
            view["variants"].append(
                {
                    "name": variant,
                    "impressions": metrics["impressions"],
                    "conversions": metrics["conversions"],
                    "conversion_rate": round(conversion_rate, 4),
                    "average_value": round(avg_value, 2),
                }
            )
        view["variants"].sort(key=lambda item: item["conversion_rate"], reverse=True)
        return view

    def _require_experiment(self, experiment_id: str) -> Dict[str, Any]:
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            raise KeyError(experiment_id)
        return experiment
