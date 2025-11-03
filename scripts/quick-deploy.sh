#!/bin/bash

# Quick Production Deployment Script
# Izvede vse deployment korake avtomatsko

set -e

echo "🚀 Omni Platform - Quick Production Deployment"
echo "==============================================="
echo ""
echo "This script will deploy all features to production:"
echo "  - Redis Cache (Cloud Memorystore)"
echo "  - Grafana Cloud Integration"
echo "  - Multi-Tenancy"
echo "  - Sentry Error Tracking"
echo "  - Updated Backend"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Configuration
PROJECT_ID="${PROJECT_ID:-refined-graph-471712-n9}"
REGION="${REGION:-europe-west1}"
SERVICE_NAME="${SERVICE_NAME:-omni-ultra-backend}"

echo ""
echo "📋 Configuration:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service: $SERVICE_NAME"
echo ""

# Step 1: Deploy Redis
echo "📦 Step 1/5: Deploying Redis..."
echo "--------------------------------"

if gcloud redis instances describe omni-cache --region=$REGION --project=$PROJECT_ID &>/dev/null; then
    echo "✓ Redis instance already exists"
else
    echo "Creating Redis instance (this may take 5-10 minutes)..."
    gcloud redis instances create omni-cache \
        --size=1 \
        --region=$REGION \
        --tier=basic \
        --redis-version=redis_6_x \
        --project=$PROJECT_ID
    echo "✓ Redis instance created"
fi

# Get Redis connection info
REDIS_INFO=$(gcloud redis instances describe omni-cache \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(host,port)")
REDIS_HOST=$(echo $REDIS_INFO | awk '{print $1}')
REDIS_PORT=$(echo $REDIS_INFO | awk '{print $2}')

echo "✓ Redis connection: $REDIS_HOST:$REDIS_PORT"

# Step 2: Setup Grafana Cloud
echo ""
echo "📊 Step 2/5: Setting up Grafana Cloud..."
echo "-----------------------------------------"
echo ""
echo "Please complete Grafana Cloud setup manually:"
echo "1. Visit: https://grafana.com/auth/sign-up"
echo "2. Create free account"
echo "3. Get Prometheus Remote Write URL and API Key"
echo "4. Run: cd grafana/ && ./setup-grafana-cloud.sh"
echo "5. Run: docker-compose up -d"
echo ""
read -p "Press Enter when Grafana Cloud setup is complete..."

# Step 3: Configure Sentry
echo ""
echo "🐛 Step 3/5: Configuring Sentry..."
echo "-----------------------------------"
echo ""
echo "Please configure Sentry:"
echo "1. Visit: https://sentry.io/signup/"
echo "2. Create project and get DSN"
echo ""
read -p "Enter Sentry DSN (or press Enter to skip): " SENTRY_DSN

# Step 4: Update environment variables
echo ""
echo "🔧 Step 4/5: Updating environment variables..."
echo "-----------------------------------------------"

ENV_VARS="REDIS_HOST=$REDIS_HOST,REDIS_PORT=$REDIS_PORT,ENABLE_MULTI_TENANCY=true"

if [ -n "$SENTRY_DSN" ]; then
    ENV_VARS="$ENV_VARS,SENTRY_DSN=$SENTRY_DSN,SENTRY_ENVIRONMENT=production,SENTRY_TRACES_SAMPLE_RATE=0.1"
fi

echo "Updating Cloud Run service with new environment variables..."
gcloud run services update $SERVICE_NAME \
    --set-env-vars "$ENV_VARS" \
    --region=$REGION \
    --project=$PROJECT_ID

echo "✓ Environment variables updated"

# Step 5: Deploy latest code
echo ""
echo "🚀 Step 5/5: Deploying latest code..."
echo "--------------------------------------"

echo "Building and deploying backend..."
gcloud builds submit \
    --config=cloudbuild-backend.yaml \
    --substitutions=_PROJECT_ID=$PROJECT_ID,_TAG=latest \
    --project=$PROJECT_ID

echo "✓ Backend deployed"

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(status.url)")

echo ""
echo "=================================================="
echo "✓ Deployment Complete!"
echo "=================================================="
echo ""
echo "📊 Service URL: $SERVICE_URL"
echo ""
echo "🧪 Next Steps:"
echo "  1. Run validation: ./scripts/validate-deployment.sh"
echo "  2. Import Grafana dashboards: cd grafana && ./import-dashboards.sh"
echo "  3. Monitor metrics in Grafana Cloud"
echo "  4. Check errors in Sentry dashboard"
echo ""
echo "📚 Documentation:"
echo "  - PRODUCTION_DEPLOYMENT_CHECKLIST.md"
echo "  - DEPLOYMENT_GUIDE_REDIS_GRAFANA.md"
echo "  - MULTI_TENANCY_GUIDE.md"
echo ""
