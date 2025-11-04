"""Advanced AI platform routes: model registry, A/B testing, AutoML, multi-modal."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

router = APIRouter()

try:
    from services.advanced_ai import (
        get_model_registry_service,
        get_ab_testing_service,
        get_automl_service,
        get_multimodal_service,
        get_mlops_pipeline_service,
        get_content_generation_service,
    )

    _model_registry = get_model_registry_service()
    _ab_testing = get_ab_testing_service()
    _automl = get_automl_service()
    _multimodal = get_multimodal_service()
    _mlops_pipeline = get_mlops_pipeline_service()
    _content_generation = get_content_generation_service()
except Exception as exc:  # pragma: no cover - optional dependency failures
    logger.warning("Advanced AI services unavailable: %s", exc)
    _model_registry = None
    _ab_testing = None
    _automl = None
    _multimodal = None
    _mlops_pipeline = None
    _content_generation = None


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
async def list_models() -> Dict[str, Any]:
    registry = _require(_model_registry, "Model registry")
    try:
        return await registry.list_models()
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Model listing failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to list models") from exc


@router.get("/models/{model_name}", tags=["Advanced AI"])
async def get_model(model_name: str) -> Dict[str, Any]:
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


@router.post("/multimodal/analyze", tags=["Advanced AI", "Multimodal"])
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


class ImageGenerationPayload(BaseModel):
    prompt: str = Field(..., description="Text prompt for image generation")
    size: str = Field(default="1024x1024", description="Image size")
    quality: str = Field(default="standard", description="Image quality")


@router.post("/multimodal/generate-image", tags=["Advanced AI", "Multimodal"])
async def generate_image(payload: ImageGenerationPayload) -> Dict[str, Any]:
    """Generate images using DALL-E."""
    orchestrator = _require(_multimodal, "Multi-modal")
    try:
        return await orchestrator.generate_image(
            prompt=payload.prompt,
            size=payload.size,
            quality=payload.quality,
        )
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Image generation failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to generate image") from exc


class TextToSpeechPayload(BaseModel):
    text: str = Field(..., description="Text to convert to speech")
    voice: str = Field(default="alloy", description="Voice to use")
    model: str = Field(default="tts-1", description="TTS model")


@router.post("/multimodal/text-to-speech", tags=["Advanced AI", "Multimodal"])
async def text_to_speech(payload: TextToSpeechPayload) -> Dict[str, Any]:
    """Convert text to speech using OpenAI TTS."""
    orchestrator = _require(_multimodal, "Multi-modal")
    try:
        return await orchestrator.text_to_speech(
            text=payload.text,
            voice=payload.voice,
            model=payload.model,
        )
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Text-to-speech failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to convert text to speech") from exc


@router.get("/status", tags=["Advanced AI"])
async def advanced_ai_status() -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "timestamp": now,
        "model_registry": bool(_model_registry),
        "ab_testing": bool(_ab_testing),
        "automl": bool(_automl),
        "multimodal": bool(_multimodal),
        "mlops_pipeline": bool(_mlops_pipeline),
        "content_generation": bool(_content_generation),
    }


# MLOps Pipeline Routes


class MLOpsPipelinePayload(BaseModel):
    model_name: str = Field(..., description="Name of the model")
    dataset_uri: str = Field(..., description="URI to the training dataset")
    target_metric: str = Field(default="accuracy", description="Target metric to optimize")
    threshold: float = Field(default=0.85, ge=0.0, le=1.0, description="Quality threshold")
    auto_deploy: bool = Field(default=True, description="Auto-deploy if threshold is met")
    schedule: Optional[str] = Field(default="daily", description="Training schedule")


@router.post("/mlops/pipelines", tags=["Advanced AI", "MLOps"])
async def create_mlops_pipeline(payload: MLOpsPipelinePayload) -> Dict[str, Any]:
    """Create an automated MLOps pipeline for continuous training and deployment."""
    service = _require(_mlops_pipeline, "MLOps Pipeline")
    try:
        return await service.create_pipeline(
            model_name=payload.model_name,
            dataset_uri=payload.dataset_uri,
            target_metric=payload.target_metric,
            threshold=payload.threshold,
            auto_deploy=payload.auto_deploy,
            schedule=payload.schedule,
        )
    except Exception as exc:
        logger.error("MLOps pipeline creation failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to create pipeline") from exc


@router.get("/mlops/pipelines", tags=["Advanced AI", "MLOps"])
async def list_mlops_pipelines() -> List[Dict[str, Any]]:
    """List all MLOps pipelines."""
    service = _require(_mlops_pipeline, "MLOps Pipeline")
    try:
        return await service.list_pipelines()
    except Exception as exc:
        logger.error("Failed to list pipelines: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to list pipelines") from exc


@router.post("/mlops/pipelines/{pipeline_id}/trigger", tags=["Advanced AI", "MLOps"])
async def trigger_mlops_pipeline(pipeline_id: str) -> Dict[str, Any]:
    """Manually trigger a pipeline run."""
    service = _require(_mlops_pipeline, "MLOps Pipeline")
    try:
        return await service.trigger_pipeline(pipeline_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Pipeline not found") from exc
    except Exception as exc:
        logger.error("Failed to trigger pipeline: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to trigger pipeline") from exc


@router.get("/mlops/pipelines/{pipeline_id}", tags=["Advanced AI", "MLOps"])
async def get_mlops_pipeline_status(pipeline_id: str) -> Dict[str, Any]:
    """Get pipeline status and latest runs."""
    service = _require(_mlops_pipeline, "MLOps Pipeline")
    try:
        return await service.get_pipeline_status(pipeline_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Pipeline not found") from exc


@router.get("/mlops/pipelines/{pipeline_id}/metrics", tags=["Advanced AI", "MLOps"])
async def get_pipeline_metrics(pipeline_id: str, limit: int = 10) -> Dict[str, Any]:
    """Get performance metrics history for monitoring."""
    service = _require(_mlops_pipeline, "MLOps Pipeline")
    try:
        return await service.get_metrics_history(pipeline_id, limit)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Pipeline not found") from exc


class ThresholdUpdatePayload(BaseModel):
    threshold: float = Field(..., ge=0.0, le=1.0, description="New threshold value")


@router.put("/mlops/pipelines/{pipeline_id}/threshold", tags=["Advanced AI", "MLOps"])
async def update_pipeline_threshold(
    pipeline_id: str, 
    payload: ThresholdUpdatePayload
) -> Dict[str, Any]:
    """Update the performance threshold for alerts."""
    service = _require(_mlops_pipeline, "MLOps Pipeline")
    try:
        return await service.update_alert_threshold(pipeline_id, payload.threshold)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Pipeline not found") from exc


# Content Generation Routes


class DocumentationPayload(BaseModel):
    code_snippet: str = Field(..., description="Code to generate documentation for")
    language: str = Field(default="python", description="Programming language")
    doc_format: str = Field(default="markdown", description="Documentation format")
    include_examples: bool = Field(default=True, description="Include usage examples")


@router.post("/content/documentation", tags=["Advanced AI", "Content Generation"])
async def generate_documentation(payload: DocumentationPayload) -> Dict[str, Any]:
    """Automatically generate documentation from code."""
    service = _require(_content_generation, "Content Generation")
    try:
        return await service.generate_documentation(
            code_snippet=payload.code_snippet,
            language=payload.language,
            doc_format=payload.doc_format,
            include_examples=payload.include_examples,
        )
    except Exception as exc:
        logger.error("Documentation generation failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to generate documentation") from exc


class TestDataPayload(BaseModel):
    schema: Dict[str, Any] = Field(..., description="Schema for test data")
    count: int = Field(default=10, ge=1, le=1000, description="Number of records")
    seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")


@router.post("/content/test-data", tags=["Advanced AI", "Content Generation"])
async def generate_test_data(payload: TestDataPayload) -> Dict[str, Any]:
    """Generate realistic test data based on schema."""
    service = _require(_content_generation, "Content Generation")
    try:
        return await service.generate_test_data(
            schema=payload.schema,
            count=payload.count,
            seed=payload.seed,
        )
    except Exception as exc:
        logger.error("Test data generation failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to generate test data") from exc


class FeatureSuggestionPayload(BaseModel):
    context: Dict[str, Any] = Field(..., description="Context for suggestions")
    max_suggestions: int = Field(default=5, ge=1, le=20, description="Maximum suggestions")


@router.post("/content/feature-suggestions", tags=["Advanced AI", "Content Generation"])
async def suggest_features(payload: FeatureSuggestionPayload) -> Dict[str, Any]:
    """Generate feature suggestions based on usage patterns and context."""
    service = _require(_content_generation, "Content Generation")
    try:
        return await service.suggest_features(
            context=payload.context,
            max_suggestions=payload.max_suggestions,
        )
    except Exception as exc:
        logger.error("Feature suggestion failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to generate suggestions") from exc


class APIExamplePayload(BaseModel):
    endpoint: str = Field(..., description="API endpoint")
    method: str = Field(default="POST", description="HTTP method")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Request parameters")


@router.post("/content/api-examples", tags=["Advanced AI", "Content Generation"])
async def generate_api_examples(payload: APIExamplePayload) -> Dict[str, Any]:
    """Generate API usage examples in multiple languages."""
    service = _require(_content_generation, "Content Generation")
    try:
        return await service.generate_api_examples(
            endpoint=payload.endpoint,
            method=payload.method,
            parameters=payload.parameters,
        )
    except Exception as exc:
        logger.error("API example generation failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to generate examples") from exc


@router.get("/content/stats", tags=["Advanced AI", "Content Generation"])
async def get_content_generation_stats() -> Dict[str, Any]:
    """Get statistics about content generation usage."""
    service = _require(_content_generation, "Content Generation")
    try:
        return await service.get_generation_stats()
    except Exception as exc:
        logger.error("Failed to get generation stats: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to get stats") from exc
