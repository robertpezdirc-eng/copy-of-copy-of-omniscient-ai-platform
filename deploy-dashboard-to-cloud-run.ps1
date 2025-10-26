# OMNI Platform Dashboard - Google Cloud Run Deployment Script (PowerShell)
param(
  [Parameter(Mandatory=$true)][string]$ProjectId,
  [string]$Region = "europe-west1",
  [string]$ServiceName = "markec-dashboard",
  [string]$RepoName = "omni-repo",
  [hashtable]$EnvVars
)

function Write-Info($msg){ Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Ok($msg){ Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Warn($msg){ Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg){ Write-Host "[ERR]  $msg" -ForegroundColor Red }

# 1) Preconditions
Write-Info "Checking gcloud CLI..."
$gcloud = Get-Command gcloud -ErrorAction SilentlyContinue
if (-not $gcloud) { Write-Err "gcloud not found. Install Google Cloud SDK and re-run."; exit 1 }

Write-Info "Checking authentication..."
$acct = (& gcloud auth list --filter=status:ACTIVE --format="value(account)")
if (-not $acct) { Write-Err "No active account. Run: gcloud auth login"; exit 1 }
Write-Ok "Active account: $acct"

# 2) Project + APIs
Write-Info "Setting project: $ProjectId"
& gcloud config set project $ProjectId | Out-Null
Write-Info "Enabling required APIs..."
& gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com | Out-Null
Write-Ok "APIs enabled"

# 3) Ensure Artifact Registry repository exists
Write-Info "Ensuring Artifact Registry repo '$RepoName' in $Region"
$repoExists = (& gcloud artifacts repositories describe $RepoName --location $Region --format="value(name)" 2>$null)
if (-not $repoExists) {
  Write-Info "Creating Artifact Registry repo..."
  & gcloud artifacts repositories create $RepoName --repository-format=docker --location $Region --description "Omni images" | Out-Null
  Write-Ok "Repository created"
} else {
  Write-Ok "Repository exists"
}

# 4) Build & push image from local Dockerfile
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$imageTag = "$Region-docker.pkg.dev/$ProjectId/$RepoName/$ServiceName:$timestamp"
Write-Info "Building image: $imageTag"
& gcloud builds submit --tag $imageTag .
if ($LASTEXITCODE -ne 0) { Write-Err "Cloud Build failed"; exit 1 }
Write-Ok "Image built and pushed"

# 5) Deploy to Cloud Run
$envArg = $null
if ($EnvVars) {
  $pairs = @()
  foreach ($k in $EnvVars.Keys) { $pairs += "$k=$($EnvVars[$k])" }
  $envArg = "--update-env-vars " + ($pairs -join ",")
  Write-Info "Using env: $($pairs -join ", ")"
}

$deployCmd = "gcloud run deploy $ServiceName --image $imageTag --region $Region --platform managed --allow-unauthenticated --port 8080 --memory 1Gi --cpu 1 --max-instances 3 --ingress all"
if ($envArg) { $deployCmd += " " + $envArg }

Write-Info "Deploying service '$ServiceName'..."
Invoke-Expression $deployCmd
if ($LASTEXITCODE -ne 0) { Write-Err "Deploy failed"; exit 1 }

# 6) Show service URL + health check
$svcUrl = (& gcloud run services describe $ServiceName --region $Region --format "value(status.url)")
Write-Ok "Service URL: $svcUrl"
Write-Info "Health check: $svcUrl/api/health"
try {
  $resp = Invoke-WebRequest -Uri "$svcUrl/api/health" -UseBasicParsing -Method GET -TimeoutSec 20
  Write-Ok "Health: $($resp.StatusCode)"
} catch {
  Write-Warn "Health check failed: $($_.Exception.Message)"
}

Write-Ok "Done."