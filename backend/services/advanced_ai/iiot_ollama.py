"""
IIoT (Industrial IoT) Data Integration Service with Ollama AI Analysis.

This service connects Google Cloud Pub/Sub for IoT data ingestion with Ollama
for real-time AI-powered analysis of industrial sensor data.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class IIoTOllamaService:
    """
    Service for processing Industrial IoT data with Ollama AI analysis.
    
    Integrates with:
    - Google Cloud Pub/Sub for IoT data ingestion
    - Ollama for local LLM inference
    - Cloud Run for scalable event-driven processing
    """

    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
        self.pubsub_project = os.getenv("GCP_PROJECT_ID")
        self.pubsub_topic = os.getenv("IOT_PUBSUB_TOPIC", "iot-data-topic")
        self.enabled = os.getenv("IIOT_OLLAMA_ENABLED", "false").lower() == "true"
        
        # Initialize Pub/Sub client if available
        self.pubsub_client = None
        if self.enabled and self.pubsub_project:
            try:
                from google.cloud import pubsub_v1
                self.pubsub_client = pubsub_v1.PublisherClient()
                self.topic_path = self.pubsub_client.topic_path(
                    self.pubsub_project, self.pubsub_topic
                )
                logger.info(f"✅ IIoT Pub/Sub enabled: {self.topic_path}")
            except Exception as e:
                logger.warning(f"⚠️  Pub/Sub client unavailable: {e}")
        
        # Ollama client
        self.ollama_client = None
        try:
            import httpx
            self.ollama_client = httpx.AsyncClient(
                base_url=self.ollama_url,
                timeout=60.0
            )
            logger.info(f"✅ Ollama client initialized: {self.ollama_url}")
        except Exception as e:
            logger.warning(f"⚠️  Ollama client unavailable: {e}")

    async def process_iot_event(
        self,
        device_id: str,
        sensor_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process an IoT event with Ollama AI analysis.
        
        This is typically called by a Pub/Sub push subscription when
        IoT data arrives.
        
        Args:
            device_id: ID of the IoT device
            sensor_data: Raw sensor readings (temp, vibration, pressure, etc.)
            metadata: Optional metadata (location, device type, etc.)
        
        Returns:
            Analysis results including anomaly detection and recommendations
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        metadata = metadata or {}
        
        # Build context for Ollama
        context = self._build_analysis_context(device_id, sensor_data, metadata)
        
        # Analyze with Ollama
        analysis = await self._analyze_with_ollama(context)
        
        # Build response
        result = {
            "device_id": device_id,
            "timestamp": timestamp,
            "sensor_data": sensor_data,
            "analysis": analysis,
            "metadata": metadata,
        }
        
        # Check for anomalies and trigger alerts if needed
        if analysis.get("anomaly_detected"):
            result["alert"] = {
                "severity": analysis.get("severity", "medium"),
                "message": analysis.get("alert_message"),
                "recommended_action": analysis.get("recommended_action"),
            }
        
        logger.info(f"Processed IoT event from device {device_id}")
        return result

    async def analyze_sensor_stream(
        self,
        device_id: str,
        sensor_readings: List[Dict[str, Any]],
        analysis_type: str = "anomaly_detection"
    ) -> Dict[str, Any]:
        """
        Analyze a stream of sensor readings.
        
        Args:
            device_id: Device identifier
            sensor_readings: List of sensor readings with timestamps
            analysis_type: Type of analysis (anomaly_detection, predictive, trend)
        
        Returns:
            Comprehensive analysis of the sensor stream
        """
        # Build prompt based on analysis type
        if analysis_type == "anomaly_detection":
            prompt = self._build_anomaly_prompt(device_id, sensor_readings)
        elif analysis_type == "predictive":
            prompt = self._build_predictive_prompt(device_id, sensor_readings)
        elif analysis_type == "trend":
            prompt = self._build_trend_prompt(device_id, sensor_readings)
        else:
            prompt = f"Analyze this IoT sensor data stream from device {device_id}: {sensor_readings}"
        
        # Get analysis from Ollama
        if self.ollama_client:
            try:
                response = await self.ollama_client.post(
                    "/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                    }
                )
                result = response.json()
                
                return {
                    "device_id": device_id,
                    "analysis_type": analysis_type,
                    "readings_analyzed": len(sensor_readings),
                    "ai_analysis": result.get("response", ""),
                    "model": self.ollama_model,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            except Exception as e:
                logger.error(f"Ollama analysis failed: {e}")
                return self._fallback_analysis(device_id, sensor_readings, analysis_type)
        else:
            return self._fallback_analysis(device_id, sensor_readings, analysis_type)

    async def publish_iot_event(
        self,
        device_id: str,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Publish an IoT event to Pub/Sub for processing.
        
        Args:
            device_id: Device identifier
            event_data: Event payload
        
        Returns:
            Publication result
        """
        if not self.pubsub_client:
            return {
                "status": "simulated",
                "message": "Pub/Sub not available, using simulation",
                "device_id": device_id,
            }
        
        try:
            message_data = json.dumps({
                "device_id": device_id,
                "data": event_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }).encode("utf-8")
            
            future = self.pubsub_client.publish(
                self.topic_path,
                message_data,
                device_id=device_id,
            )
            message_id = future.result()
            
            return {
                "status": "published",
                "message_id": message_id,
                "topic": self.topic_path,
                "device_id": device_id,
            }
        except Exception as e:
            logger.error(f"Failed to publish to Pub/Sub: {e}")
            return {
                "status": "error",
                "error": str(e),
                "device_id": device_id,
            }

    def _build_analysis_context(
        self,
        device_id: str,
        sensor_data: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> str:
        """Build context string for Ollama analysis."""
        context = f"Analyze sensor data from industrial IoT device {device_id}.\n\n"
        context += "Sensor Readings:\n"
        for key, value in sensor_data.items():
            context += f"- {key}: {value}\n"
        
        if metadata:
            context += "\nDevice Metadata:\n"
            for key, value in metadata.items():
                context += f"- {key}: {value}\n"
        
        context += "\nProvide analysis including:\n"
        context += "1. Are any readings abnormal or concerning?\n"
        context += "2. What is the overall device health status?\n"
        context += "3. Any recommended actions?\n"
        
        return context

    async def _analyze_with_ollama(self, prompt: str) -> Dict[str, Any]:
        """Analyze data using Ollama."""
        if not self.ollama_client:
            return self._fallback_simple_analysis()
        
        try:
            response = await self.ollama_client.post(
                "/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                }
            )
            result = response.json()
            ai_response = result.get("response", "")
            
            # Parse AI response for structured data
            return {
                "ai_analysis": ai_response,
                "anomaly_detected": "abnormal" in ai_response.lower() or "concerning" in ai_response.lower(),
                "severity": self._extract_severity(ai_response),
                "alert_message": self._extract_alert(ai_response),
                "recommended_action": self._extract_recommendation(ai_response),
                "model": self.ollama_model,
            }
        except Exception as e:
            logger.error(f"Ollama analysis error: {e}")
            return self._fallback_simple_analysis()

    def _fallback_analysis(
        self,
        device_id: str,
        sensor_readings: List[Dict[str, Any]],
        analysis_type: str
    ) -> Dict[str, Any]:
        """Fallback analysis when Ollama is unavailable."""
        return {
            "device_id": device_id,
            "analysis_type": analysis_type,
            "readings_analyzed": len(sensor_readings),
            "ai_analysis": "Analysis service unavailable. Using rule-based fallback.",
            "status": "fallback",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _fallback_simple_analysis(self) -> Dict[str, Any]:
        """Simple fallback when Ollama unavailable."""
        return {
            "ai_analysis": "AI analysis unavailable. Device readings logged.",
            "anomaly_detected": False,
            "severity": "info",
            "alert_message": None,
            "recommended_action": "Monitor device status",
            "status": "fallback",
        }

    def _build_anomaly_prompt(self, device_id: str, readings: List[Dict[str, Any]]) -> str:
        """Build prompt for anomaly detection."""
        return f"""Analyze this time-series sensor data from device {device_id} for anomalies:

{json.dumps(readings, indent=2)}

Identify any unusual patterns, outliers, or concerning trends that may indicate:
- Equipment malfunction
- Performance degradation
- Safety concerns
- Maintenance needs

Provide specific findings and severity level."""

    def _build_predictive_prompt(self, device_id: str, readings: List[Dict[str, Any]]) -> str:
        """Build prompt for predictive maintenance."""
        return f"""Analyze sensor data from device {device_id} to predict potential issues:

{json.dumps(readings, indent=2)}

Based on these readings, predict:
- Likelihood of failure in next 24-48 hours
- Components that may need maintenance
- Optimal maintenance schedule
- Early warning signs observed"""

    def _build_trend_prompt(self, device_id: str, readings: List[Dict[str, Any]]) -> str:
        """Build prompt for trend analysis."""
        return f"""Analyze trends in this sensor data from device {device_id}:

{json.dumps(readings, indent=2)}

Identify:
- Overall trends (improving, degrading, stable)
- Performance metrics
- Efficiency changes
- Recommendations for optimization"""

    def _extract_severity(self, text: str) -> str:
        """Extract severity from AI response."""
        text_lower = text.lower()
        if "critical" in text_lower or "emergency" in text_lower:
            return "critical"
        elif "high" in text_lower or "urgent" in text_lower:
            return "high"
        elif "medium" in text_lower or "moderate" in text_lower:
            return "medium"
        else:
            return "low"

    def _extract_alert(self, text: str) -> Optional[str]:
        """Extract alert message from AI response."""
        lines = text.split("\n")
        for line in lines:
            if "alert" in line.lower() or "warning" in line.lower():
                return line.strip()
        return None

    def _extract_recommendation(self, text: str) -> Optional[str]:
        """Extract recommendation from AI response."""
        lines = text.split("\n")
        for line in lines:
            if "recommend" in line.lower() or "action" in line.lower():
                return line.strip()
        return None


# Singleton instance
_iiot_ollama_service: Optional[IIoTOllamaService] = None


def get_iiot_ollama_service() -> IIoTOllamaService:
    """Get singleton instance of IIoT Ollama service."""
    global _iiot_ollama_service
    if _iiot_ollama_service is None:
        _iiot_ollama_service = IIoTOllamaService()
    return _iiot_ollama_service
