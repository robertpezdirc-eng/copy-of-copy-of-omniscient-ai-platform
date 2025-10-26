param(
  [string]$ProjectId = "refined-graph-471712-n9",
  [string]$Region = "europe-west1",
  [string]$RuntimeSa = $("omni-deployer@" + "refined-graph-471712-n9" + ".iam.gserviceaccount.com"),
  [switch]$PublicFrontend
)

$ErrorActionPreference = "Stop"

function Exec($cmd) {
  Write-Host "> $cmd" -ForegroundColor Cyan
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = "powershell"
  $psi.Arguments = "-NoProfile -NonInteractive -Command `"$cmd`""
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.UseShellExecute = $false
  $p = [System.Diagnostics.Process]::Start($psi)
  $out = $p.StandardOutput.ReadToEnd()
  $err = $p.StandardError.ReadToEnd()
  $p.WaitForExit()
  if ($out.Trim()) { Write-Host $out }
  if ($err.Trim()) { Write-Host $err -ForegroundColor Yellow }
  if ($p.ExitCode -ne 0) { throw "Command failed ($($p.ExitCode)): $cmd`n$err" }
}

Write-Host "==> Active gcloud accounts" -ForegroundColor Green
Exec 'gcloud auth list'

Write-Host "==> Selecting project $ProjectId" -ForegroundColor Green
Exec "gcloud config set project $ProjectId"

Write-Host "==> Enabling required APIs" -ForegroundColor Green
Exec "gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com aiplatform.googleapis.com"

Write-Host "==> Pre-deploy: Vertex/Gemini connectivity + IAM check" -ForegroundColor Green
$checkScript = Join-Path $PSScriptRoot 'scripts\vertex_connectivity_check.ps1'
& $checkScript -ProjectId $ProjectId -Region 'us-central1' -RunRegion $Region -ServiceName 'omni-backend' -PromptFix
if ($LASTEXITCODE -ne 0) { Write-Host "Pre-deploy check failed (code $LASTEXITCODE). Aborting." -ForegroundColor Red; exit $LASTEXITCODE }

Write-Host "==> Ensuring Artifact Registry repo 'omni' exists in $Region" -ForegroundColor Green
try {
  Exec "gcloud artifacts repositories describe omni --location=$Region"
  Write-Host "Repo 'omni' already exists." -ForegroundColor DarkGray
} catch {
  Exec "gcloud artifacts repositories create omni --repository-format=docker --location=$Region --description='Omni images'"
}

Write-Host "==> Ensuring Secret Manager secrets exist" -ForegroundColor Green
$secrets = @('openai-api-key','gemini-api-key','google-api-key')
foreach ($s in $secrets) {
  try {
    Exec "gcloud secrets describe $s"
    Write-Host "Secret $s exists." -ForegroundColor DarkGray
  } catch {
    Exec "gcloud secrets create $s --replication-policy=automatic"
  }
}

Write-Host "==> Ensuring secret versions (if env vars set)" -ForegroundColor Green
if ($env:OPENAI_API_KEY) { $env:OPENAI_API_KEY | Out-File -FilePath "$env:TEMP\openai.tmp" -Encoding ascii; Exec "gcloud secrets versions add openai-api-key --data-file=$env:TEMP/openai.tmp" } else { Write-Host "OPENAI_API_KEY env var not set; skipping version add" -ForegroundColor DarkGray }
if ($env:GEMINI_API_KEY) { $env:GEMINI_API_KEY | Out-File -FilePath "$env:TEMP\gemini.tmp" -Encoding ascii; Exec "gcloud secrets versions add gemini-api-key --data-file=$env:TEMP/gemini.tmp" } else { Write-Host "GEMINI_API_KEY env var not set; skipping version add" -ForegroundColor DarkGray }
if ($env:GOOGLE_API_KEY) { $env:GOOGLE_API_KEY | Out-File -FilePath "$env:TEMP\google.tmp" -Encoding ascii; Exec "gcloud secrets versions add google-api-key --data-file=$env:TEMP/google.tmp" } else { Write-Host "GOOGLE_API_KEY env var not set; skipping version add" -ForegroundColor DarkGray }

Write-Host "==> Granting IAM roles (requires Owner)" -ForegroundColor Green
$DeploySa = "omni-runner@$ProjectId.iam.gserviceaccount.com"
$roles = @(
  'roles/serviceusage.serviceUsageAdmin',
  'roles/run.admin',
  'roles/iam.serviceAccountUser',
  'roles/artifactregistry.writer',
  'roles/cloudbuild.builds.editor',
  'roles/secretmanager.secretAccessor'
)
foreach ($r in $roles) { Exec "gcloud projects add-iam-policy-binding $ProjectId --member serviceAccount:$DeploySa --role $r" }

# Runtime permissions
try {
  Exec "gcloud projects add-iam-policy-binding $ProjectId --member serviceAccount:$RuntimeSa --role roles/secretmanager.secretAccessor"
} catch {}

$ProjectNumber = (& gcloud projects describe $ProjectId --format="value(projectNumber)").Trim()
$ServerlessRobot = "service-$ProjectNumber@serverless-robot-prod.iam.gserviceaccount.com"
try { Exec "gcloud projects add-iam-policy-binding $ProjectId --member serviceAccount:$ServerlessRobot --role roles/artifactregistry.reader" } catch {}

Write-Host "==> Submitting Cloud Build (cloudbuild.dual.yaml)" -ForegroundColor Green
Exec "gcloud builds submit --config cloudbuild.dual.yaml --substitutions=_ENV=prod,_REGION=$Region,_RUNTIME_SA=$RuntimeSa ."

Write-Host "==> Fetching Cloud Run URLs" -ForegroundColor Green
try { Exec "gcloud run services describe omni-backend --region $Region --format=value(status.url)" } catch {}
try { Exec "gcloud run services describe omni-frontend --region $Region --format=value(status.url)" } catch {}

if ($PublicFrontend) {
  Write-Host "==> Allowing public access to omni-frontend" -ForegroundColor Green
  try { Exec "gcloud run services add-iam-policy-binding omni-frontend --region $Region --member=allUsers --role=roles/run.invoker" } catch {}
}

Write-Host "✅ Done. If any step failed with permission errors, run this script with an Owner account." -ForegroundColor Green