"""Advanced AI platform routes: model registry, A/B testing, AutoML, multi-modal."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator

# Import caching utility
from utils.cache import cache_response

logger = logging.getLogger(__name__)

router = APIRouter()

try:
    from services.advanced_ai import (
        get_model_registry_service,
        get_ab_testing_service,
        get_automl_service,
        get_multimodal_service,
    )

    _model_registry = get_model_registry_service()
    _ab_testing = get_ab_testing_service()
    _automl = get_automl_service()
    _multimodal = get_multimodal_service()
except Exception as exc:  # pragma: no cover - optional dependency failures
    logger.warning("Advanced AI services unavailable: %s", exc)
    _model_registry = _ab_testing = _automl = _multimodal = None


def _require(service: Any, name: str) -> Any:
    if not service:
        raise HTTPException(status_code=503, detail=f"{name} service unavailable")
    return service


class ModelVersionPayload(BaseModel):
    version: str = Field(..., description="Semantic version identifier")
    artifact_uri: str = Field(..., description="Location of the model artifact")
    metrics: Dict[str, float] | None = Field(default=None, description="Evaluation metrics")
    metadata: Dict[str, Any] | None = Field(default=None, description="Additional metadata")
    stage: str = Field(default="staging", description="Initial stage for the version")
    created_by: Optional[str] = Field(default=None, description="Author or pipeline")

    @validator("stage")
    def validate_stage(cls, value: str) -> str:
        allowed = {"staging", "canary", "production"}
        if value not in allowed:
            raise ValueError(f"stage must be one of {allowed}")
        return value


class ModelPromotePayload(BaseModel):
    version: str
    canary_percent: Optional[int] = Field(default=None, ge=0, le=100)


class ModelTrafficPayload(BaseModel):
    canary_version: str
    canary_percent: int = Field(ge=0, le=100)


class ExperimentCreatePayload(BaseModel):
    name: str
    variants: List[str]
    primary_metric: str = Field(default="conversion_rate")
    owner: Optional[str] = None

    @validator("variants")
    def ensure_variants(cls, value: List[str]) -> List[str]:
        if len(value) < 2:
            raise ValueError("At least two variants are required")
        return value


class ExperimentEventPayload(BaseModel):
    variant: str
    event_type: str = Field(description="impression or conversion")
    value: Optional[float] = Field(default=None, description="Optional monetary value")


class ExperimentFinalizePayload(BaseModel):
    winning_variant: Optional[str] = Field(default=None)
    summary: Optional[str] = Field(default=None)


class AutoMLTrainPayload(BaseModel):
    dataset_uri: str
    problem_type: str
    target_column: str
    objective_metric: str = Field(default="accuracy")
    budget_hours: float = Field(default=1.0, ge=0.25, le=24)


class MultiModalPayload(BaseModel):
    text: Optional[str] = Field(default=None)
    image_url: Optional[str] = Field(default=None)
    audio_url: Optional[str] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("metadata", pre=True, always=True)
    def ensure_metadata(cls, value: Any) -> Dict[str, Any]:
        return value or {}


@router.get("/models", tags=["Advanced AI"])
@cache_response(ttl=600)  # Cache for 10 minutes
async def list_models() -> Dict[str, Any]:
    """List all models - cached for 10 min"""
    registry = _require(_model_registry, "Model registry")
    try:
        return await registry.list_models()
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Model listing failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to list models") from exc


@router.get("/models/{model_name}", tags=["Advanced AI"])
@cache_response(ttl=600)  # Cache for 10 minutes
async def get_model(model_name: str) -> Dict[str, Any]:
    """Get model details - cached for 10 min"""
    registry = _require(_model_registry, "Model registry")
    try:
        return await registry.get_model(model_name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found") from exc


@router.post("/models/{model_name}/versions", tags=["Advanced AI"])
async def register_model_version(model_name: str, payload: ModelVersionPayload) -> Dict[str, Any]:
    registry = _require(_model_registry, "Model registry")
    try:
        return await registry.register_version(
            model_name=model_name,
            version=payload.version,
            artifact_uri=payload.artifact_uri,
            metrics=payload.metrics,
            metadata=payload.metadata,
            stage=payload.stage,
            created_by=payload.created_by,
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Model version registration failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to register version") from exc


@router.post("/models/{model_name}/promote", tags=["Advanced AI"])
async def promote_model(model_name: str, payload: ModelPromotePayload) -> Dict[str, Any]:
    registry = _require(_model_registry, "Model registry")
    try:
        return await registry.promote_version(model_name, payload.version, payload.canary_percent)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Model version '{payload.version}' not found") from exc


@router.post("/models/{model_name}/traffic", tags=["Advanced AI"])
async def update_canary_split(model_name: str, payload: ModelTrafficPayload) -> Dict[str, Any]:
    registry = _require(_model_registry, "Model registry")
    try:
        return await registry.update_canary_split(model_name, payload.canary_version, payload.canary_percent)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Model version '{payload.canary_version}' not found") from exc


@router.post("/experiments", tags=["Advanced AI"])
async def create_experiment(payload: ExperimentCreatePayload) -> Dict[str, Any]:
    service = _require(_ab_testing, "A/B testing")
    try:
        return await service.create_experiment(
            name=payload.name,
            variants=payload.variants,
            primary_metric=payload.primary_metric,
            owner=payload.owner,
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Experiment creation failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to create experiment") from exc


@router.post("/experiments/{experiment_id}/events", tags=["Advanced AI"])
async def record_experiment_event(experiment_id: str, payload: ExperimentEventPayload) -> Dict[str, Any]:
    service = _require(_ab_testing, "A/B testing")
    try:
        return await service.record_event(
            experiment_id=experiment_id,
            variant=payload.variant,
            event_type=payload.event_type,
            value=payload.value,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Experiment or variant not found") from exc


@router.post("/experiments/{experiment_id}/finalize", tags=["Advanced AI"])
async def finalize_experiment(experiment_id: str, payload: ExperimentFinalizePayload) -> Dict[str, Any]:
    service = _require(_ab_testing, "A/B testing")
    try:
        return await service.finalize_experiment(
            experiment_id=experiment_id,
            winning_variant=payload.winning_variant,
            summary=payload.summary,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Experiment not found") from exc


@router.get("/experiments/{experiment_id}", tags=["Advanced AI"])
async def get_experiment(experiment_id: str) -> Dict[str, Any]:
    service = _require(_ab_testing, "A/B testing")
    try:
        return await service.get_experiment(experiment_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Experiment not found") from exc


@router.post("/automl/train", tags=["Advanced AI"])
async def start_automl_training(payload: AutoMLTrainPayload) -> Dict[str, Any]:
    service = _require(_automl, "AutoML")
    try:
        return await service.start_training(
            dataset_uri=payload.dataset_uri,
            problem_type=payload.problem_type,
            target_column=payload.target_column,
            objective_metric=payload.objective_metric,
            budget_hours=payload.budget_hours,
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("AutoML training start failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to start AutoML job") from exc


@router.get("/automl/jobs/{job_id}", tags=["Advanced AI"])
async def get_automl_job(job_id: str) -> Dict[str, Any]:
    service = _require(_automl, "AutoML")
    try:
        return await service.get_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="AutoML job not found") from exc


@router.post("/multimodal/analyze", tags=["Advanced AI"])
async def analyze_multimodal(payload: MultiModalPayload) -> Dict[str, Any]:
    orchestrator = _require(_multimodal, "Multi-modal")
    if not any([payload.text, payload.image_url, payload.audio_url]):
        raise HTTPException(status_code=400, detail="Provide at least one modality (text, image_url, audio_url)")
    try:
        return await orchestrator.analyze(
            text=payload.text,
            image_url=payload.image_url,
            audio_url=payload.audio_url,
            metadata=payload.metadata,
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Multi-modal analysis failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to process request") from exc


@router.get("/status", tags=["Advanced AI"])
async def advanced_ai_status() -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "timestamp": now,
        "model_registry": bool(_model_registry),
        "ab_testing": bool(_ab_testing),
        "automl": bool(_automl),
        "multimodal": bool(_multimodal),
    }
