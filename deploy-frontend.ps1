<#
------------------------------------------
 DEPLOY FRONTEND TO CLOUD RUN
------------------------------------------
 This script submits the frontend Cloud Build with properly quoted substitutions.
 Run from the repo root.
#>

param(
  [string]$PROJECT_ID = "refined-graph-471712-n9",
  [string]$REGION = "europe-west1"
)

$SERVICE_NAME = "omni-frontend"

Write-Host "🚀 Začenjam deploy frontend-a v $REGION ..." -ForegroundColor Cyan

# Use the frontend-specific Cloud Build; only pass the needed substitutions
gcloud builds submit `
  --config "frontend/cloudbuild.yaml" `
  --project "$PROJECT_ID" `
  --substitutions "_PROJECT_ID=$PROJECT_ID,_REGION=$REGION"

Write-Host "✅ Deploy ukaz poslan za $SERVICE_NAME" -ForegroundColor Green

Write-Host "🔎 Pridobivam URL storitve ..." -ForegroundColor Yellow
$FRONTEND_URL = gcloud run services describe $SERVICE_NAME --region "$REGION" --project "$PROJECT_ID" --format "value(status.url)"
if ($LASTEXITCODE -eq 0 -and $FRONTEND_URL) {
  Write-Host "🌐 Frontend URL: $FRONTEND_URL" -ForegroundColor Green
} else {
  Write-Host "ℹ️  Deploy poslan. URL bo na voljo po zaključku gradnje v Cloud Build logih." -ForegroundColor Yellow
}
