"""
IIoT (Industrial IoT) routes with Ollama AI integration.

Provides endpoints for:
- Processing IoT events with AI analysis
- Publishing events to Pub/Sub
- Analyzing sensor data streams
- Real-time anomaly detection
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# Import service
try:
    from services.advanced_ai.iiot_ollama import get_iiot_ollama_service
    _iiot_service = get_iiot_ollama_service()
except Exception as exc:
    logger.warning(f"IIoT Ollama service unavailable: {exc}")
    _iiot_service = None


def _require_service():
    """Ensure service is available."""
    if not _iiot_service:
        raise HTTPException(
            status_code=503,
            detail="IIoT Ollama service unavailable"
        )
    return _iiot_service


# Request Models

class IoTEventPayload(BaseModel):
    device_id: str = Field(..., description="Device identifier")
    sensor_data: Dict[str, Any] = Field(..., description="Sensor readings")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Device metadata")


class SensorStreamPayload(BaseModel):
    device_id: str = Field(..., description="Device identifier")
    sensor_readings: List[Dict[str, Any]] = Field(..., description="Time-series sensor data")
    analysis_type: str = Field(
        default="anomaly_detection",
        description="Analysis type: anomaly_detection, predictive, or trend"
    )


class PublishEventPayload(BaseModel):
    device_id: str = Field(..., description="Device identifier")
    event_data: Dict[str, Any] = Field(..., description="Event payload")


# Webhook endpoint for Pub/Sub push subscriptions

@router.post("/webhook/pubsub", tags=["IIoT", "Webhooks"])
async def pubsub_webhook(request: Request) -> Dict[str, Any]:
    """
    Webhook endpoint for Google Cloud Pub/Sub push subscriptions.
    
    This endpoint is called by Pub/Sub when IoT data arrives.
    Configure your Pub/Sub subscription with:
    ```bash
    gcloud pubsub subscriptions create iot-to-ollama-trigger \\
      --topic iot-data-topic \\
      --push-endpoint=https://your-domain/api/v1/iiot/webhook/pubsub \\
      --push-auth-service-account=your-sa@project.iam.gserviceaccount.com
    ```
    """
    service = _require_service()
    
    try:
        # Parse Pub/Sub message
        body = await request.json()
        
        # Extract message data
        message = body.get("message", {})
        data = message.get("data", "")
        attributes = message.get("attributes", {})
        
        # Decode base64 data
        import base64
        import json
        decoded_data = json.loads(base64.b64decode(data).decode("utf-8"))
        
        device_id = decoded_data.get("device_id") or attributes.get("device_id")
        sensor_data = decoded_data.get("data", {})
        metadata = decoded_data.get("metadata", {})
        
        # Process with Ollama AI
        result = await service.process_iot_event(device_id, sensor_data, metadata)
        
        # Return 200 to acknowledge message
        return {
            "status": "processed",
            "message_id": message.get("messageId"),
            "device_id": device_id,
            "analysis": result.get("analysis", {}),
        }
        
    except Exception as exc:
        logger.error(f"Pub/Sub webhook error: {exc}")
        # Return 200 even on error to avoid redelivery loops
        # Log the error for investigation
        return {
            "status": "error",
            "error": str(exc),
        }


# API Endpoints

@router.post("/events/analyze", tags=["IIoT", "AI Analysis"])
async def analyze_iot_event(payload: IoTEventPayload) -> Dict[str, Any]:
    """
    Analyze an IoT event with Ollama AI.
    
    Example:
    ```json
    {
      "device_id": "machine-a-001",
      "sensor_data": {
        "temperature": 85.5,
        "vibration": 92,
        "pressure": 120,
        "rpm": 1800
      },
      "metadata": {
        "location": "factory-floor-2",
        "machine_type": "cnc_mill"
      }
    }
    ```
    
    Returns AI-powered analysis including:
    - Anomaly detection
    - Health status assessment
    - Alert recommendations
    - Suggested actions
    """
    service = _require_service()
    
    try:
        result = await service.process_iot_event(
            device_id=payload.device_id,
            sensor_data=payload.sensor_data,
            metadata=payload.metadata,
        )
        return result
    except Exception as exc:
        logger.error(f"IoT event analysis failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(exc)}"
        )


@router.post("/streams/analyze", tags=["IIoT", "AI Analysis"])
async def analyze_sensor_stream(payload: SensorStreamPayload) -> Dict[str, Any]:
    """
    Analyze a time-series stream of sensor data.
    
    Supports three analysis types:
    - `anomaly_detection`: Detect unusual patterns and outliers
    - `predictive`: Predict potential failures and maintenance needs
    - `trend`: Analyze performance trends and optimization opportunities
    
    Example:
    ```json
    {
      "device_id": "pump-b-042",
      "analysis_type": "predictive",
      "sensor_readings": [
        {
          "timestamp": "2025-11-03T20:00:00Z",
          "temperature": 75.2,
          "pressure": 105
        },
        {
          "timestamp": "2025-11-03T20:05:00Z",
          "temperature": 76.8,
          "pressure": 108
        }
      ]
    }
    ```
    """
    service = _require_service()
    
    try:
        result = await service.analyze_sensor_stream(
            device_id=payload.device_id,
            sensor_readings=payload.sensor_readings,
            analysis_type=payload.analysis_type,
        )
        return result
    except Exception as exc:
        logger.error(f"Sensor stream analysis failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(exc)}"
        )


@router.post("/events/publish", tags=["IIoT", "Pub/Sub"])
async def publish_iot_event(payload: PublishEventPayload) -> Dict[str, Any]:
    """
    Publish an IoT event to Google Cloud Pub/Sub.
    
    The event will be queued for processing by Cloud Run workers
    running Ollama for AI analysis.
    
    Example:
    ```json
    {
      "device_id": "sensor-xyz-123",
      "event_data": {
        "temperature": 95.3,
        "humidity": 65,
        "alert": "high_temperature"
      }
    }
    ```
    
    Returns publication confirmation with message ID.
    """
    service = _require_service()
    
    try:
        result = await service.publish_iot_event(
            device_id=payload.device_id,
            event_data=payload.event_data,
        )
        return result
    except Exception as exc:
        logger.error(f"Event publication failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Publication failed: {str(exc)}"
        )


@router.get("/status", tags=["IIoT", "Health"])
async def iiot_service_status() -> Dict[str, Any]:
    """
    Get IIoT service status including Ollama and Pub/Sub availability.
    """
    if not _iiot_service:
        return {
            "status": "unavailable",
            "ollama": False,
            "pubsub": False,
        }
    
    return {
        "status": "operational",
        "ollama": {
            "enabled": _iiot_service.ollama_client is not None,
            "url": _iiot_service.ollama_url,
            "model": _iiot_service.ollama_model,
        },
        "pubsub": {
            "enabled": _iiot_service.pubsub_client is not None,
            "project": _iiot_service.pubsub_project,
            "topic": _iiot_service.pubsub_topic,
        },
        "iiot_enabled": _iiot_service.enabled,
    }


@router.get("/health", tags=["IIoT", "Health"])
async def iiot_health_check() -> Dict[str, Any]:
    """
    Health check endpoint for load balancers and monitoring.
    """
    service = _require_service()
    
    # Test Ollama connection
    ollama_healthy = service.ollama_client is not None
    pubsub_healthy = service.pubsub_client is not None or not service.enabled
    
    overall_health = "healthy" if (ollama_healthy or pubsub_healthy) else "degraded"
    
    return {
        "status": overall_health,
        "components": {
            "ollama": "healthy" if ollama_healthy else "unavailable",
            "pubsub": "healthy" if pubsub_healthy else "unavailable",
        },
    }
