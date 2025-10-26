#requires -Version 5.1
param(
  [string]$PROJECT_ID = $env:PROJECT_ID
    ? $env:PROJECT_ID
    : 'refined-graph-471712-n9',
  [string]$REGION = $env:REGION
    ? $env:REGION
    : 'europe-west1',
  [string]$AR_REPO = 'omni'
)

$ErrorActionPreference = 'Stop'

function Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Run($cmd) { Write-Host "> $cmd" -ForegroundColor Green; iex $cmd }

$AR_HOST = "$REGION-docker.pkg.dev"
Info "Uporabljam PROJECT_ID=$PROJECT_ID, REGION=$REGION"

# 1) Poenoti regijo
Info "Poenotenje regije za Cloud Run"
Run "gcloud config set run/region $REGION"
Warn "Za Cloud Build uporabi --region $REGION v ukazih in triggerjih (ni globalne builds/location)."

# 2) Artifact Registry (opcijsko)
Info "Konfiguracija Artifact Registry Docker avtentikacije"
Run "gcloud auth configure-docker $AR_HOST --quiet"

Info "Ustvarjanje AR repozitorija, če ne obstaja"
$repoExists = $false
try {
  & gcloud artifacts repositories describe $AR_REPO --location=$REGION | Out-Null
  if ($LASTEXITCODE -eq 0) { $repoExists = $true }
} catch { $repoExists = $false }

if (-not $repoExists) {
  Run "gcloud artifacts repositories create $AR_REPO --repository-format=docker --location=$REGION --description 'Omni platform images'"
} else {
  Info "AR repozitorij $AR_REPO že obstaja v $REGION"
}

# 3) Cloud Build YAML (če obstaja)
$cb = Join-Path (Get-Location) 'cloudbuild.missing-services.yaml'
if (Test-Path $cb) {
  Info "Posodobitev image URL-jev v cloudbuild.missing-services.yaml (GCR -> AR)"
  $content = Get-Content $cb -Raw
  $pattern = "gcr.io/$PROJECT_ID"
  $replacement = "$AR_HOST/$PROJECT_ID/$AR_REPO"
  $newContent = $content -replace [Regex]::Escape($pattern), [Regex]::Escape($replacement)
  Set-Content -Path $cb -Value $newContent -Encoding UTF8
  Copy-Item $cb "$cb.bak" -Force
  Info "Backup: cloudbuild.missing-services.yaml.bak"
} else {
  Warn "Datoteka cloudbuild.missing-services.yaml ne obstaja. Preskakujem zamenjavo GCR referenc."
}

# 4) Min instances in concurrency (le, če storitve obstajajo)
function Update-Run($svc, $args) {
  try {
    & gcloud run services describe $svc --region $REGION | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Not found" }
    Info "Posodobitev storitve $svc: $args"
    Run "gcloud run services update $svc $args --region $REGION"
  } catch {
    Warn "Storitev $svc ni najdena v $REGION. Preskakujem posodobitev."
  }
}

Update-Run 'omni-api-gateway' '--min-instances 1 --concurrency 80'
Update-Run 'omni-singularity' '--min-instances 1 --concurrency 40'

# 5) Secret Manager (primer za OPENAI_API_KEY)
Info "Ustvarjanje OPENAI_API_KEY v Secret Manager (če še ne obstaja)"
$secretExists = $false
try {
  & gcloud secrets describe OPENAI_API_KEY | Out-Null
  if ($LASTEXITCODE -eq 0) { $secretExists = $true }
} catch { $secretExists = $false }

if (-not $secretExists) {
  if ($env:OPENAI_API_KEY) {
    $tmp = New-TemporaryFile
    Set-Content -Path $tmp -Value $env:OPENAI_API_KEY -Encoding UTF8 -NoNewline
    Run "gcloud secrets create OPENAI_API_KEY --data-file='$tmp' --replication-policy=automatic"
    Remove-Item $tmp -Force
  } else {
    Warn "OPENAI_API_KEY ni podan v okolju. Preskakujem ustvarjanje. Uporabi: \n  setx OPENAI_API_KEY 'VALUE' (Windows) ali export v bash, nato ponovno zaženi skripto."
  }
} else {
  Info "Skrivnost OPENAI_API_KEY že obstaja"
}

# Povezava skrivnosti na storitev (primer omni-api)
try {
  & gcloud run services describe omni-api --region $REGION | Out-Null
  if ($LASTEXITCODE -eq 0) {
    Info "Povezava skrivnosti OPENAI_API_KEY na omni-api"
    Run "gcloud run services update omni-api --set-secrets \"OPENAI_API_KEY=projects/$PROJECT_ID/secrets/OPENAI_API_KEY:latest\" --region $REGION"
  } else {
    throw "not found"
  }
} catch {
  Warn "Storitev omni-api ni najdena v $REGION. Preskakujem --set-secrets."
}

# 6) Health endpoint preverba
$HEALTH_URL = 'https://omni-api-gateway-guzjyv6gfa-ew.a.run.app/healthz'
Info "Preverjam health endpoint: $HEALTH_URL"
try {
  $resp = Invoke-WebRequest -Uri $HEALTH_URL -Method Head -ErrorAction Stop
  if ($resp.StatusCode -eq 200) {
    Info "Health endpoint vrne 200 OK"
  } else {
    Warn "Health endpoint vrne $($resp.StatusCode). Dodaj handler v FastAPI/Express: GET /healthz -> {status: 'ok'}"
  }
} catch {
  Warn "Health endpoint ni dosegljiv ali vrača napako. Dodaj handler v storitev in ponovno preveri."
}

# 7) Domain mapping (opcijsko)
Info "Domain mapping je opcijski. Primer ukaza:"
Write-Host "gcloud run domain-mappings create --region $REGION --service omni-api-gateway --domain api.omni-platform.ai --certificate-mode managed"

Info "Končano. Uporabi Cloud Build z regijo:"
Write-Host "gcloud builds submit --config cloudbuild.missing-services.yaml --region $REGION --project $PROJECT_ID"