# OMNI Platform Dashboard - Cloud Run Deployment Script (PowerShell)
# This script deploys the integrated OMNI dashboard to Google Cloud Run

Write-Host "🚀 OMNI DASHBOARD - GOOGLE CLOUD RUN DEPLOYMENT" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Configuration
$PROJECT_ID = "gen-lang-client-0885737339"
$REGION = "europe-west1"
$SERVICE_NAME = "omni-dashboard"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

# 1. Check prerequisites
Write-Status "Checking prerequisites..."

# Check if gcloud is installed
$gcloudExists = Get-Command gcloud -ErrorAction SilentlyContinue
if (-not $gcloudExists) {
    Write-Error-Custom "gcloud CLI is not installed. Please install Google Cloud SDK first."
    exit 1
}

# Check if Docker is installed
$dockerExists = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerExists) {
    Write-Error-Custom "Docker is not installed. Please install Docker first."
    exit 1
}

# 2. Authenticate with Google Cloud
Write-Status "Authenticating with Google Cloud..."
try {
    $authResult = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>$null
    if (-not $authResult) {
        Write-Status "Please authenticate with Google Cloud:"
        gcloud auth login
    }
} catch {
    Write-Error-Custom "Failed to authenticate with Google Cloud"
    exit 1
}

# 3. Set project
Write-Status "Setting Google Cloud project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# 4. Enable required APIs
Write-Status "Enabling required Google Cloud APIs..."
$apis = @("run.googleapis.com", "containerregistry.googleapis.com", "cloudbuild.googleapis.com")
foreach ($api in $apis) {
    Write-Status "Enabling $api..."
    gcloud services enable $api
}

# 5. Build Docker image
Write-Status "Building Docker image..."
try {
    docker build -f Dockerfile.dashboard -t $IMAGE_NAME:latest .
    Write-Success "Docker image built successfully"
} catch {
    Write-Error-Custom "Failed to build Docker image: $_"
    exit 1
}

# 6. Push image to Google Container Registry
Write-Status "Pushing image to Google Container Registry..."
try {
    gcloud auth configure-docker --quiet
    docker push $IMAGE_NAME:latest
    Write-Success "Image pushed successfully"
} catch {
    Write-Error-Custom "Failed to push image: $_"
    exit 1
}

# 7. Deploy to Cloud Run
Write-Status "Deploying to Cloud Run..."
try {
    $deployCmd = @"
    gcloud run deploy $SERVICE_NAME `
        --image $IMAGE_NAME:latest `
        --platform managed `
        --region $REGION `
        --allow-unauthenticated `
        --port 8080 `
        --memory 1Gi `
        --cpu 1 `
        --max-instances 3 `
        --timeout 300 `
        --set-env-vars PROJECT_ID=$PROJECT_ID `
        --set-env-vars REGION=$REGION `
        --set-env-vars OMNI_DEBUG_AUTH=true
"@

    Invoke-Expression $deployCmd
    Write-Success "Dashboard deployed to Cloud Run successfully"
} catch {
    Write-Error-Custom "Failed to deploy to Cloud Run: $_"
    exit 1
}

# 8. Get service URL
Write-Status "Getting service information..."
try {
    $serviceUrl = gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format="value(status.url)"
    Write-Success "Dashboard is available at: $serviceUrl"

    # Display service details
    Write-Host ""
    Write-Host "📋 SERVICE DETAILS:" -ForegroundColor Yellow
    Write-Host "   Service Name: $SERVICE_NAME" -ForegroundColor Green
    Write-Host "   Region: $REGION" -ForegroundColor Green
    Write-Host "   URL: $serviceUrl" -ForegroundColor Green
    Write-Host "   Project: $PROJECT_ID" -ForegroundColor Green

    Write-Host ""
    Write-Host "🔧 MANAGEMENT COMMANDS:" -ForegroundColor Yellow
    Write-Host "   View logs: gcloud logs read ""resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME"" --limit 50" -ForegroundColor Gray
    Write-Host "   View service: gcloud run services describe $SERVICE_NAME --region $REGION" -ForegroundColor Gray
    Write-Host "   Update image: gcloud run deploy $SERVICE_NAME --image $IMAGE_NAME:latest --region $REGION" -ForegroundColor Gray

    Write-Host ""
    Write-Host "💡 FEATURES:" -ForegroundColor Yellow
    Write-Host "   ✅ Real-time system monitoring" -ForegroundColor Green
    Write-Host "   ✅ OMNI platform integration" -ForegroundColor Green
    Write-Host "   ✅ Interactive charts and graphs" -ForegroundColor Green
    Write-Host "   ✅ Google Cloud Functions integration" -ForegroundColor Green
    Write-Host "   ✅ Auto-scaling and high availability" -ForegroundColor Green

} catch {
    Write-Error-Custom "Failed to get service information: $_"
    exit 1
}

Write-Success "🎉 OMNI DASHBOARD DEPLOYMENT COMPLETED!"
Write-Host ""
Write-Host "🌐 Access your dashboard at: $serviceUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "   1. Open the URL in your browser"
Write-Host "   2. The dashboard will show both system metrics and OMNI platform data"
Write-Host "   3. Monitor logs for any issues"
Write-Host "   4. Configure authentication if needed for production use"