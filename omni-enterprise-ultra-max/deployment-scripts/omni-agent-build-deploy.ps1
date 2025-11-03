param(
  [Parameter(Mandatory=$true)] [string]$PROJECT_ID,
  [string]$REGION = "europe-west1",
  [string]$GCP_KEY_FILE = "",
  [string[]]$SERVICES = @("backend","frontend","gateway","ollama","ai-worker","backup"),
  [switch]$SKIP_BUILD
)

$ErrorActionPreference = "Stop"

function Invoke-HealthCheck {
  param([string]$Url)
  try {
    $code = (curl.exe -s -o NUL -w "%{http_code}" $Url)
    return $code
  } catch { return "000" }
}

Write-Host "[i] Project: $PROJECT_ID  Region: $REGION" -ForegroundColor Cyan

if ($GCP_KEY_FILE -and (Test-Path $GCP_KEY_FILE)) {
  Write-Host "[i] Activating service account from $GCP_KEY_FILE" -ForegroundColor Yellow
  gcloud auth activate-service-account --key-file=$GCP_KEY_FILE | Out-Null
}

gcloud config set project $PROJECT_ID | Out-Null

# Ensure minimal SDK components for Cloud Run deploys
try { gcloud --version | Out-Null } catch { throw "gcloud not installed" }

$TAG = Get-Date -Format "yyyyMMdd-HHmmss"

if ("ollama" -in $SERVICES) {
  Write-Host "[->] Deploying Ollama (Cloud Run)" -ForegroundColor Cyan
  $ollamaUrl = (gcloud run services describe ollama --region $REGION --format "value(status.url)" 2>$null)
  if (-not $ollamaUrl) {
    gcloud run deploy ollama `
      --image=ollama/ollama:latest `
      --region=$REGION `
      --platform=managed `
      --allow-unauthenticated `
      --cpu=2 `
      --memory=4Gi `
      --port=8080 `
      --execution-environment=gen2 `
      --set-env-vars="OLLAMA_HOST=0.0.0.0:8080,OLLAMA_KEEP_ALIVE=5m" | Out-Null
    $ollamaUrl = (gcloud run services describe ollama --region $REGION --format "value(status.url)")
  }
  Write-Host "[OK] Ollama URL: $ollamaUrl" -ForegroundColor Green
  $oc = Invoke-HealthCheck "$ollamaUrl/api/tags"
  Write-Host "[health] $oc /api/tags"
}

if ("backend" -in $SERVICES) {
  Write-Host "[->] Building & Deploying Backend" -ForegroundColor Cyan
  if (-not $SKIP_BUILD) {
    # Use reduced context via .gcloudignore already present
    gcloud builds submit --config cloudbuild-backend.yaml --substitutions "_PROJECT_ID=$PROJECT_ID,_TAG=$TAG" | Out-Null
  }
  # Deploy using existing script if present
  if (Test-Path "./deploy-backend.ps1") {
    .\deploy-backend.ps1 -PROJECT_ID $PROJECT_ID -REGION $REGION -TAG $TAG
  } else {
    $IMAGE_URI = "europe-west1-docker.pkg.dev/$PROJECT_ID/omni/omni-ultra-backend:$TAG"
    gcloud run deploy omni-ultra-backend `
      --image $IMAGE_URI `
      --region $REGION `
      --platform managed `
      --allow-unauthenticated `
      --port 8080 | Out-Null
  }
  $backendUrl = (gcloud run services describe omni-ultra-backend --region $REGION --format "value(status.url)")
  Write-Host "[OK] Backend URL: $backendUrl" -ForegroundColor Green
  $bc = Invoke-HealthCheck "$backendUrl/api/health"
  Write-Host "[health] $bc /api/health"
}

if ("gateway" -in $SERVICES) {
  Write-Host "[->] Deploying Gateway" -ForegroundColor Cyan
  if (Test-Path "./deploy-gateway.ps1") {
    # Non-interactive deploy: replicate key args from script
    $backendUrl = (gcloud run services describe omni-ultra-backend --region $REGION --format "value(status.url)")
    Push-Location gateway
    gcloud run deploy ai-gateway `
      --source=. `
      --region=$REGION `
      --project=$PROJECT_ID `
      --allow-unauthenticated `
      --port=8080 `
      --set-env-vars="UPSTREAM_URL=$backendUrl,API_KEYS=prod-key-omni-2025" | Out-Null
    Pop-Location
  } else {
    Write-Host "[warn] deploy-gateway.ps1 not found; skipping gateway deploy" -ForegroundColor Yellow
  }
  $gwUrl = (gcloud run services describe ai-gateway --region $REGION --format "value(status.url)" 2>$null)
  if ($gwUrl) { Write-Host "[OK] Gateway URL: $gwUrl" -ForegroundColor Green }
}

if ("frontend" -in $SERVICES) {
  Write-Host "[->] Building & Deploying Frontend" -ForegroundColor Cyan
  if (Test-Path "./deploy-frontend.ps1") {
    # Use the Cloud Build file already configured
    .\deploy-frontend.ps1
  } else {
    Write-Host "[warn] deploy-frontend.ps1 not found; skipping frontend deploy" -ForegroundColor Yellow
  }
}

if ("ai-worker" -in $SERVICES) {
  Write-Host "[->] Deploying AI Worker" -ForegroundColor Cyan
  # Build and deploy from source directory
  if (Test-Path "./ai-worker") {
    gcloud run deploy omni-ai-worker `
      --source=ai-worker `
      --region=$REGION `
      --project=$PROJECT_ID `
      --allow-unauthenticated `
      --port=8080 `
      --cpu=2 `
      --memory=4Gi | Out-Null
    $aiwUrl = (gcloud run services describe omni-ai-worker --region $REGION --project $PROJECT_ID --format "value(status.url)")
    Write-Host "[OK] AI Worker URL: $aiwUrl" -ForegroundColor Green
    $hc = Invoke-HealthCheck "$aiwUrl/health"
    Write-Host "[health] $hc /health"
  } else {
    Write-Host "[warn] ./ai-worker not found; skipping AI Worker" -ForegroundColor Yellow
  }
}

if ("backup" -in $SERVICES) {
  Write-Host "[->] Deploying Backup Service" -ForegroundColor Cyan
  $bucketName = "omni-unified-backups-$PROJECT_ID"
  $exists = gcloud storage buckets list --filter "name:gs://$bucketName" --format "value(name)"
  if (-not $exists) {
    gcloud storage buckets create gs://$bucketName --location=$REGION | Out-Null
  }
  if (Test-Path "./backup-service") {
    gcloud run deploy omni-backup-service `
      --source=backup-service `
      --region=$REGION `
      --project=$PROJECT_ID `
      --allow-unauthenticated `
      --port=8080 `
      --set-env-vars "GCS_BUCKET=gs://$bucketName,BACKUP_NAME=omni-platform-backup" | Out-Null
    $bkUrl = (gcloud run services describe omni-backup-service --region $REGION --project $PROJECT_ID --format "value(status.url)")
    Write-Host "[OK] Backup Service URL: $bkUrl" -ForegroundColor Green
    $bhc = Invoke-HealthCheck "$bkUrl/health"
    Write-Host "[health] $bhc /health"
  } else {
    Write-Host "[warn] ./backup-service not found; skipping Backup Service" -ForegroundColor Yellow
  }
}

Write-Host "[DONE] Orchestration complete." -ForegroundColor Green
