"""
Background task utilities for async processing.
Uses FastAPI BackgroundTasks for lightweight tasks and optional Celery for heavy workloads.
"""
import logging
import os
from typing import Callable, Any
from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)

# Optional Celery integration
CELERY_ENABLED = os.getenv("CELERY_ENABLED", "false").lower() == "true"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

celery_app = None

if CELERY_ENABLED:
    try:
        from celery import Celery
        celery_app = Celery(
            "omni-backend",
            broker=REDIS_URL,
            backend=REDIS_URL
        )
        celery_app.conf.update(
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='UTC',
            enable_utc=True,
            task_track_started=True,
            task_time_limit=300,  # 5 min max
            worker_prefetch_multiplier=4,
            worker_max_tasks_per_child=1000,
        )
        logger.info("✅ Celery initialized")
    except ImportError:
        logger.warning("⚠️ Celery not installed; heavy background tasks disabled")
        CELERY_ENABLED = False


def schedule_lightweight_task(
    background_tasks: BackgroundTasks,
    func: Callable,
    *args,
    **kwargs
) -> None:
    """
    Schedule a lightweight background task using FastAPI BackgroundTasks.
    Best for: logging, metrics, simple cleanup, notifications.

    Args:
        background_tasks: FastAPI BackgroundTasks instance from request
        func: Function to execute
        *args, **kwargs: Arguments to pass to func
    """
    background_tasks.add_task(func, *args, **kwargs)
    logger.debug(f"Scheduled lightweight task: {func.__name__}")


def schedule_heavy_task(task_name: str, *args, **kwargs) -> Any:
    """
    Schedule a heavy background task using Celery (if enabled).
    Best for: ML inference, data processing, batch operations, external API calls.

    Args:
        task_name: Name of Celery task to execute
        *args, **kwargs: Arguments to pass to task

    Returns:
        Celery AsyncResult if Celery enabled, None otherwise
    """
    if not CELERY_ENABLED or not celery_app:
        logger.warning(f"Celery not enabled; skipping heavy task: {task_name}")
        return None

    try:
        result = celery_app.send_task(task_name, args=args, kwargs=kwargs)
        logger.info(f"Scheduled heavy task: {task_name} (task_id={result.id})")
        return result
    except Exception as e:
        logger.error(f"Failed to schedule heavy task {task_name}: {e}")
        return None


# Example lightweight tasks
async def log_api_call(endpoint: str, user_id: str, duration_ms: float):
    """Log API call for analytics (lightweight)."""
    logger.info(f"API call logged: {endpoint} by {user_id} ({duration_ms:.2f}ms)")
    # Could write to DB or analytics service here


async def send_notification(user_id: str, message: str):
    """Send user notification (lightweight)."""
    logger.info(f"Notification sent to {user_id}: {message}")
    # Could integrate with email/SMS service here


# Example Celery tasks (define in separate tasks.py)
if CELERY_ENABLED and celery_app:

    @celery_app.task(name="process_large_dataset")
    def process_large_dataset(dataset_id: str):
        """Process large dataset (heavy task)."""
        logger.info(f"Processing dataset: {dataset_id}")
        # Implement heavy processing logic
        return {"status": "completed", "dataset_id": dataset_id}

    @celery_app.task(name="train_ml_model")
    def train_ml_model(model_id: str, data_path: str):
        """Train ML model (heavy task)."""
        logger.info(f"Training model: {model_id} with data: {data_path}")
        # Implement training logic
        return {"status": "trained", "model_id": model_id}

    @celery_app.task(name="generate_report")
    def generate_report(report_type: str, params: dict):
        """Generate analytics report (heavy task)."""
        logger.info(f"Generating report: {report_type}")
        # Implement report generation
        return {"status": "generated", "report_type": report_type}
