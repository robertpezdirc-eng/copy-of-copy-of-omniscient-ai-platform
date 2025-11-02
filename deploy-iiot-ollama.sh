#!/bin/bash
# Quick deployment script for IIoT-Ollama integration
# Deploys all components in the correct order

set -e

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"refined-graph-471712-n9"}
REGION=${REGION:-"europe-west1"}

echo "================================================"
echo "IIoT-Ollama Integration - Quick Deploy"
echo "================================================"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo ""

# Set project
gcloud config set project ${PROJECT_ID}

# Step 1: Setup Pub/Sub infrastructure
echo "Step 1/3: Setting up Pub/Sub infrastructure..."
./setup-iiot-pubsub.sh

# Step 2: Deploy Ollama service
echo ""
echo "Step 2/3: Deploying Ollama LLM service..."
echo "⚠️  This may take 20-30 minutes due to model download"
gcloud builds submit --config=cloudbuild.ollama.yaml

# Step 3: Deploy IIoT processing service
echo ""
echo "Step 3/3: Deploying IIoT processing service..."
gcloud builds submit --config=cloudbuild.iiot-ollama.yaml

# Step 4: Setup subscription (re-run setup to create subscription with URL)
echo ""
echo "Step 4/4: Creating Pub/Sub subscription..."
./setup-iiot-pubsub.sh

echo ""
echo "================================================"
echo "Deployment Complete!"
echo "================================================"
echo ""
echo "Test the deployment:"
echo ""
echo "1. Send a test message:"
echo "   gcloud pubsub topics publish iot-data-topic --message='{\"device_id\":\"sensor-001\",\"sensor_type\":\"vibration\",\"timestamp\":\"2024-01-01T12:00:00Z\",\"measurements\":{\"vibration\":92,\"temperature\":75}}'"
echo ""
echo "2. View logs:"
echo "   gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=iiot-ollama-processor' --limit=20"
echo ""
echo "3. Check service health:"
echo "   ./test-iiot-ollama.sh"
echo ""
