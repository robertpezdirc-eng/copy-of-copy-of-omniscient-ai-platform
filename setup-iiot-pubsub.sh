#!/bin/bash
# Setup script for IIoT Pub/Sub Infrastructure
# Creates Pub/Sub topics, subscriptions, and service accounts

set -e

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"refined-graph-471712-n9"}
REGION=${REGION:-"europe-west1"}

# Pub/Sub topics
IOT_DATA_TOPIC="iot-data-topic"
IOT_ANALYSIS_RESULTS_TOPIC="iot-analysis-results"

# Service account
SERVICE_ACCOUNT_NAME="ollama-runner"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Cloud Run service
IIOT_SERVICE_NAME="iiot-ollama-processor"

echo "================================================"
echo "IIoT Pub/Sub Infrastructure Setup"
echo "================================================"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo ""

# Set the project
echo "Setting project..."
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable pubsub.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Create Pub/Sub topics
echo ""
echo "Creating Pub/Sub topics..."

# IoT data topic (input)
if gcloud pubsub topics describe ${IOT_DATA_TOPIC} &>/dev/null; then
    echo "✓ Topic ${IOT_DATA_TOPIC} already exists"
else
    gcloud pubsub topics create ${IOT_DATA_TOPIC}
    echo "✓ Created topic: ${IOT_DATA_TOPIC}"
fi

# Analysis results topic (output)
if gcloud pubsub topics describe ${IOT_ANALYSIS_RESULTS_TOPIC} &>/dev/null; then
    echo "✓ Topic ${IOT_ANALYSIS_RESULTS_TOPIC} already exists"
else
    gcloud pubsub topics create ${IOT_ANALYSIS_RESULTS_TOPIC}
    echo "✓ Created topic: ${IOT_ANALYSIS_RESULTS_TOPIC}"
fi

# Create service account
echo ""
echo "Setting up service account..."
if gcloud iam service-accounts describe ${SERVICE_ACCOUNT_EMAIL} &>/dev/null; then
    echo "✓ Service account ${SERVICE_ACCOUNT_EMAIL} already exists"
else
    gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} \
        --display-name="Ollama Runner Service Account" \
        --description="Service account for running Ollama Cloud Run service"
    echo "✓ Created service account: ${SERVICE_ACCOUNT_EMAIL}"
fi

# Grant necessary IAM roles
echo ""
echo "Granting IAM roles..."

# Allow service account to invoke Cloud Run
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/run.invoker" \
    --condition=None \
    || echo "Note: IAM binding may already exist"

# Allow service account to publish to Pub/Sub
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/pubsub.publisher" \
    --condition=None \
    || echo "Note: IAM binding may already exist"

# Allow service account to subscribe to Pub/Sub
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/pubsub.subscriber" \
    --condition=None \
    || echo "Note: IAM binding may already exist"

echo "✓ IAM roles configured"

# Get Cloud Run service URL (if deployed)
echo ""
echo "Checking for deployed Cloud Run service..."
if gcloud run services describe ${IIOT_SERVICE_NAME} --region=${REGION} &>/dev/null; then
    SERVICE_URL=$(gcloud run services describe ${IIOT_SERVICE_NAME} \
        --region=${REGION} \
        --format='value(status.url)')
    echo "✓ Cloud Run service URL: ${SERVICE_URL}"
    
    # Create or update Pub/Sub push subscription
    echo ""
    echo "Setting up Pub/Sub push subscription..."
    SUBSCRIPTION_NAME="iot-to-ollama-trigger"
    
    if gcloud pubsub subscriptions describe ${SUBSCRIPTION_NAME} &>/dev/null; then
        echo "Updating existing subscription..."
        gcloud pubsub subscriptions update ${SUBSCRIPTION_NAME} \
            --push-endpoint="${SERVICE_URL}/" \
            --push-auth-service-account="${SERVICE_ACCOUNT_EMAIL}"
        echo "✓ Updated subscription: ${SUBSCRIPTION_NAME}"
    else
        echo "Creating new subscription..."
        gcloud pubsub subscriptions create ${SUBSCRIPTION_NAME} \
            --topic=${IOT_DATA_TOPIC} \
            --push-endpoint="${SERVICE_URL}/" \
            --push-auth-service-account="${SERVICE_ACCOUNT_EMAIL}" \
            --ack-deadline=600 \
            --message-retention-duration=7d
        echo "✓ Created subscription: ${SUBSCRIPTION_NAME}"
    fi
else
    echo "⚠ Cloud Run service not deployed yet"
    echo "After deploying the service, run this script again to create the push subscription"
    echo ""
    echo "To create subscription manually after deployment:"
    echo "  export SERVICE_URL=\$(gcloud run services describe ${IIOT_SERVICE_NAME} --region=${REGION} --format='value(status.url)')"
    echo "  gcloud pubsub subscriptions create iot-to-ollama-trigger \\"
    echo "    --topic=${IOT_DATA_TOPIC} \\"
    echo "    --push-endpoint=\"\${SERVICE_URL}/\" \\"
    echo "    --push-auth-service-account=${SERVICE_ACCOUNT_EMAIL} \\"
    echo "    --ack-deadline=600 \\"
    echo "    --message-retention-duration=7d"
fi

echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Deploy Ollama service:"
echo "   gcloud builds submit --config=cloudbuild.ollama.yaml"
echo ""
echo "2. Deploy IIoT processing service:"
echo "   gcloud builds submit --config=cloudbuild.iiot-ollama.yaml"
echo ""
echo "3. Test by publishing a message:"
echo "   gcloud pubsub topics publish ${IOT_DATA_TOPIC} --message='{\"device_id\":\"sensor-001\",\"sensor_type\":\"vibration\",\"timestamp\":\"2024-01-01T12:00:00Z\",\"measurements\":{\"vibration\":92,\"temperature\":75}}'"
echo ""
