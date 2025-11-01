#!/bin/bash
#
# Deploy OMNI Platform to Google Cloud Run
# Builds and deploys both frontend and backend services
#

set -e

echo "☁️  OMNI Platform - Cloud Run Deployment"
echo "========================================"

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-omni-platform-prod}"
REGION="${GCP_REGION:-europe-west1}"
FRONTEND_SERVICE="omni-frontend"
BACKEND_SERVICE="omni-backend"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check gcloud CLI
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI not found. Install from https://cloud.google.com/sdk"
    exit 1
fi

echo -e "${YELLOW}🔐 Step 1: Authenticating with Google Cloud${NC}"
gcloud auth list
gcloud config set project $PROJECT_ID

echo -e "${YELLOW}🏗️  Step 2: Building Docker images${NC}"

# Build frontend
echo -e "${BLUE}Building frontend...${NC}"
docker build -f frontend/Dockerfile -t gcr.io/$PROJECT_ID/$FRONTEND_SERVICE:latest .

# Build backend
echo -e "${BLUE}Building backend...${NC}"
docker build -f backend/Dockerfile -t gcr.io/$PROJECT_ID/$BACKEND_SERVICE:latest .

echo -e "${YELLOW}📤 Step 3: Pushing images to Container Registry${NC}"
docker push gcr.io/$PROJECT_ID/$FRONTEND_SERVICE:latest
docker push gcr.io/$PROJECT_ID/$BACKEND_SERVICE:latest

echo -e "${YELLOW}🚀 Step 4: Deploying to Cloud Run${NC}"

# Deploy backend first
echo -e "${BLUE}Deploying backend service...${NC}"
gcloud run deploy $BACKEND_SERVICE \
    --image gcr.io/$PROJECT_ID/$BACKEND_SERVICE:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --set-env-vars "AI_GATEWAY_URL=https://ai-gateway-661612368188.europe-west1.run.app" \
    --port 8080

# Get backend URL
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE --region $REGION --format 'value(status.url)')
echo -e "${GREEN}Backend URL: $BACKEND_URL${NC}"

# Deploy frontend
echo -e "${BLUE}Deploying frontend service...${NC}"
gcloud run deploy $FRONTEND_SERVICE \
    --image gcr.io/$PROJECT_ID/$FRONTEND_SERVICE:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 256Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --set-env-vars "API_BASE_URL=$BACKEND_URL" \
    --port 8000

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE --region $REGION --format 'value(status.url)')

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "📡 Service URLs:"
echo "   Frontend: $FRONTEND_URL"
echo "   Backend:  $BACKEND_URL"
echo ""
echo "🔍 Monitor services:"
echo "   gcloud run services list --region $REGION"
echo ""
echo "📊 View logs:"
echo "   gcloud run services logs read $FRONTEND_SERVICE --region $REGION"
echo "   gcloud run services logs read $BACKEND_SERVICE --region $REGION"
