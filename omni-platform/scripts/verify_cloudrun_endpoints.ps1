Param(
  [Parameter(Mandatory=$false)] [string]$ServiceUrl,
  [Parameter(Mandatory=$false)] [string]$ProjectId,
  [Parameter(Mandatory=$false)] [string]$Region = "europe-west1",
  [Parameter(Mandatory=$false)] [string]$ServiceName = "omni-dashboard"
)

function Write-Status { param([string]$Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-OK { param([string]$Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-FAIL { param([string]$Message) Write-Host "[FAIL] $Message" -ForegroundColor Red }
function Write-Warn { param([string]$Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }

$passCount = 0
$failCount = 0

Write-Status "Starting Cloud Run endpoint verification"

# gcloud presence
try { $v = & gcloud --version 2>&1; if ($LASTEXITCODE -ne 0) { throw "gcloud not found" } } catch { Write-Warn "gcloud not found or not in PATH. Scheduler/Service env checks will be skipped." }

# Optionally set project/region
if ($ProjectId) {
  Write-Status "Setting gcloud project and region..."
  & gcloud config set project $ProjectId | Out-Null
  & gcloud config set run/region $Region | Out-Null
}

# Derive ServiceUrl if not provided
if (-not $ServiceUrl) {
  if ($ProjectId) {
    try {
      $ServiceUrl = (& gcloud run services describe $ServiceName --region $Region --format "value(status.url)").Trim()
      Write-Status "Discovered Service URL: $ServiceUrl"
    } catch {
      Write-FAIL "Failed to discover Service URL. Provide -ServiceUrl explicitly."
      exit 1
    }
  } else {
    Write-FAIL "ServiceUrl not provided and ProjectId is empty. Provide -ServiceUrl."
    exit 1
  }
}

# Show Cloud Run env vars (if gcloud available)
try {
  $svc = & gcloud run services describe $ServiceName --region $Region --format json
  if ($LASTEXITCODE -eq 0 -and $svc) {
    $svcObj = $svc | ConvertFrom-Json
    $envVars = $svcObj.spec.template.spec.containers[0].env
    $gm = ($envVars | Where-Object { $_.name -eq 'GEMINI_MODEL' }).value
    $gr = ($envVars | Where-Object { $_.name -eq 'GOOGLE_CLOUD_REGION' }).value
    Write-Status "Cloud Run Env: GEMINI_MODEL=$gm, GOOGLE_CLOUD_REGION=$gr"
  }
} catch { Write-Warn "Could not read Cloud Run env vars: $($_.Exception.Message)" }

# Helper to run a test safely
function Test-GET {
  param([string]$Url)
  try { $resp = Invoke-RestMethod -Uri $Url -Method GET -TimeoutSec 30; return @{ ok=$true; data=$resp } }
  catch { return @{ ok=$false; err=$_.Exception.Message } }
}

function Test-POST {
  param([string]$Url, [object]$Body)
  try { $resp = Invoke-RestMethod -Uri $Url -Method POST -ContentType 'application/json' -Body ($Body | ConvertTo-Json -Depth 5) -TimeoutSec 60; return @{ ok=$true; data=$resp } }
  catch { return @{ ok=$false; err=$_.Exception.Message } }
}

# 1) /readyz
Write-Status "Testing GET /readyz"
$r1 = Test-GET "$ServiceUrl/readyz"
if ($r1.ok) { Write-OK "/readyz OK"; $passCount++ } else { Write-FAIL "/readyz FAILED: $($r1.err)"; $failCount++ }

# 2) POST /api/gemini/generate
Write-Status "Testing POST /api/gemini/generate"
$genBody = @{ prompt = "Verification ping"; model = "gemini-2.0-flash" }
$r2 = Test-POST "$ServiceUrl/api/gemini/generate" $genBody
if ($r2.ok -and $r2.data.ok) { Write-OK "/api/gemini/generate OK (model=$($r2.data.model))"; $passCount++ } else { Write-Warn "Primary generate failed: $($r2.err). Trying fallback /api/gcp/gemini..."; $r2b = Test-POST "$ServiceUrl/api/gcp/gemini" $genBody; if ($r2b.ok) { Write-OK "Fallback /api/gcp/gemini OK"; $passCount++ } else { Write-FAIL "Generate and fallback failed: $($r2b.err)"; $failCount++ } }

# 3) POST /api/gemini/query
Write-Status "Testing POST /api/gemini/query"
$qBody = @{ prompt = "Hello from verification"; model = "gemini-2.0-flash" }
$r3 = Test-POST "$ServiceUrl/api/gemini/query" $qBody
if ($r3.ok -and $r3.data.ok) { Write-OK "/api/gemini/query OK (model=$($r3.data.model))"; $passCount++ } else { Write-Warn "Query failed: $($r3.err)"; $failCount++ }

# 4) POST /api/gemini/structured
Write-Status "Testing POST /api/gemini/structured"
$sBody = @{ prompt = "Return JSON {title:string, items:string[]} for 'Verification checklist'"; model = "gemini-2.0-flash" }
$r4 = Test-POST "$ServiceUrl/api/gemini/structured" $sBody
if ($r4.ok -and $r4.data.ok) {
  $data = $r4.data.data
  $title = $data.title
  $items = $data.items
  if ($title -and $items) { Write-OK "/api/gemini/structured OK (title=$title, items=$($items.Count))"; $passCount++ }
  else { Write-Warn "/api/gemini/structured returned unexpected shape"; $passCount++ }
} else { Write-Warn "Structured failed: $($r4.err)"; $failCount++ }

# 5) GET /api/gemini/cron
Write-Status "Testing GET /api/gemini/cron"
$r5 = Test-GET "$ServiceUrl/api/gemini/cron"
if ($r5.ok) { Write-OK "/api/gemini/cron OK"; $passCount++ } else { Write-Warn "/api/gemini/cron failed: $($r5.err)"; $failCount++ }

# 6) Cloud Scheduler jobs existence
if ($ProjectId) {
  Write-Status "Checking Cloud Scheduler jobs in $Region"
  try {
    $jobs = & gcloud scheduler jobs list --location $Region --format json
    $jobsObj = $null
    if ($LASTEXITCODE -eq 0 -and $jobs) { $jobsObj = $jobs | ConvertFrom-Json }
    $names = @("omni-dashboard-heartbeat", "omni-dashboard-gemini-selftest", "omni-dashboard-gemini-cron")
    foreach ($n in $names) {
      $exists = $false
      if ($jobsObj) { $exists = ($jobsObj | Where-Object { $_.name -match "/jobs/$n$" }) -ne $null }
      if ($exists) { Write-OK "Scheduler job exists: $n"; $passCount++ } else { Write-Warn "Scheduler job missing: $n" }
    }
  } catch { Write-Warn "Could not list scheduler jobs: $($_.Exception.Message)" }
}

Write-Host ""; Write-Status "Verification summary: PASS=$passCount, FAIL=$failCount"
if ($failCount -gt 0) { Write-Warn "Some checks failed. Review messages above." } else { Write-OK "All checks passed" }