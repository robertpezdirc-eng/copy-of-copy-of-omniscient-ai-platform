#!/bin/bash
# Deployment script for IIoT Ollama infrastructure on Google Cloud
# This script sets up Pub/Sub, Cloud Run with Ollama, and event subscriptions

set -e

# Configuration - Update these values for your project
export PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
export REGION="${GCP_REGION:-europe-west1}"
export OLLAMA_MODEL="${OLLAMA_MODEL:-llama3}"
export PUBSUB_TOPIC="${PUBSUB_TOPIC:-iot-data-topic}"
export SUBSCRIPTION_NAME="${SUBSCRIPTION_NAME:-iot-to-ollama-trigger}"
export SERVICE_NAME="${SERVICE_NAME:-ollama-ai-inference}"
export SERVICE_ACCOUNT="${SERVICE_ACCOUNT:-ollama-runner@${PROJECT_ID}.iam.gserviceaccount.com}"

echo "🚀 Deploying IIoT Ollama Infrastructure"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Model: ${OLLAMA_MODEL}"

# 1. Create Pub/Sub Topic for IoT Data
echo ""
echo "📡 Creating Pub/Sub topic: ${PUBSUB_TOPIC}"
gcloud pubsub topics create ${PUBSUB_TOPIC} \
  --project=${PROJECT_ID} || echo "Topic already exists"

# 2. Build and Push Ollama Docker Image
echo ""
echo "🐳 Building Ollama Docker image..."
gcloud builds submit \
  --config=cloudbuild-ollama.yaml \
  --substitutions=_PROJECT_ID=${PROJECT_ID},_OLLAMA_MODEL=${OLLAMA_MODEL} \
  --project=${PROJECT_ID}

# 3. Deploy Ollama to Cloud Run
echo ""
echo "☁️  Deploying Ollama to Cloud Run: ${SERVICE_NAME}"
gcloud run deploy ${SERVICE_NAME} \
  --image=gcr.io/${PROJECT_ID}/ollama-llm-service:latest \
  --platform=managed \
  --region=${REGION} \
  --cpu=4 \
  --memory=8Gi \
  --timeout=300 \
  --concurrency=10 \
  --min-instances=0 \
  --max-instances=10 \
  --no-allow-unauthenticated \
  --ingress=all \
  --set-env-vars="OLLAMA_MODEL=${OLLAMA_MODEL}" \
  --project=${PROJECT_ID}

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --format='value(status.url)')

echo "✅ Service deployed at: ${SERVICE_URL}"

# 4. Create Service Account if it doesn't exist
echo ""
echo "🔐 Setting up service account..."
gcloud iam service-accounts create ollama-runner \
  --display-name="Ollama Cloud Run Service Account" \
  --project=${PROJECT_ID} || echo "Service account already exists"

# Grant necessary permissions
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/pubsub.subscriber" \
  --condition=None

gcloud run services add-iam-policy-binding ${SERVICE_NAME} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/run.invoker" \
  --region=${REGION} \
  --project=${PROJECT_ID}

# 5. Create Pub/Sub Push Subscription
echo ""
echo "📬 Creating Pub/Sub push subscription..."
gcloud pubsub subscriptions create ${SUBSCRIPTION_NAME} \
  --topic=${PUBSUB_TOPIC} \
  --push-endpoint="${SERVICE_URL}/api/v1/iiot/webhook/pubsub" \
  --push-auth-service-account=${SERVICE_ACCOUNT} \
  --ack-deadline=300 \
  --message-retention-duration=7d \
  --project=${PROJECT_ID} || echo "Subscription already exists"

echo ""
echo "✅ Deployment Complete!"
echo ""
echo "📊 Summary:"
echo "  • Pub/Sub Topic: ${PUBSUB_TOPIC}"
echo "  • Cloud Run Service: ${SERVICE_NAME}"
echo "  • Service URL: ${SERVICE_URL}"
echo "  • Subscription: ${SUBSCRIPTION_NAME}"
echo ""
echo "🧪 Test with:"
echo "  gcloud pubsub topics publish ${PUBSUB_TOPIC} \\"
echo "    --message='{\"device_id\":\"test-001\",\"data\":{\"temperature\":85,\"vibration\":90}}' \\"
echo "    --project=${PROJECT_ID}"
echo ""
echo "📝 View logs:"
echo "  gcloud run logs read ${SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID}"
