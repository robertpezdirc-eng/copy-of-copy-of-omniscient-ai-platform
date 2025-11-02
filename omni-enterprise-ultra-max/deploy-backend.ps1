param(
  [Parameter(Mandatory=$true)] [string]$PROJECT_ID,
  [string]$REGION = "europe-west1",
  [string]$SERVICE = "omni-ultra-backend",
  [string]$TAG = $(Get-Date -Format "yyyyMMdd-HHmmss"),
  [string]$ENCRYPTION_SECRET_RESOURCE = "",
  [string]$MIN_INSTANCES = "1",
  [string]$MAX_INSTANCES = "10",
  [string]$MEMORY = "1024Mi",
  [string]$CPU = "1",
  [string]$TIMEOUT = "600"
)

$ErrorActionPreference = "Stop"

Write-Host "[i] Project: $PROJECT_ID  Region: $REGION  Service: $SERVICE  Tag: $TAG"

# Verify gcloud
try {
  gcloud --version | Out-Null
} catch {
  Write-Error "gcloud is not installed or not on PATH. Install Google Cloud SDK and retry."
  exit 1
}

# Configure project
Write-Host "[i] Setting gcloud project..."
gcloud config set project $PROJECT_ID | Out-Null

# Build and push image via Cloud Build
Write-Host "[i] Building backend image with Cloud Build..."
gcloud builds submit --config cloudbuild-backend.yaml --substitutions "_PROJECT_ID=$PROJECT_ID,_TAG=$TAG"

if ($LASTEXITCODE -ne 0) { Write-Error "Cloud Build failed."; exit 1 }

# Deploy to Cloud Run
Write-Host "[i] Deploying to Cloud Run..."
$IMAGE_URI = "europe-west1-docker.pkg.dev/$PROJECT_ID/omni/omni-ultra-backend:$TAG"
$ENV_VARS = @(
  "RUN_AS_INTERNAL=0",
  "PERF_SLOW_THRESHOLD_SEC=1.0",
  "GCP_PROJECT_ID=$PROJECT_ID"
)
if ($ENCRYPTION_SECRET_RESOURCE -ne "") {
  $ENV_VARS += "GCP_SECRET_ENCRYPTION_KEY=$ENCRYPTION_SECRET_RESOURCE"
}

$envArg = $ENV_VARS -join ","

gcloud run deploy $SERVICE `
  --image $IMAGE_URI `
  --region $REGION `
  --platform managed `
  --allow-unauthenticated `
  --port 8080 `
  --min-instances $MIN_INSTANCES `
  --max-instances $MAX_INSTANCES `
  --memory $MEMORY `
  --cpu $CPU `
  --timeout $TIMEOUT `
  --set-env-vars $envArg

if ($LASTEXITCODE -ne 0) { Write-Error "Cloud Run deploy failed."; exit 1 }

Write-Host "[OK] Deploy complete."
