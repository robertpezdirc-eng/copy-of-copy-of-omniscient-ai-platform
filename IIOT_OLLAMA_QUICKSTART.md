# Quick Start Guide - IIoT Ollama Integration

## Prerequisites

```bash
export PROJECT_ID="refined-graph-471712-n9"
export REGION="europe-west1"
gcloud config set project ${PROJECT_ID}
```

## Option 1: Quick Deploy (All-in-One)

```bash
./deploy-iiot-ollama.sh
```

This script will:
1. Setup Pub/Sub infrastructure
2. Deploy Ollama LLM service (⚠️ takes 20-30 minutes)
3. Deploy IIoT processing service
4. Configure push subscriptions

## Option 2: Manual Step-by-Step

### 1. Setup Infrastructure

```bash
./setup-iiot-pubsub.sh
```

### 2. Deploy Ollama Service

```bash
gcloud builds submit --config=cloudbuild.ollama.yaml
```

### 3. Deploy IIoT Processor

```bash
gcloud builds submit --config=cloudbuild.iiot-ollama.yaml
```

### 4. Create Subscription (run setup again)

```bash
./setup-iiot-pubsub.sh
```

## Testing

### Run Test Suite

```bash
./test-iiot-ollama.sh
```

### Send Test Message

```bash
gcloud pubsub topics publish iot-data-topic --message='{
  "device_id": "sensor-001",
  "sensor_type": "vibration",
  "timestamp": "2024-01-01T12:00:00Z",
  "measurements": {
    "vibration": 92,
    "temperature": 75
  }
}'
```

### Generate Realistic Test Data

```bash
# Install dependencies
pip install google-cloud-pubsub

# Generate 20 messages with 2 second intervals
python3 iot_data_generator.py \
  --project ${PROJECT_ID} \
  --count 20 \
  --interval 2 \
  --status mixed
```

### View Logs

```bash
# Tail logs in real-time
gcloud logging tail \
  "resource.type=cloud_run_revision AND resource.labels.service_name=iiot-ollama-processor"

# View recent logs
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=iiot-ollama-processor" \
  --limit=50 \
  --format=json
```

## Architecture Overview

```
IoT Devices
    ↓
Pub/Sub (iot-data-topic)
    ↓
Push Subscription
    ↓
Cloud Run: IIoT Processor → Ollama LLM
    ↓
Analysis Results
```

## Key Components

| Component | Purpose | Resources |
|-----------|---------|-----------|
| `ollama-ai-inference` | LLM inference with llama3 | 4 CPU, 8GB RAM |
| `iiot-ollama-processor` | Pub/Sub message processing | 2 CPU, 4GB RAM |
| `iot-data-topic` | IoT data ingestion | Pub/Sub topic |
| `iot-to-ollama-trigger` | Event trigger | Push subscription |

## Cost Optimization

- **Min instances**: 0 (no cost when idle)
- **Max instances**: 10 (configurable)
- **Pay-per-use**: Only charged for actual request processing time
- **Cold start**: ~5-10 seconds for IIoT processor, ~30-60 seconds for Ollama

## Monitoring

```bash
# Service status
gcloud run services describe iiot-ollama-processor --region=${REGION}
gcloud run services describe ollama-ai-inference --region=${REGION}

# Metrics in Cloud Console
# → Cloud Run → Services → Select service → Metrics
```

## Troubleshooting

### Messages not processed

```bash
# Check subscription
gcloud pubsub subscriptions describe iot-to-ollama-trigger

# Check logs for errors
gcloud logging read \
  "resource.type=cloud_run_revision AND severity>=ERROR" \
  --limit=20
```

### Ollama timeout

```bash
# Increase subscription ack deadline
gcloud pubsub subscriptions update iot-to-ollama-trigger \
  --ack-deadline=600
```

### High costs

```bash
# Reduce max instances
gcloud run services update iiot-ollama-processor \
  --region=${REGION} \
  --max-instances 5
```

## Documentation

See [IIOT_OLLAMA_INTEGRATION.md](IIOT_OLLAMA_INTEGRATION.md) for complete documentation.
