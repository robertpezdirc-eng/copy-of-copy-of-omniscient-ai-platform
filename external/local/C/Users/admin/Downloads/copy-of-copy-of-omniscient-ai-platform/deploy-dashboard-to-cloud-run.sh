#!/bin/bash

# OMNI Platform Dashboard - Google Cloud Run Deployment Script
# Deploy to project: refined-graph-471712-n9

set -e

# Configuration
PROJECT_ID="refined-graph-471712-n9"
REGION="europe-west1"
SERVICE_NAME="omni-dashboard"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Check if gcloud is installed and authenticated
check_gcloud_auth() {
    log_info "Checking Google Cloud authentication..."

    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is not installed. Please install Google Cloud SDK first."
        exit 1
    fi

    # Check if authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_warning "Not authenticated with Google Cloud. Please run: gcloud auth login"
        log_info "Opening browser for authentication..."
        gcloud auth login
    fi

    # Set project
    log_info "Setting Google Cloud project to: ${PROJECT_ID}"
    gcloud config set project ${PROJECT_ID}
}

# Enable required APIs
enable_apis() {
    log_info "Enabling required Google Cloud APIs..."

    apis=(
        "run.googleapis.com"
        "containerregistry.googleapis.com"
        "cloudbuild.googleapis.com"
        "monitoring.googleapis.com"
        "logging.googleapis.com"
    )

    for api in "${apis[@]}"; do
        log_info "Enabling API: ${api}"
        gcloud services enable ${api} --project=${PROJECT_ID}
    done
}

# Create requirements.txt for the dashboard
create_requirements() {
    log_info "Creating requirements.txt for the dashboard..."

    cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
plotly==5.17.0
pandas==2.1.3
psutil==5.9.6
python-multipart==0.0.6
aiofiles==23.2.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-decouple==3.8
gunicorn==21.2.0
requests==2.31.0
google-cloud-monitoring==2.16.0
google-cloud-logging==3.8.0
google-cloud-trace==1.11.0
google-cloud-error-reporting==1.10.0
EOF
}

# Build and push Docker image
build_and_push_image() {
    log_info "Building Docker image with Dockerfile.dashboard..."

    # Build the image using specialized dashboard Dockerfile
    docker build -f Dockerfile.dashboard -t ${IMAGE_NAME}:latest .

    log_info "Pushing Docker image to Google Container Registry..."
    gcloud auth configure-docker --quiet
    docker push ${IMAGE_NAME}:latest

    log_success "OMNI Professional Dashboard image pushed successfully: ${IMAGE_NAME}:latest"
}

# Deploy to Cloud Run
deploy_to_cloud_run() {
    log_info "Deploying to Google Cloud Run..."

    gcloud run deploy ${SERVICE_NAME} \
        --image ${IMAGE_NAME}:latest \
        --platform managed \
        --region ${REGION} \
        --allow-unauthenticated \
        --port 8080 \
        --memory 2Gi \
        --cpu 2 \
        --min-instances 1 \
        --max-instances 10 \
        --concurrency 80 \
        --timeout 600 \
        --set-env-vars "PROJECT_ID=${PROJECT_ID}" \
        --set-env-vars "ENVIRONMENT=production" \
        --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
        --set-env-vars "GOOGLE_CLOUD_REGION=${REGION}" \
        --set-env-vars "ORCHESTRATION_ENABLED=1" \
        --set-env-vars "OMNI_SYSTEM_CHECKS=false" \
        --set-env-vars "OMNI_QUIET_CLOUDRUN=true" \
        --set-secrets "OPENAI_API_KEY=openai-api-key:latest" \
        --project ${PROJECT_ID}

    log_success "OMNI Professional Dashboard deployed to Cloud Run successfully!"
}

# Get service URL
get_service_info() {
    log_info "Getting service information..."

    SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
        --platform managed \
        --region ${REGION} \
        --format 'value(status.url)' \
        --project ${PROJECT_ID})

    if [ -n "${SERVICE_URL}" ]; then
        log_success "🎉 OMNI Dashboard is live!"
        echo ""
        echo "📊 Dashboard URL: ${SERVICE_URL}"
        echo "🔗 Direct access: ${SERVICE_URL}/"
        echo "📈 Metrics API: ${SERVICE_URL}/api/metrics"
        echo "🔧 Services API: ${SERVICE_URL}/api/services"
        echo "☁️ Cloud API: ${SERVICE_URL}/api/cloud"
        echo "🚨 Alerts API: ${SERVICE_URL}/api/alerts"
        echo ""
        echo "💡 Useful commands:"
        echo "   View logs: gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME}\" --limit 50"
        echo "   Check status: gcloud run services describe ${SERVICE_NAME} --region=${REGION}"
        echo "   Update deployment: gcloud run deploy ${SERVICE_NAME} --image ${IMAGE_NAME}:latest --region=${REGION}"
    else
        log_error "Failed to get service URL"
        exit 1
    fi
}

# Main deployment function
main() {
    echo "🚀 OMNI Platform Dashboard - Google Cloud Run Deployment"
    echo "======================================================"
    echo "Project: ${PROJECT_ID}"
    echo "Region: ${REGION}"
    echo "Service: ${SERVICE_NAME}"
    echo ""

    # Run deployment steps
    check_gcloud_auth
    enable_apis
    create_requirements
    build_and_push_image
    deploy_to_cloud_run
    get_service_info

    echo ""
    log_success "Deployment completed successfully!"
    echo ""
    echo "🎯 Next steps:"
    echo "1. Open the dashboard URL in your browser"
    echo "2. Verify all APIs are working correctly"
    echo "3. Set up monitoring and alerting if needed"
    echo "4. Configure custom domain (optional)"
    echo ""
    echo "🔒 Security note: The service is deployed with --allow-unauthenticated"
    echo "   Consider adding authentication for production use."
}

# Run main function with all arguments
main "$@"