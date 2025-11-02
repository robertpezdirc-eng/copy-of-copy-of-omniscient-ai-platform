#!/bin/bash

# ================================================
# TIER 1 Deployment Script
# Deploys AI Worker with production essentials
# ================================================

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-refined-graph-471712-n9}"
REGION="${GCP_REGION:-europe-west1}"
SERVICE_NAME="omni-ai-worker"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:tier1"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  TIER 1 Deployment - OMNI AI Worker${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Step 1: Check prerequisites
echo -e "${YELLOW}Step 1: Checking prerequisites...${NC}"

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not found${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: docker not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites OK${NC}"
echo ""

# Step 2: Check environment variables
echo -e "${YELLOW}Step 2: Checking environment variables...${NC}"

if [ -z "$SENTRY_DSN" ]; then
    echo -e "${YELLOW}Warning: SENTRY_DSN not set (error tracking disabled)${NC}"
    SENTRY_DSN="not-configured"
fi

if [ -z "$MASTER_API_KEY" ]; then
    echo -e "${YELLOW}Warning: MASTER_API_KEY not set, using default (CHANGE IN PRODUCTION!)${NC}"
    MASTER_API_KEY="master-key-change-in-production"
fi

echo -e "${GREEN}✓ Environment check complete${NC}"
echo ""

# Step 3: Build Docker image
echo -e "${YELLOW}Step 3: Building Docker image...${NC}"

cd ai-worker

# Create Dockerfile if it doesn't exist
if [ ! -f "Dockerfile" ]; then
    echo -e "${BLUE}Creating Dockerfile...${NC}"
    cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spacy model
RUN python -m spacy download en_core_web_sm

# Copy application
COPY . .

# Expose port
EXPOSE 8080

# Run with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
EOF
fi

echo -e "${BLUE}Building image: ${IMAGE_NAME}${NC}"
docker build -t ${IMAGE_NAME} .

echo -e "${GREEN}✓ Docker image built${NC}"
echo ""

# Step 4: Push to GCR
echo -e "${YELLOW}Step 4: Pushing image to GCR...${NC}"

gcloud auth configure-docker gcr.io --quiet
docker push ${IMAGE_NAME}

echo -e "${GREEN}✓ Image pushed to GCR${NC}"
echo ""

# Step 5: Deploy to Cloud Run
echo -e "${YELLOW}Step 5: Deploying to Cloud Run...${NC}"

gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --region ${REGION} \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars "ENVIRONMENT=production,LOG_LEVEL=INFO,SENTRY_DSN=${SENTRY_DSN},MASTER_API_KEY=${MASTER_API_KEY},GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
  --project ${PROJECT_ID}

echo -e "${GREEN}✓ Deployed to Cloud Run${NC}"
echo ""

# Step 6: Get service URL
echo -e "${YELLOW}Step 6: Getting service URL...${NC}"

SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --region ${REGION} \
  --project ${PROJECT_ID} \
  --format="value(status.url)")

echo -e "${GREEN}Service URL: ${SERVICE_URL}${NC}"
echo ""

# Step 7: Health check
echo -e "${YELLOW}Step 7: Running health check...${NC}"

sleep 5  # Wait for service to be ready

HEALTH_CHECK=$(curl -s "${SERVICE_URL}/health" || echo "failed")

if echo "$HEALTH_CHECK" | grep -q "ok"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    echo -e "${GREEN}Response: ${HEALTH_CHECK}${NC}"
else
    echo -e "${RED}✗ Health check failed${NC}"
    echo -e "${RED}Response: ${HEALTH_CHECK}${NC}"
fi

echo ""

# Step 8: Test metrics endpoint
echo -e "${YELLOW}Step 8: Testing Prometheus metrics...${NC}"

METRICS_CHECK=$(curl -s "${SERVICE_URL}/metrics" | head -n 5)

if echo "$METRICS_CHECK" | grep -q "api_requests_total"; then
    echo -e "${GREEN}✓ Metrics endpoint working${NC}"
    echo -e "${GREEN}Sample: ${METRICS_CHECK}${NC}"
else
    echo -e "${YELLOW}⚠ Metrics endpoint may need initialization${NC}"
fi

echo ""

# Summary
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  TIER 1 Deployment Complete! 🚀${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "${GREEN}Service Details:${NC}"
echo -e "  URL: ${SERVICE_URL}"
echo -e "  Health: ${SERVICE_URL}/health"
echo -e "  Metrics: ${SERVICE_URL}/metrics"
echo -e "  Docs: ${SERVICE_URL}/docs"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Test with: python tests/tier1_tests.py"
echo "  2. Configure Sentry: https://sentry.io"
echo "  3. Set up Grafana dashboards"
echo "  4. Create production API keys"
echo "  5. Monitor metrics: ${SERVICE_URL}/metrics"
echo ""
echo -e "${GREEN}TIER 1 Features Deployed:${NC}"
echo "  ✓ Prometheus Metrics"
echo "  ✓ Structured Logging"
echo "  ✓ API Authentication"
echo "  ✓ Rate Limiting"
echo "  ✓ Sentry Error Tracking"
echo ""

cd ..
