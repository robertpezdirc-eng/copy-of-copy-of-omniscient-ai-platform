# Observability Smoke Test for Omni Platform
param(
  [string]$PrometheusUrl = $(if ($env:PROMETHEUS_URL) { $env:PROMETHEUS_URL } else { 'http://localhost:9091' }),
  [string]$AlertmanagerUrl = $(if ($env:ALERTMANAGER_URL) { $env:ALERTMANAGER_URL } else { 'http://localhost:9093' })
)

Write-Host "[info] Prometheus URL: $PrometheusUrl"
Write-Host "[info] Alertmanager URL: $AlertmanagerUrl"

# Ensure URL encoding support
[void][System.Reflection.Assembly]::LoadWithPartialName('System.Web')

function Invoke-PromQL {
  param([Parameter(Mandatory=$true)][string]$Query)
  $encoded = [System.Web.HttpUtility]::UrlEncode($Query)
  $url = "$PrometheusUrl/api/v1/query?query=$encoded"
  try {
    return Invoke-RestMethod -Uri $url -Method GET -UseBasicParsing -TimeoutSec 10
  } catch {
    Write-Host "[error] Prometheus query failed: $Query" -ForegroundColor Red
    throw
  }
}

function Test-Http200 {
  param([Parameter(Mandatory=$true)][string]$Url, [string]$Name = $Url)
  try {
    $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -Method GET -TimeoutSec 10
    if ($resp.StatusCode -eq 200) {
      Write-Host "[ok] $Name is ready" -ForegroundColor Green
      return $true
    }
  } catch {
    Write-Host "[warn] $Name not ready: $_" -ForegroundColor Yellow
  }
  return $false
}

$overallOk = $true

# Reload Prometheus rules/config (requires --web.enable-lifecycle)
try {
  Write-Host "[info] Reloading Prometheus configuration" -ForegroundColor Cyan
  Invoke-WebRequest -Uri "$PrometheusUrl/-/reload" -Method POST -UseBasicParsing -TimeoutSec 10 | Out-Null
  Start-Sleep -Seconds 1
} catch {
  Write-Host "[warn] Prometheus reload endpoint failed or disabled: $_" -ForegroundColor Yellow
}

# Readiness checks
$pReady = Test-Http200 -Url "$PrometheusUrl/-/ready" -Name "Prometheus readiness"
if (-not $pReady) { $overallOk = $false }

# Target availability
Write-Host "[info] Checking targets up by job" -ForegroundColor Cyan
$upResp = Invoke-PromQL -Query 'sum by (job) (up)'
if ($upResp.status -ne 'success') {
  Write-Host "[error] Query failed: sum by(job)(up)" -ForegroundColor Red
  exit 2
}

$expectedJobs = @('prometheus','alertmanager','loki','tempo','promtail')
$upByJob = @{}
foreach ($r in $upResp.data.result) {
  $job = $r.metric.job
  $val = [double]$r.value[1]
  $upByJob[$job] = $val
}

foreach ($j in $expectedJobs) {
  if ($upByJob.ContainsKey($j) -and $upByJob[$j] -gt 0) {
    Write-Host "[ok] $j up = $($upByJob[$j])" -ForegroundColor Green
  } else {
    Write-Host "[error] $j appears DOWN (no up metrics)" -ForegroundColor Red
    $overallOk = $false
  }
}

# Ingestion and drops telemetry
Write-Host "[info] Checking ingestion/drop rates" -ForegroundColor Cyan
$queries = @{
  'loki_rate'     = 'rate(loki_distributor_lines_received_total[5m])';
  'tempo_rate'    = 'rate(tempo_distributor_spans_received_total[5m])';
  'promtail_drop' = 'rate(promtail_dropped_entries_total[5m])';
}

foreach ($name in $queries.Keys) {
  $q = $queries[$name]
  $resp = Invoke-PromQL -Query $q
  if ($resp.status -ne 'success') {
    Write-Host "[warn] Query failed: $q" -ForegroundColor Yellow
    continue
  }
  $sum = 0.0
  foreach ($r in $resp.data.result) { $sum += [double]$r.value[1] }
  Write-Host ("[metric] {0} = {1}" -f $name, ([string]::Format('{0:0.####}', $sum)))
}

if ($overallOk) {
  Write-Host "[result] Smoke test PASSED" -ForegroundColor Green
  exit 0
} else {
  Write-Host "[result] Smoke test FAILED" -ForegroundColor Red
  exit 1
}