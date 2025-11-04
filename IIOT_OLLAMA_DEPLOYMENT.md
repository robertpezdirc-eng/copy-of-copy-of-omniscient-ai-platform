# IIoT Integration with Ollama AI - Deployment Guide

## 🎯 Overview

This guide describes the Industrial IoT (IIoT) integration with Ollama AI for real-time sensor data analysis using Google Cloud infrastructure.

### Architecture

```
IoT Devices → Pub/Sub Topic → Push Subscription → Cloud Run (Ollama) → Analysis Results
```

**Components:**
1. **Google Cloud Pub/Sub**: Scalable IoT data ingestion
2. **Cloud Run with Ollama**: AI-powered analysis service
3. **Event-Driven Processing**: Automatic triggering on data arrival

---

## 🚀 Quick Start

### Prerequisites

- Google Cloud Project with billing enabled
- gcloud CLI installed and configured
- Docker installed locally (for testing)
- Appropriate IAM permissions

### 1. Set Environment Variables

```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="europe-west1"
export OLLAMA_MODEL="llama3"
```

### 2. Deploy Infrastructure

Run the automated deployment script:

```bash
chmod +x scripts/deploy-iiot-ollama.sh
./scripts/deploy-iiot-ollama.sh
```

This script will:
- Create Pub/Sub topic for IoT data
- Build and push Ollama Docker image
- Deploy Ollama to Cloud Run
- Set up service account and permissions
- Create Pub/Sub push subscription

### 3. Verify Deployment

```bash
# Check Cloud Run service
gcloud run services describe ollama-ai-inference \
  --region=europe-west1 \
  --format='value(status.url)'

# Test the health endpoint
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  https://your-service-url/api/v1/iiot/health
```

---

## 📡 Pub/Sub Configuration

### Creating the Topic

```bash
gcloud pubsub topics create iot-data-topic \
  --project=${GCP_PROJECT_ID}
```

### Creating Push Subscription

The subscription automatically triggers Cloud Run when IoT data arrives:

```bash
SERVICE_URL=$(gcloud run services describe ollama-ai-inference \
  --region=${GCP_REGION} \
  --format='value(status.url)')

gcloud pubsub subscriptions create iot-to-ollama-trigger \
  --topic=iot-data-topic \
  --push-endpoint="${SERVICE_URL}/api/v1/iiot/webhook/pubsub" \
  --push-auth-service-account=ollama-runner@${GCP_PROJECT_ID}.iam.gserviceaccount.com \
  --ack-deadline=300 \
  --message-retention-duration=7d
```

---

## 🐳 Ollama Docker Configuration

### Dockerfile.ollama

The provided `Dockerfile.ollama` creates an optimized container:

```dockerfile
FROM ollama/ollama:latest
ENV OLLAMA_MODELS=llama3
RUN ollama pull ${OLLAMA_MODELS}
EXPOSE 11434
CMD ["ollama", "serve"]
```

### Building Locally

```bash
docker build -f Dockerfile.ollama -t ollama-llm-service .
docker run -p 11434:11434 ollama-llm-service
```

### Building with Cloud Build

```bash
gcloud builds submit \
  --config=cloudbuild-ollama.yaml \
  --substitutions=_PROJECT_ID=${GCP_PROJECT_ID},_OLLAMA_MODEL=llama3
```

---

## ☁️ Cloud Run Deployment

### Deployment Command

```bash
gcloud run deploy ollama-ai-inference \
  --image=gcr.io/${GCP_PROJECT_ID}/ollama-llm-service:latest \
  --platform=managed \
  --region=europe-west1 \
  --cpu=4 \
  --memory=8Gi \
  --timeout=300 \
  --concurrency=10 \
  --min-instances=0 \
  --max-instances=10 \
  --no-allow-unauthenticated \
  --set-env-vars="OLLAMA_MODEL=llama3,IIOT_OLLAMA_ENABLED=true"
```

### Configuration Options

| Parameter | Value | Description |
|-----------|-------|-------------|
| `--cpu` | 4 | CPU allocation (2-8 recommended) |
| `--memory` | 8Gi | Memory allocation (4-16Gi) |
| `--timeout` | 300 | Max request timeout (seconds) |
| `--concurrency` | 10 | Concurrent requests per instance |
| `--min-instances` | 0 | Minimum instances (0 for cost savings) |
| `--max-instances` | 10 | Maximum auto-scaling limit |

### GPU Support (Optional)

For larger models, add GPU acceleration:

```bash
--accelerator type=NVIDIA_TESLA_T4,count=1
```

---

## 🔐 Security & Permissions

### Service Account Creation

```bash
gcloud iam service-accounts create ollama-runner \
  --display-name="Ollama Cloud Run Service Account" \
  --project=${GCP_PROJECT_ID}
```

### Required Permissions

```bash
# Pub/Sub subscriber
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:ollama-runner@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/pubsub.subscriber"

# Cloud Run invoker
gcloud run services add-iam-policy-binding ollama-ai-inference \
  --member="serviceAccount:ollama-runner@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --region=${GCP_REGION}
```

---

## 📊 API Endpoints

### 1. Process IoT Event

**POST** `/api/v1/iiot/events/analyze`

```bash
curl -X POST https://your-api-url/api/v1/iiot/events/analyze \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

**Response:**
```json
{
  "device_id": "machine-a-001",
  "timestamp": "2025-11-03T21:00:00Z",
  "sensor_data": {...},
  "analysis": {
    "ai_analysis": "Temperature and vibration are elevated...",
    "anomaly_detected": true,
    "severity": "medium",
    "recommended_action": "Schedule maintenance check"
  },
  "alert": {
    "severity": "medium",
    "message": "Vibration levels concerning",
    "recommended_action": "Schedule maintenance check"
  }
}
```

### 2. Analyze Sensor Stream

**POST** `/api/v1/iiot/streams/analyze`

```bash
curl -X POST https://your-api-url/api/v1/iiot/streams/analyze \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

**Analysis Types:**
- `anomaly_detection` - Detect unusual patterns
- `predictive` - Predict failures and maintenance needs
- `trend` - Analyze performance trends

### 3. Publish to Pub/Sub

**POST** `/api/v1/iiot/events/publish`

```bash
curl -X POST https://your-api-url/api/v1/iiot/events/publish \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "sensor-xyz-123",
    "event_data": {
      "temperature": 95.3,
      "humidity": 65,
      "alert": "high_temperature"
    }
  }'
```

### 4. Pub/Sub Webhook

**POST** `/api/v1/iiot/webhook/pubsub`

This endpoint is automatically called by Pub/Sub push subscription. No manual calls needed.

### 5. Service Status

**GET** `/api/v1/iiot/status`

```bash
curl https://your-api-url/api/v1/iiot/status \
  -H "Authorization: ******"
```

---

## 🧪 Testing

### Publish Test Message

```bash
gcloud pubsub topics publish iot-data-topic \
  --message='{"device_id":"test-001","data":{"temperature":85,"vibration":90,"pressure":110},"metadata":{"location":"test-lab"}}' \
  --project=${GCP_PROJECT_ID}
```

### View Logs

```bash
# Cloud Run logs
gcloud run logs read ollama-ai-inference \
  --region=${GCP_REGION} \
  --limit=50

# Pub/Sub subscription status
gcloud pubsub subscriptions describe iot-to-ollama-trigger \
  --format=json
```

---

## 📈 Monitoring

### Key Metrics

Monitor these metrics in Cloud Console:

- **Cloud Run**:
  - Request latency (target: <5s for analysis)
  - Container CPU utilization
  - Container memory utilization
  - Request count
  - Error rate

- **Pub/Sub**:
  - Undelivered messages
  - Oldest unacked message age
  - Push request latency

### Alerting Policies

Create alerts for:
- High error rate (>5%)
- Slow request latency (>10s)
- Undelivered messages (>100)

---

## 💰 Cost Optimization

### Recommendations

1. **Minimum Instances**: Set to 0 for development, 1+ for production
2. **Concurrency**: Increase to 20-50 if model can handle it
3. **CPU/Memory**: Start with 4 CPU / 8Gi, adjust based on load
4. **Message Retention**: 7 days is sufficient for most cases
5. **Model Selection**: Use smaller models (gemma:2b) for cost savings

### Estimated Costs (Monthly)

Based on 1M requests/month:

- Cloud Run: ~$50-100 (depends on request duration)
- Pub/Sub: ~$40 (per million messages)
- Container Registry: ~$5
- **Total**: ~$95-145/month

---

## 🔧 Troubleshooting

### Issue: Cloud Run cold starts

**Solution**: Set `--min-instances=1` or use warm-up requests

### Issue: Ollama model not loaded

**Solution**: Check model is pulled in Dockerfile:
```bash
docker run ollama-llm-service ollama list
```

### Issue: Pub/Sub messages not being processed

**Solution**: Check subscription status and service account permissions:
```bash
gcloud pubsub subscriptions describe iot-to-ollama-trigger
```

### Issue: High latency on analysis

**Solution**: 
- Increase CPU/memory allocation
- Consider using GPU
- Use smaller/faster model

---

## 🌍 Environment Variables

Configure these in Cloud Run:

```bash
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3
GCP_PROJECT_ID=your-project-id
IOT_PUBSUB_TOPIC=iot-data-topic
IIOT_OLLAMA_ENABLED=true
```

---

## 📚 Additional Resources

- [Google Cloud Pub/Sub Documentation](https://cloud.google.com/pubsub/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Ollama Documentation](https://ollama.ai/docs)
- [Industrial IoT Best Practices](https://cloud.google.com/solutions/iot)

---

## 🆘 Support

For issues or questions:
1. Check Cloud Run logs
2. Verify Pub/Sub subscription status
3. Test Ollama endpoint directly
4. Review this documentation

---

## 📝 Changelog

### Version 1.0.0 (2025-11-03)

- ✨ Initial IIoT Ollama integration
- ✨ Google Cloud Pub/Sub support
- ✨ Cloud Run deployment automation
- ✨ Three analysis types (anomaly, predictive, trend)
- ✨ Webhook for push subscriptions
- 📝 Complete deployment documentation
