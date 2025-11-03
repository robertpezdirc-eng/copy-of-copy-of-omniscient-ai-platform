"""
AI/ML Models API Routes
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List
from pydantic import BaseModel

from services.ml_models_service import AIMLModelsService, ModelType, ModelStatus

router = APIRouter(prefix="/api/v1/ml-models", tags=["AI/ML Models"])
ml_service = AIMLModelsService()


class CreateModelRequest(BaseModel):
    tenant_id: str
    model_name: str
    model_type: ModelType
    config: dict


class DeployModelRequest(BaseModel):
    environment: str = "production"
    replicas: int = 3


class CreateABTestRequest(BaseModel):
    model_id_b: str
    traffic_split: float = 0.5
    metrics_to_track: Optional[List[str]] = None


class AutoMLRequest(BaseModel):
    tenant_id: str
    dataset_url: str
    target_column: str
    task_type: ModelType
    max_trials: int = 100
    max_time_hours: int = 24


class PredictRequest(BaseModel):
    input_data: dict


@router.post("/create")
async def create_custom_model(request: CreateModelRequest):
    """Create new custom ML model"""
    try:
        model = await ml_service.create_custom_model(
            tenant_id=request.tenant_id,
            model_name=request.model_name,
            model_type=request.model_type,
            config=request.config
        )
        return model
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_id}/deploy")
async def deploy_model(model_id: str, request: DeployModelRequest):
    """Deploy trained model to production"""
    try:
        deployment = await ml_service.deploy_model(
            model_id=model_id,
            environment=request.environment,
            replicas=request.replicas
        )
        return deployment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_id}/ab-test")
async def create_ab_test(model_id: str, request: CreateABTestRequest):
    """Create A/B test between two model versions"""
    try:
        ab_test = await ml_service.create_ab_test(
            model_id_a=model_id,
            model_id_b=request.model_id_b,
            traffic_split=request.traffic_split,
            metrics_to_track=request.metrics_to_track
        )
        return ab_test
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ab-test/{test_id}/results")
async def get_ab_test_results(test_id: str):
    """Get A/B test results"""
    try:
        results = await ml_service.get_ab_test_results(test_id)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automl/train")
async def auto_ml_train(request: AutoMLRequest):
    """Auto ML - automatically find best model"""
    try:
        job = await ml_service.auto_ml_train(
            tenant_id=request.tenant_id,
            dataset_url=request.dataset_url,
            target_column=request.target_column,
            task_type=request.task_type,
            max_trials=request.max_trials,
            max_time_hours=request.max_time_hours
        )
        return job
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_id}/predict")
async def predict(model_id: str, request: PredictRequest):
    """Make prediction using deployed model"""
    try:
        prediction = await ml_service.predict(
            model_id=model_id,
            input_data=request.input_data
        )
        return prediction
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}/metrics")
async def get_model_metrics(model_id: str):
    """Get model performance metrics"""
    try:
        metrics = await ml_service.get_model_metrics(model_id)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list/{tenant_id}")
async def list_models(
    tenant_id: str,
    status: Optional[ModelStatus] = None
):
    """List all models for tenant"""
    try:
        models = await ml_service.list_models(tenant_id=tenant_id, status=status)
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{model_id}")
async def delete_model(model_id: str):
    """Delete or archive model"""
    try:
        result = await ml_service.delete_model(model_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}/export")
async def export_model(model_id: str, format: str = "onnx"):
    """Export model in specified format"""
    try:
        export = await ml_service.export_model(model_id=model_id, format=format)
        return export
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
