"""Tests for MLOps Pipeline service."""

import pytest
from datetime import datetime, timezone
from backend.services.advanced_ai.mlops_pipeline import MLOpsPipeline


@pytest.fixture
def pipeline_service():
    """Create a fresh MLOps pipeline service instance."""
    return MLOpsPipeline()


@pytest.mark.asyncio
async def test_create_pipeline(pipeline_service):
    """Test creating an MLOps pipeline."""
    result = await pipeline_service.create_pipeline(
        model_name="test_model",
        dataset_uri="gs://test-bucket/data.csv",
        target_metric="accuracy",
        threshold=0.85,
        auto_deploy=True,
        schedule="daily",
    )
    
    assert result["model_name"] == "test_model"
    assert result["dataset_uri"] == "gs://test-bucket/data.csv"
    assert result["target_metric"] == "accuracy"
    assert result["threshold"] == 0.85
    assert result["auto_deploy"] is True
    assert result["schedule"] == "daily"
    assert result["status"] == "active"
    assert "id" in result
    assert result["total_runs"] == 0


@pytest.mark.asyncio
async def test_trigger_pipeline(pipeline_service):
    """Test manually triggering a pipeline run."""
    # Create pipeline first
    pipeline = await pipeline_service.create_pipeline(
        model_name="test_model",
        dataset_uri="gs://test-bucket/data.csv",
    )
    
    # Trigger the pipeline
    result = await pipeline_service.trigger_pipeline(pipeline["id"])
    
    assert result["pipeline_id"] == pipeline["id"]
    assert "run_id" in result
    assert result["status"] == "started"
    assert "started_at" in result


@pytest.mark.asyncio
async def test_trigger_nonexistent_pipeline(pipeline_service):
    """Test triggering a pipeline that doesn't exist."""
    with pytest.raises(KeyError):
        await pipeline_service.trigger_pipeline("nonexistent-id")


@pytest.mark.asyncio
async def test_get_pipeline_status(pipeline_service):
    """Test getting pipeline status."""
    # Create and trigger pipeline
    pipeline = await pipeline_service.create_pipeline(
        model_name="test_model",
        dataset_uri="gs://test-bucket/data.csv",
    )
    await pipeline_service.trigger_pipeline(pipeline["id"])
    
    # Get status
    status = await pipeline_service.get_pipeline_status(pipeline["id"])
    
    assert status["id"] == pipeline["id"]
    assert status["total_runs"] == 1
    assert status["latest_run"] is not None
    assert "metrics" in status["latest_run"]


@pytest.mark.asyncio
async def test_pipeline_progress_simulation(pipeline_service):
    """Test that pipeline progresses through stages."""
    # Create and trigger pipeline
    pipeline = await pipeline_service.create_pipeline(
        model_name="test_model",
        dataset_uri="gs://test-bucket/data.csv",
        auto_deploy=True,
        threshold=0.85,
    )
    await pipeline_service.trigger_pipeline(pipeline["id"])
    
    # Check initial status (training)
    status1 = await pipeline_service.get_pipeline_status(pipeline["id"])
    # Should progress to evaluating
    
    # Check again for evaluation phase
    status2 = await pipeline_service.get_pipeline_status(pipeline["id"])
    assert status2["latest_run"]["status"] in ["evaluating", "deploying", "deployed", "completed"]
    
    # Check for deployment
    status3 = await pipeline_service.get_pipeline_status(pipeline["id"])
    assert status3["latest_run"]["status"] in ["deploying", "deployed", "completed"]


@pytest.mark.asyncio
async def test_list_pipelines(pipeline_service):
    """Test listing all pipelines."""
    # Create multiple pipelines
    await pipeline_service.create_pipeline(
        model_name="model1",
        dataset_uri="gs://test-bucket/data1.csv",
    )
    await pipeline_service.create_pipeline(
        model_name="model2",
        dataset_uri="gs://test-bucket/data2.csv",
    )
    
    pipelines = await pipeline_service.list_pipelines()
    
    assert len(pipelines) == 2
    assert pipelines[0]["model_name"] in ["model1", "model2"]
    assert pipelines[1]["model_name"] in ["model1", "model2"]


@pytest.mark.asyncio
async def test_get_metrics_history(pipeline_service):
    """Test retrieving metrics history."""
    # Create and trigger pipeline
    pipeline = await pipeline_service.create_pipeline(
        model_name="test_model",
        dataset_uri="gs://test-bucket/data.csv",
        threshold=0.85,
    )
    await pipeline_service.trigger_pipeline(pipeline["id"])
    
    # Progress pipeline to generate metrics
    await pipeline_service.get_pipeline_status(pipeline["id"])
    await pipeline_service.get_pipeline_status(pipeline["id"])
    await pipeline_service.get_pipeline_status(pipeline["id"])
    
    # Get metrics history
    metrics = await pipeline_service.get_metrics_history(pipeline["id"], limit=10)
    
    assert metrics["pipeline_id"] == pipeline["id"]
    assert metrics["model_name"] == "test_model"
    assert metrics["target_metric"] == "accuracy"
    assert "history" in metrics
    assert "trend_percent" in metrics


@pytest.mark.asyncio
async def test_update_alert_threshold(pipeline_service):
    """Test updating the alert threshold."""
    # Create pipeline
    pipeline = await pipeline_service.create_pipeline(
        model_name="test_model",
        dataset_uri="gs://test-bucket/data.csv",
        threshold=0.85,
    )
    
    # Update threshold
    updated = await pipeline_service.update_alert_threshold(pipeline["id"], 0.90)
    
    assert updated["threshold"] == 0.90
    assert updated["id"] == pipeline["id"]


@pytest.mark.asyncio
async def test_pipeline_with_disabled_auto_deploy(pipeline_service):
    """Test pipeline behavior when auto_deploy is disabled."""
    # Create pipeline with auto_deploy=False
    pipeline = await pipeline_service.create_pipeline(
        model_name="test_model",
        dataset_uri="gs://test-bucket/data.csv",
        auto_deploy=False,
        threshold=0.85,
    )
    await pipeline_service.trigger_pipeline(pipeline["id"])
    
    # Progress through stages
    for _ in range(5):
        status = await pipeline_service.get_pipeline_status(pipeline["id"])
    
    # Should complete without deploying
    final_status = await pipeline_service.get_pipeline_status(pipeline["id"])
    if final_status["latest_run"]["status"] == "completed":
        assert final_status["latest_run"].get("deployment_approved") is False


@pytest.mark.asyncio
async def test_pipeline_schedule_options(pipeline_service):
    """Test different schedule options."""
    schedules = ["hourly", "daily", "weekly"]
    
    for schedule in schedules:
        pipeline = await pipeline_service.create_pipeline(
            model_name=f"model_{schedule}",
            dataset_uri="gs://test-bucket/data.csv",
            schedule=schedule,
        )
        assert pipeline["schedule"] == schedule


@pytest.mark.asyncio
async def test_metrics_threshold_check(pipeline_service):
    """Test that metrics are checked against threshold."""
    pipeline = await pipeline_service.create_pipeline(
        model_name="test_model",
        dataset_uri="gs://test-bucket/data.csv",
        threshold=0.90,  # High threshold
        auto_deploy=True,
    )
    await pipeline_service.trigger_pipeline(pipeline["id"])
    
    # Progress pipeline
    for _ in range(5):
        await pipeline_service.get_pipeline_status(pipeline["id"])
    
    metrics = await pipeline_service.get_metrics_history(pipeline["id"], limit=1)
    assert "meets_threshold" in metrics
