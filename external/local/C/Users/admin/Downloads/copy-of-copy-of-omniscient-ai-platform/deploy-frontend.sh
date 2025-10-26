#!/bin/bash

# Omni Platform Frontend Deployment Script
# This script deploys the web frontend to Google Cloud Run

set -e

PROJECT_ID="refined-graph-471712-n9"
REGION="europe-west1"
SERVICE_NAME="omni-frontend"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying Omni Platform Frontend to Google Cloud Run"
echo "======================================================"

# Check if gcloud is configured
if ! gcloud config get-value project >/dev/null 2>&1; then
    echo "❌ gcloud is not configured. Please run: gcloud auth login"
    exit 1
fi

# Set project
echo "📋 Setting project to: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Enable required services
echo "🔧 Enabling required Google Cloud services..."
gcloud services enable run.googleapis.com \
                      cloudbuild.googleapis.com \
                      containerregistry.googleapis.com \
                      >/dev/null 2>&1

# Build and push container image
TIMESTAMP=$(date +%Y%m%d%H%M%S)
IMAGE_TAG="${IMAGE_NAME}:${TIMESTAMP}"

echo "🏗️ Building container image: $IMAGE_TAG"
gcloud builds submit --tag $IMAGE_TAG .

if [ $? -ne 0 ]; then
    echo "❌ Container build failed"
    exit 1
fi

echo "✅ Container image built and pushed: $IMAGE_TAG"

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_TAG \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 3 \
    --timeout 300 \
    --set-env-vars OMNI_API_BASE=https://omni-dashboard-661612368188.europe-west1.run.app

if [ $? -ne 0 ]; then
    echo "❌ Cloud Run deployment failed"
    exit 1
fi

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo ""
echo "🎉 Frontend Deployment Successful!"
echo "=================================="
echo "🌐 Frontend URL: $SERVICE_URL"
echo "🔗 Backend API: https://omni-dashboard-661612368188.europe-west1.run.app"
echo "🤖 Gemini Model: gemini-2.0-flash"
echo "📍 Region: $REGION"
echo ""
echo "🔧 Features Available:"
echo "  ✅ Interactive AI Chat Interface"
echo "  ✅ API Testing Tools"
echo "  ✅ System Health Monitoring"
echo "  ✅ Real-time Status Updates"
echo "  ✅ Responsive Design"
echo ""
echo "🌟 Access your Omni Platform at: $SERVICE_URL"