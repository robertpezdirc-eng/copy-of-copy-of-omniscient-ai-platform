# OMNI Dashboard - Google Cloud Run Deployment Script (PowerShell)
# This script deploys the OMNI dashboard to Google Cloud Run (free tier eligible)

Write-Host "🚀 OMNI DASHBOARD - GOOGLE CLOUD RUN DEPLOYMENT" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan

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

# 1. Enable required Google Cloud APIs
Write-Status "Enabling required Google Cloud APIs..."
$apis = @("run.googleapis.com", "containerregistry.googleapis.com", "cloudbuild.googleapis.com")
foreach ($api in $apis) {
    Write-Status "Enabling $api..."
    gcloud services enable $api
}

# 2. Set region for Cloud Run
$region = "us-central1"
Write-Status "Using region: $region"

# 3. Create Dockerfile for the dashboard
Write-Status "Creating Dockerfile for the dashboard..."

$dockerfileContent = @"
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy dashboard files
COPY omni_dashboard_professional.py .
COPY omni_singularity_core.py .
COPY test_imports.py .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 8080

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8080

# Run the dashboard
CMD ["python", "omni_dashboard_professional.py"]
"@

Set-Content -Path "Dockerfile" -Value $dockerfileContent

# 4. Create requirements.txt for Docker
Write-Status "Creating requirements.txt for Docker..."
$requirementsContent = @"
fastapi==0.104.1
uvicorn[standard]==0.24.0
plotly==5.17.0
pandas==2.1.3
psutil==5.9.6
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
python-multipart==0.0.6
requests==2.31.0
"@

Set-Content -Path "requirements.txt" -Value $requirementsContent

# 5. Create cloudbuild.yaml for automated builds
Write-Status "Creating Cloud Build configuration..."

$cloudbuildContent = @"
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', 'gcr.io/$PROJECT_ID/omni-dashboard', '.']

- name: 'gcr.io/cloud-builders/docker'
  args: ['push', 'gcr.io/$PROJECT_ID/omni-dashboard']

- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  entrypoint: gcloud
  args:
  - 'run'
  - 'deploy'
  - 'omni-dashboard-service'
  - '--image'
  - 'gcr.io/$PROJECT_ID/omni-dashboard'
  - '--region'
  - '$region'
  - '--platform'
  - 'managed'
  - '--allow-unauthenticated'
  - '--port'
  - '8080'
  - '--memory'
  - '1Gi'
  - '--cpu'
  - '1'
  - '--max-instances'
  - '3'
  - '--set-env-vars'
  - 'PYTHONPATH=/app,PORT=8080'

options:
  logging: CLOUD_LOGGING_ONLY
"@

Set-Content -Path "cloudbuild.yaml" -Value $cloudbuildContent

# 6. Build and deploy using Cloud Build
Write-Status "Building and deploying to Cloud Run..."
$projectId = gcloud config get-value project

try {
    # Submit build to Cloud Build
    $buildResult = gcloud builds submit --config cloudbuild.yaml .

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Build submitted successfully"

        # Get the service URL
        $serviceUrl = gcloud run services describe omni-dashboard-service --region=$region --format="value(status.url)"

        Write-Success "🎉 OMNI DASHBOARD DEPLOYED TO GOOGLE CLOUD RUN!"
        Write-Host ""
        Write-Host "🌐 Dashboard URL:" -ForegroundColor Yellow
        Write-Host "   $serviceUrl" -ForegroundColor Green
        Write-Host ""
        Write-Host "📋 Service Information:" -ForegroundColor Yellow
        Write-Host "   Service Name: omni-dashboard-service" -ForegroundColor Green
        Write-Host "   Region: $region" -ForegroundColor Green
        Write-Host "   Project: $projectId" -ForegroundColor Green
        Write-Host ""
        Write-Host "🔧 Management Commands:" -ForegroundColor Yellow
        Write-Host "   Check status: gcloud run services describe omni-dashboard-service --region=$region"
        Write-Host "   View logs: gcloud logs read ""resource.type=cloud_run_revision"" --limit 50"
        Write-Host "   Update service: gcloud run services update omni-dashboard-service --region=$region"
        Write-Host ""
        Write-Host "💡 Next steps:" -ForegroundColor Yellow
        Write-Host "   1. Open your browser and go to: $serviceUrl"
        Write-Host "   2. The dashboard should be accessible immediately"
        Write-Host "   3. Check the logs if you encounter any issues"
        Write-Host ""
        Write-Host "✅ Deployment completed successfully!" -ForegroundColor Green

    } else {
        Write-Error-Custom "Build failed. Check the logs above for details."
        exit 1
    }

} catch {
    Write-Error-Custom "Deployment failed: $($_.Exception.Message)"
    exit 1
}