param(
  [Parameter(Mandatory=$true)] [string]$ProjectId,
  [Parameter(Mandatory=$true)] [string]$ServiceName,
  [string]$Region = "europe-west1",
  [Parameter(Mandatory=$true)] [string]$FrontendOrigin,
  [string]$ExtraOrigins = "" # Comma-separated list of extra origins
)

$ErrorActionPreference = "Stop"

Write-Host "Updating CORS env vars on Cloud Run service '$ServiceName' (project '$ProjectId')..." -ForegroundColor Cyan
& gcloud config set project $ProjectId | Out-Null

# Show current env vars
try {
  $svc = & gcloud run services describe $ServiceName --region $Region --format json | ConvertFrom-Json
  $curVars = @{}
  foreach ($e in $svc.spec.template.spec.containers[0].env) { $curVars[$e.name] = $e.value }
  Write-Host "Current OMNI_FRONTEND_ORIGIN: $($curVars["OMNI_FRONTEND_ORIGIN"])" -ForegroundColor Gray
  Write-Host "Current OMNI_FRONTEND_EXTRA_ORIGINS: $($curVars["OMNI_FRONTEND_EXTRA_ORIGINS"])" -ForegroundColor Gray
} catch {
  Write-Host "ℹ️ Could not read current env vars (service may not exist yet)." -ForegroundColor Yellow
}

# Prepare set-env-vars string
$envPairs = @()
$envPairs += "OMNI_FRONTEND_ORIGIN=$FrontendOrigin"
if (-not [string]::IsNullOrWhiteSpace($ExtraOrigins)) {
  $envPairs += "OMNI_FRONTEND_EXTRA_ORIGINS=$ExtraOrigins"
}
$envArg = ($envPairs -join ",")

Write-Host "Applying: $envArg" -ForegroundColor Gray
& gcloud run services update $ServiceName --region $Region --set-env-vars $envArg | Out-Null

# Confirm
$svc2 = & gcloud run services describe $ServiceName --region $Region --format json | ConvertFrom-Json
$env2 = @{}
foreach ($e in $svc2.spec.template.spec.containers[0].env) { $env2[$e.name] = $e.value }

Write-Host "✅ Updated OMNI_FRONTEND_ORIGIN: $($env2["OMNI_FRONTEND_ORIGIN"])" -ForegroundColor Green
Write-Host "✅ Updated OMNI_FRONTEND_EXTRA_ORIGINS: $($env2["OMNI_FRONTEND_EXTRA_ORIGINS"])" -ForegroundColor Green

Write-Host "Done. Requests from your domain(s) will now be allowed by FastAPI CORSMiddleware in omni_unified_platform.py." -ForegroundColor Cyan