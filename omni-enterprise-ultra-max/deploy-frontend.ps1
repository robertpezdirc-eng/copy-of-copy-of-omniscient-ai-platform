# Quick Frontend Deployment Script for PowerShell
# Run from repo root

$Project = "refined-graph-471712-n9"
$Region = "europe-west1"
$Repo = "omni-ultra"
$Image = "omni-frontend"
$Tag = "v1.0.0"
$API = "https://omni-ultra-backend-prod-661612368188.europe-west1.run.app"
$WS = "wss://omni-ultra-backend-prod-661612368188.europe-west1.run.app"

Write-Host "Building & deploying frontend to Cloud Run..." -ForegroundColor Cyan

# Submit Cloud Build from repo root using frontend/cloudbuild.yaml
# This builds the Docker image and deploys it to Cloud Run

gcloud builds submit `
  --config=frontend/cloudbuild.yaml `
  --project=$Project `
  --substitutions=_PROJECT_ID=$Project,_REGION=$Region,_REPO=$Repo,_IMAGE=$Image,_TAG=$Tag,_VITE_API_URL=$API,_VITE_WS_URL=$WS

Write-Host "Fetching service URL..." -ForegroundColor Yellow
$FRONTEND_URL = gcloud run services describe omni-frontend --region=$Region --project=$Project --format="value(status.url)"
Write-Host "Frontend URL: $FRONTEND_URL" -ForegroundColor Green
