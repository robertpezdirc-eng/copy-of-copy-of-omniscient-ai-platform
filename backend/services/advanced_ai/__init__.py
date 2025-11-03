"""Advanced AI service singletons."""

from __future__ import annotations

from .model_registry import ModelRegistryService
from .ab_testing import ABTestingService
from .automl import AutoMLOrchestrator
from .multimodal import MultiModalOrchestrator
from .mlops_pipeline import MLOpsPipeline
from .content_generation import ContentGenerationService
from .iiot_ollama import IIoTOllamaService
from .recommendation_engine_v2 import RecommendationEngine
from .ai_insights import AIInsightsService

_model_registry: ModelRegistryService | None = None
_ab_testing: ABTestingService | None = None
_automl: AutoMLOrchestrator | None = None
_multimodal: MultiModalOrchestrator | None = None
_mlops_pipeline: MLOpsPipeline | None = None
_content_generation: ContentGenerationService | None = None
_iiot_ollama: IIoTOllamaService | None = None
_recommendation_engine: RecommendationEngine | None = None
_ai_insights: AIInsightsService | None = None


def get_model_registry_service() -> ModelRegistryService:
    """Return singleton instance of the model registry."""
    global _model_registry
    if _model_registry is None:
        _model_registry = ModelRegistryService()
    return _model_registry


def get_ab_testing_service() -> ABTestingService:
    """Return singleton instance of the A/B testing service."""
    global _ab_testing
    if _ab_testing is None:
        _ab_testing = ABTestingService()
    return _ab_testing


def get_automl_service() -> AutoMLOrchestrator:
    """Return singleton instance of the AutoML orchestrator."""
    global _automl
    if _automl is None:
        _automl = AutoMLOrchestrator()
    return _automl


def get_multimodal_service() -> MultiModalOrchestrator:
    """Return singleton instance of the multi-modal orchestrator."""
    global _multimodal
    if _multimodal is None:
        _multimodal = MultiModalOrchestrator()
    return _multimodal


def get_mlops_pipeline_service() -> MLOpsPipeline:
    """Return singleton instance of the MLOps pipeline."""
    global _mlops_pipeline
    if _mlops_pipeline is None:
        _mlops_pipeline = MLOpsPipeline()
    return _mlops_pipeline


def get_content_generation_service() -> ContentGenerationService:
    """Return singleton instance of the content generation service."""
    global _content_generation
    if _content_generation is None:
        _content_generation = ContentGenerationService()
    return _content_generation


def get_iiot_ollama_service() -> IIoTOllamaService:
    """Return singleton instance of the IIoT Ollama service."""
    global _iiot_ollama
    if _iiot_ollama is None:
        _iiot_ollama = IIoTOllamaService()
    return _iiot_ollama


def get_recommendation_engine() -> RecommendationEngine:
    """Return singleton instance of the recommendation engine."""
    global _recommendation_engine
    if _recommendation_engine is None:
        _recommendation_engine = RecommendationEngine()
    return _recommendation_engine


def get_ai_insights_service() -> AIInsightsService:
    """Return singleton instance of the AI insights service."""
    global _ai_insights
    if _ai_insights is None:
        _ai_insights = AIInsightsService()
    return _ai_insights
