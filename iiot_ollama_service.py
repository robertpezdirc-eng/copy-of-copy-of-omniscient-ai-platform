"""
IIoT Data Processing Service with Ollama Integration
Handles Pub/Sub messages from IoT devices and processes them with Ollama LLM
"""
import os
import json
import logging
import base64
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="IIoT Ollama Processing Service",
    description="Processes IIoT sensor data using Ollama LLM for analysis",
    version="1.0.0"
)

# Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))

# Google Cloud configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "refined-graph-471712-n9")
# Note: PUBSUB_OUTPUT_TOPIC can be used for publishing analysis results to another topic
# Currently analysis results are returned in the HTTP response
# PUBSUB_OUTPUT_TOPIC = os.getenv("PUBSUB_OUTPUT_TOPIC", "iot-analysis-results")


class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self, base_url: str, model: str, timeout: float = 120):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        logger.info(f"Ollama client initialized: {self.base_url} (model: {self.model})")
    
    async def generate(self, prompt: str, temperature: float = 0.7) -> Dict[str, Any]:
        """Generate response from Ollama"""
        endpoint = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Sending request to Ollama: {endpoint}")
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                data = response.json()
                
                return {
                    "response": data.get("response", ""),
                    "model": self.model,
                    "done": data.get("done", False),
                    "context": data.get("context", []),
                }
        except httpx.HTTPError as e:
            logger.error(f"Ollama HTTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if Ollama is healthy"""
        try:
            endpoint = f"{self.base_url}/api/tags"
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(endpoint)
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False


# Initialize Ollama client
ollama_client = OllamaClient(OLLAMA_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT)


def decode_pubsub_message(request_json: Dict) -> Dict[str, Any]:
    """Decode Pub/Sub message from request"""
    try:
        message = request_json.get('message', {})
        
        # Decode base64 data
        data_b64 = message.get('data', '')
        if data_b64:
            data_bytes = base64.b64decode(data_b64)
            data_str = data_bytes.decode('utf-8')
            data = json.loads(data_str)
        else:
            data = {}
        
        # Get attributes
        attributes = message.get('attributes', {})
        message_id = message.get('messageId', 'unknown')
        publish_time = message.get('publishTime', '')
        
        return {
            'message_id': message_id,
            'publish_time': publish_time,
            'data': data,
            'attributes': attributes
        }
    except Exception as e:
        logger.error(f"Error decoding Pub/Sub message: {e}")
        raise


def build_analysis_prompt(iot_data: Dict[str, Any]) -> str:
    """Build analysis prompt for Ollama based on IoT data"""
    
    # Extract sensor data
    device_id = iot_data.get('device_id', 'unknown')
    sensor_type = iot_data.get('sensor_type', 'unknown')
    measurements = iot_data.get('measurements', {})
    timestamp = iot_data.get('timestamp', '')
    
    # Build prompt
    prompt = f"""Analyze the following IIoT sensor data and identify any potential issues or anomalies:

Device ID: {device_id}
Sensor Type: {sensor_type}
Timestamp: {timestamp}

Measurements:
"""
    
    for key, value in measurements.items():
        prompt += f"- {key}: {value}\n"
    
    prompt += """
Please provide:
1. Analysis of the sensor readings
2. Identification of any anomalies or concerning patterns
3. Recommended actions if issues are detected
4. Overall health assessment (HEALTHY, WARNING, or CRITICAL)

Format your response as a structured analysis."""
    
    return prompt


async def process_iot_data(iot_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process IoT data with Ollama LLM analysis"""
    
    logger.info(f"Processing IoT data: {iot_data}")
    
    # Build analysis prompt
    prompt = build_analysis_prompt(iot_data)
    
    # Get analysis from Ollama
    try:
        ollama_response = await ollama_client.generate(prompt, temperature=0.3)
        
        analysis_result = {
            'device_id': iot_data.get('device_id'),
            'sensor_type': iot_data.get('sensor_type'),
            'timestamp': iot_data.get('timestamp'),
            'original_data': iot_data,
            'analysis': ollama_response['response'],
            'model': ollama_response['model'],
            'processed_at': datetime.utcnow().isoformat(),
        }
        
        logger.info(f"Analysis completed for device {iot_data.get('device_id')}")
        return analysis_result
        
    except Exception as e:
        logger.error(f"Error processing IoT data: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "IIoT Ollama Processing Service",
        "status": "running",
        "model": OLLAMA_MODEL,
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    ollama_healthy = await ollama_client.health_check()
    
    return {
        "status": "healthy" if ollama_healthy else "degraded",
        "ollama": {
            "url": OLLAMA_URL,
            "model": OLLAMA_MODEL,
            "healthy": ollama_healthy
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/")
async def pubsub_push(request: Request):
    """
    Handle Pub/Sub push messages
    This is the main endpoint that Pub/Sub will call
    """
    try:
        # Parse request body
        request_json = await request.json()
        logger.info(f"Received Pub/Sub message: {request_json.get('message', {}).get('messageId', 'unknown')}")
        
        # Decode Pub/Sub message
        decoded_message = decode_pubsub_message(request_json)
        iot_data = decoded_message['data']
        
        # Process IoT data with Ollama
        analysis_result = await process_iot_data(iot_data)
        
        logger.info(f"Successfully processed message {decoded_message['message_id']}")
        
        # Return success (200 OK tells Pub/Sub to acknowledge the message)
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message_id": decoded_message['message_id'],
                "result": analysis_result
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing Pub/Sub message: {e}", exc_info=True)
        # Return 500 to tell Pub/Sub to retry
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
async def analyze_iot_data(iot_data: Dict[str, Any]):
    """
    Direct endpoint for analyzing IoT data (for testing)
    """
    try:
        result = await process_iot_data(iot_data)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error in analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
