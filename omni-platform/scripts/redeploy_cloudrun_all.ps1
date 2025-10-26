Param(
  [Parameter(Mandatory=$true)] [string]$ProjectId,
  [Parameter(Mandatory=$false)] [string]$Region = "europe-west1",
  [Parameter(Mandatory=$false)] [string]$ServiceName = "omni-dashboard",
  [Parameter(Mandatory=$false)] [switch]$SkipSchedulerJobs,
  [Parameter(Mandatory=$false)] [switch]$CreateCronJob,
  [Parameter(Mandatory=$false)] [switch]$UseOpenAISecret,
  [Parameter(Mandatory=$false)] [string]$OpenAISecretName = "openai-api-key"
)

function Write-Status { param([string]$Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Success { param([string]$Message) Write-Host "[SUCCESS] $Message" -ForegroundColor Green }
function Write-Warning2 { param([string]$Message) Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Error2 { param([string]$Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

Write-Status "Starting one-click Cloud Run redeploy for Omni Dashboard"

# 1) Prerequisites: gcloud
try {
  $gcloudVersion = & gcloud --version 2>&1
  if ($LASTEXITCODE -ne 0) { throw "gcloud not found" }
  Write-Success "gcloud found"
} catch {
  Write-Error2 "gcloud SDK ni nameščen ali ni v PATH. Namestite https://cloud.google.com/sdk/docs/install in poskusite znova."
  exit 1
}

# 2) Set project & region
Write-Status "Setting gcloud project and region..."
& gcloud config set project $ProjectId | Out-Null
& gcloud config set run/region $Region | Out-Null
Write-Success "Project=$ProjectId, Region=$Region"

# 3) Enable required services
Write-Status "Enabling required services (Cloud Run, Cloud Build, Container Registry, Vertex AI, Secret Manager)..."
& gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com aiplatform.googleapis.com secretmanager.googleapis.com pubsub.googleapis.com cloudtasks.googleapis.com iam.googleapis.com | Out-Null
Write-Success "Services enabled"

# Orchestration resource provisioning: Pub/Sub, Cloud Tasks, Service Account
Write-Status "Provisioning Pub/Sub topic/subscription and Cloud Tasks queue for orchestration..."
$topicName = "omni-workflows"
$subName = "omni-workflows-default"
$queueName = "omni-dispatch"

# Pub/Sub Topic
$topicCheck = (& gcloud pubsub topics describe $topicName --format "value(name)" 2>$null)
if (-not $topicCheck) {
  Write-Status "Creating Pub/Sub topic: $topicName"
  & gcloud pubsub topics create $topicName | Out-Null
} else { Write-Status "Pub/Sub topic exists: $topicName" }

# Pub/Sub Subscription
$subCheck = (& gcloud pubsub subscriptions describe $subName --format "value(name)" 2>$null)
if (-not $subCheck) {
  Write-Status "Creating Pub/Sub subscription: $subName"
  & gcloud pubsub subscriptions create $subName --topic $topicName | Out-Null
} else { Write-Status "Pub/Sub subscription exists: $subName" }

# Cloud Tasks Queue
$queueCheck = (& gcloud tasks queues describe $queueName --location $Region --format "value(name)" 2>$null)
if (-not $queueCheck) {
  Write-Status "Creating Cloud Tasks queue: $queueName in $Region"
  & gcloud tasks queues create $queueName --location $Region | Out-Null
} else { Write-Status "Cloud Tasks queue exists: $queueName" }

# Service Account for Cloud Run (orchestrator)
Write-Status "Ensuring service account 'omni-orchestrator' and IAM roles..."
$saEmail = "omni-orchestrator@$ProjectId.iam.gserviceaccount.com"
$saCheck = (& gcloud iam service-accounts describe $saEmail --format "value(email)" 2>$null)
if (-not $saCheck) {
  & gcloud iam service-accounts create omni-orchestrator --display-name "Omni Orchestrator SA" | Out-Null
  Write-Status "Created service account: $saEmail"
} else { Write-Status "Service account exists: $saEmail" }

# Bind IAM roles needed by orchestrator
& gcloud projects add-iam-policy-binding $ProjectId --member "serviceAccount:$saEmail" --role "roles/pubsub.publisher" | Out-Null
& gcloud projects add-iam-policy-binding $ProjectId --member "serviceAccount:$saEmail" --role "roles/cloudtasks.enqueuer" | Out-Null
& gcloud projects add-iam-policy-binding $ProjectId --member "serviceAccount:$saEmail" --role "roles/secretmanager.secretAccessor" | Out-Null
Write-Success "Orchestration resources ensured"


# 4) Build container image via Cloud Build (tagged)
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$image = "gcr.io/$ProjectId/${ServiceName}:$timestamp"
Write-Status "Building image: $image"
& gcloud builds submit --tag $image
if ($LASTEXITCODE -ne 0) { Write-Error2 "Cloud Build ni uspel"; exit 1 }
Write-Success "Image built and pushed: $image"

# 5) Deploy to Cloud Run (managed) with unified env vars
$envVars = "PROJECT_ID=$ProjectId,GOOGLE_CLOUD_PROJECT=$ProjectId,GOOGLE_CLOUD_REGION=$Region,GEMINI_MODEL=gemini-2.0-flash,ENVIRONMENT=production,OMNI_SYSTEM_CHECKS=false,OMNI_DEBUG_AUTH=true,OMNI_QUIET_CLOUDRUN=true,ORCHESTRATION_ENABLED=1,WORKFLOW_PUBSUB_TOPIC=omni-workflows,DISPATCH_QUEUE=omni-dispatch"

# Optional: inject OPENAI_API_KEY from Secret Manager
$secretFlags = ""
if ($UseOpenAISecret) {
  Write-Status "Checking Secret Manager for '$OpenAISecretName'..."
  $secretExists = (& gcloud secrets describe $OpenAISecretName --format "value(name)" 2>$null)
  if ($LASTEXITCODE -eq 0 -and $secretExists) {
    Write-Success "Secret found: $OpenAISecretName (injecting OPENAI_API_KEY)"
    $secretFlags = "--set-secrets=OPENAI_API_KEY=$OpenAISecretName:latest"
  } else {
    Write-Warning2 "Secret '$OpenAISecretName' not found; skipping --set-secrets"
  }
}

Write-Status "Deploying service '$ServiceName' to Cloud Run..."
& gcloud run deploy $ServiceName --image $image --region $Region --platform managed --allow-unauthenticated --port 8080 --memory 1Gi --cpu 1 --min-instances 1 --max-instances 10 --concurrency 20 --timeout 600 --service-account $saEmail --set-env-vars $envVars $secretFlags
if ($LASTEXITCODE -ne 0) { Write-Error2 "Cloud Run deploy ni uspel"; exit 1 }
Write-Success "Service deployed"

# 6) Get service URL
Write-Status "Retrieving service URL..."
$ServiceUrl = (& gcloud run services describe $ServiceName --region $Region --format "value(status.url)").Trim()
if (-not $ServiceUrl) { Write-Error2 "Ni bilo mogoče pridobiti URL storitve"; exit 1 }
Write-Success "Service URL: $ServiceUrl"

# Update TARGET_URL_BASE env var for Cloud Tasks callbacks
Write-Status "Updating service env var TARGET_URL_BASE=$ServiceUrl"
& gcloud run services update $ServiceName --region $Region --set-env-vars "TARGET_URL_BASE=$ServiceUrl" | Out-Null
Write-Success "TARGET_URL_BASE configured"

# 7) Verify endpoints
Write-Status "Verifying /readyz..."
try {
  $ready = Invoke-RestMethod -Uri "$ServiceUrl/readyz" -Method GET -TimeoutSec 30
  Write-Success "Readyz OK"
} catch {
  Write-Warning2 "Readyz klic ni uspel: $($_.Exception.Message)"
}

Write-Status "Testing Gemini generate endpoint..."
$genBody = @{ prompt = "Ping from redeploy script"; model = "gemini-2.0-flash" } | ConvertTo-Json -Depth 3
try {
  $genResult = Invoke-RestMethod -Uri "$ServiceUrl/api/gemini/generate" -Method POST -ContentType "application/json" -Body $genBody -TimeoutSec 60
  Write-Success "Gemini generate OK"
} catch {
  Write-Warning2 "Gemini generate ni uspel: $($_.Exception.Message). Poskus z /api/gcp/gemini..."
  try {
    $fallbackResult = Invoke-RestMethod -Uri "$ServiceUrl/api/gcp/gemini" -Method POST -ContentType "application/json" -Body $genBody -TimeoutSec 60
    Write-Success "Fallback /api/gcp/gemini OK"
  } catch {
    Write-Warning2 "Fallback ni uspel: $($_.Exception.Message)"
  }
}

# 8) Cloud Scheduler jobs
if (-not $SkipSchedulerJobs) {
  Write-Status "Creating/updating Cloud Scheduler jobs in $Region..."
  # List existing jobs
  $existingJobs = & gcloud scheduler jobs list --location $Region --format json 2>$null
  $existing = @()
  if ($LASTEXITCODE -eq 0 -and $existingJobs) {
    try { $existing = $existingJobs | ConvertFrom-Json } catch { $existing = @() }
  }

  # Helper: check existence
  function JobExists { param([string]$JobName) return ($existing | Where-Object { $_.name -match "/jobs/$JobName$" }) }

  # Heartbeat: GET /readyz every 5 minutes
  $hbName = "omni-dashboard-heartbeat"
  $hbExists = JobExists $hbName
  if ($hbExists) {
    Write-Status "Updating heartbeat job: $hbName"
    & gcloud scheduler jobs update http $hbName --schedule "*/5 * * * *" --location $Region --http-method GET --uri "$ServiceUrl/readyz" | Out-Null
  } else {
    Write-Status "Creating heartbeat job: $hbName"
    & gcloud scheduler jobs create http $hbName --schedule "*/5 * * * *" --location $Region --http-method GET --uri "$ServiceUrl/readyz" | Out-Null
  }

  # Self-test: POST /api/gcp/gemini every 15 minutes
  $stName = "omni-dashboard-gemini-selftest"
  $stExists = JobExists $stName
  $stBody = '{"prompt":"ping","model":"gemini-2.0-flash"}'
  if ($stExists) {
    Write-Status "Updating self-test job: $stName"
    & gcloud scheduler jobs update http $stName --schedule "*/15 * * * *" --location $Region --http-method POST --headers "Content-Type=application/json" --uri "$ServiceUrl/api/gcp/gemini" --message-body $stBody | Out-Null
  } else {
    Write-Status "Creating self-test job: $stName"
    & gcloud scheduler jobs create http $stName --schedule "*/15 * * * *" --location $Region --http-method POST --headers "Content-Type=application/json" --uri "$ServiceUrl/api/gcp/gemini" --message-body $stBody | Out-Null
  }

  # Optional: Cron GET /api/gemini/cron every 10 minutes
  if ($CreateCronJob) {
    $cronName = "omni-dashboard-gemini-cron"
    $cronExists = JobExists $cronName
    if ($cronExists) {
      Write-Status "Updating cron job: $cronName"
      & gcloud scheduler jobs update http $cronName --schedule "*/10 * * * *" --location $Region --http-method GET --uri "$ServiceUrl/api/gemini/cron" | Out-Null
    } else {
      Write-Status "Creating cron job: $cronName"
      & gcloud scheduler jobs create http $cronName --schedule "*/10 * * * *" --location $Region --http-method GET --uri "$ServiceUrl/api/gemini/cron" | Out-Null
    }
  }

  Write-Success "Cloud Scheduler jobs configured"
} else {
  Write-Warning2 "Skipping Cloud Scheduler job creation per parameter"
}

Write-Host ""; Write-Success "Redeploy completed"
Write-Host "Service URL: $ServiceUrl" -ForegroundColor Cyan
Write-Host "API Docs: $ServiceUrl/api/docs" -ForegroundColor Cyan
Write-Host "Readyz: $ServiceUrl/readyz" -ForegroundColor Cyan
Write-Host "Gemini Generate: POST $ServiceUrl/api/gemini/generate" -ForegroundColor Cyan
Write-Host "Gemini Structured: POST $ServiceUrl/api/gemini/structured" -ForegroundColor Cyan
Write-Host "Gemini Cron: GET $ServiceUrl/api/gemini/cron" -ForegroundColor Cyan