#!/bin/bash

# OMNI Platform - Google Cloud Deployment Script
# This script deploys the entire OMNI platform to Google Cloud

set -e

# Configuration
PROJECT_ID="refined-graph-471712-n9"
REGION="europe-west1"
ZONE="europe-west1-b"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if gcloud is installed
check_gcloud() {
    log_info "Checking Google Cloud CLI..."
    if ! command -v gcloud &> /dev/null; then
        log_error "Google Cloud CLI is not installed. Please install it first:"
        log_error "https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    log_success "Google Cloud CLI found"
}

# Authenticate with Google Cloud
authenticate() {
    log_info "Authenticating with Google Cloud..."
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 > /dev/null; then
        log_warning "Not authenticated with Google Cloud. Please run:"
        log_warning "gcloud auth login"
        exit 1
    fi
    log_success "Authentication verified"
}

# Set project
set_project() {
    log_info "Setting Google Cloud project to: $PROJECT_ID"
    gcloud config set project $PROJECT_ID
    log_success "Project set to $PROJECT_ID"
}

# Enable required APIs
enable_apis() {
    log_info "Enabling required Google Cloud APIs..."

    apis=(
        "cloudbuild.googleapis.com"
        "run.googleapis.com"
        "containerregistry.googleapis.com"
        "storage.googleapis.com"
        "logging.googleapis.com"
        "monitoring.googleapis.com"
        "secretmanager.googleapis.com"
        "iam.googleapis.com"
        "compute.googleapis.com"
    )

    for api in "${apis[@]}"; do
        log_info "Enabling $api..."
        gcloud services enable $api --project=$PROJECT_ID
    done

    log_success "All required APIs enabled"
}

# Create secrets
create_secrets() {
    log_info "Creating secrets in Secret Manager..."

    # Create OpenAI API key secret if it exists
    if [ -f "openai key.txt" ]; then
        gcloud secrets create openai-api-key --data-file="openai key.txt" 2>/dev/null || \
        gcloud secrets versions add openai-api-key --data-file="openai key.txt"
        log_success "OpenAI API key secret created"
    else
        log_warning "OpenAI API key file not found. Please create 'openai key.txt' with your API key"
    fi

    # Create service account key secret if it exists
    if [ -f "service_account.json" ]; then
        gcloud secrets create service-account-key --data-file="service_account.json" 2>/dev/null || \
        gcloud secrets versions add service-account-key --data-file="service_account.json"
        log_success "Service account key secret created"
    fi

    log_success "Secrets created"
}

# Create Cloud Storage buckets
create_buckets() {
    log_info "Creating Cloud Storage buckets..."

    buckets=(
        "omni-platform-$PROJECT_ID-assets"
        "omni-platform-$PROJECT_ID-backups"
        "omni-platform-$PROJECT_ID-logs"
    )

    for bucket in "${buckets[@]}"; do
        if gsutil ls gs://$bucket >/dev/null 2>&1; then
            log_info "Bucket $bucket already exists"
        else
            gsutil mb -l $REGION gs://$bucket
            gsutil uniformbucketlevelaccess set on gs://$bucket
            log_success "Created bucket: $bucket"
        fi
    done

    log_success "Cloud Storage buckets created"
}

# Build and deploy with Cloud Build
deploy_services() {
    log_info "Building and deploying services with Cloud Build..."

    # Set OpenAI API key for Cloud Build
    if gcloud secrets describe openai-api-key >/dev/null 2>&1; then
        OPENAI_KEY=$(gcloud secrets versions access latest --secret="openai-api-key")
        export OPENAI_API_KEY="$OPENAI_KEY"
    fi

    # Trigger Cloud Build
    gcloud builds submit --config cloudbuild.yaml .

    log_success "Services deployed successfully"
}

# Configure monitoring and alerting
setup_monitoring() {
    log_info "Setting up monitoring and alerting..."

    # Create alerting policy for high CPU usage
    gcloud alpha monitoring policies create \
        --policy-from-file=monitoring-policy-cpu.json \
        --project=$PROJECT_ID 2>/dev/null || log_info "CPU monitoring policy already exists"

    # Create alerting policy for high memory usage
    gcloud alpha monitoring policies create \
        --policy-from-file=monitoring-policy-memory.json \
        --project=$PROJECT_ID 2>/dev/null || log_info "Memory monitoring policy already exists"

    # Create alerting policy for error rate
    gcloud alpha monitoring policies create \
        --policy-from-file=monitoring-policy-errors.json \
        --project=$PROJECT_ID 2>/dev/null || log_info "Error monitoring policy already exists"

    log_success "Monitoring and alerting configured"
}

# Set up IAM permissions
setup_iam() {
    log_info "Setting up IAM permissions..."

    # Create service account for Cloud Run
    SERVICE_ACCOUNT_EMAIL="omni-platform@$PROJECT_ID.iam.gserviceaccount.com"

    gcloud iam service-accounts create omni-platform \
        --display-name="OMNI Platform Service Account" \
        --project=$PROJECT_ID 2>/dev/null || log_info "Service account already exists"

    # Grant necessary permissions
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/cloudtranslate.user" 2>/dev/null || true

    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/secretmanager.secretAccessor" 2>/dev/null || true

    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/storage.objectAdmin" 2>/dev/null || true

    log_success "IAM permissions configured"
}

# Main deployment function
main() {
    log_info "🚀 Starting OMNI Platform deployment to Google Cloud..."
    echo "=================================================="

    check_gcloud
    authenticate
    set_project
    enable_apis
    create_secrets
    create_buckets
    setup_iam
    deploy_services
    setup_monitoring

    echo ""
    log_success "🎉 OMNI Platform deployment completed successfully!"
    echo ""
    log_info "📋 Service URLs:"
    echo "   API Service: $(gcloud run services describe omni-platform-api --platform=managed --region=$REGION --format='value(status.url)')"
    echo "   Web Service: $(gcloud run services describe omni-platform-web --platform=managed --region=$REGION --format='value(status.url)')"
    echo ""
    log_info "📊 Monitoring Dashboard:"
    echo "   https://console.cloud.google.com/monitoring/dashboards"
    echo ""
    log_info "📝 Logs:"
    echo "   https://console.cloud.google.com/logs/query"
    echo ""
    log_info "🔧 Management Console:"
    echo "   https://console.cloud.google.com/run"
}

# Run main function
main "$@"