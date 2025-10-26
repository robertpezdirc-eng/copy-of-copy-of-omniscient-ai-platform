# Alertmanager Health Check Script
# Posts a test alert and inspects Alertmanager logs for delivery errors.
param(
  [string]$Severity = "critical",
  [string]$Service = "omni-unified",
  [string]$AlertName = "HealthCheckTest",
  [string]$Instance = "localhost",
  [int]$LogWindowSeconds = 120,
  [switch]$CheckMockSlack,
  [string]$MockSlackLogPath = "logs/mock_slack.log"
)

$ErrorActionPreference = "Stop"

function Post-TestAlert {
  $now = Get-Date
  $labels = @{ alertname = $AlertName; service = $Service; severity = $Severity; instance = $Instance }
  $annotations = @{ summary = "Automated health-check alert"; description = "This is a test to verify routing and delivery." }
  $payloadObj = @(
    @{ labels = $labels; annotations = $annotations; startsAt = $now.ToString("o") }
  )
  $payload = (ConvertTo-Json $payloadObj)
  Write-Host "Posting test alert to Alertmanager v2 API..."
  try {
    $resp = Invoke-WebRequest -Uri "http://localhost:9093/api/v2/alerts" -Method Post -ContentType "application/json" -Body $payload -TimeoutSec 30
    return $resp.StatusCode
  } catch {
    Write-Warning "Failed to post alert: $($_.Exception.Message)"
    return -1
  }
}

function Get-AlertmanagerLogs {
  param([int]$SinceSeconds)
  try {
    $since = "$SinceSeconds" + "s"
    $logs = & cmd /c "docker logs alertmanager --since $since" 2>&1
    return $logs
  } catch {
    Write-Warning "Failed to read alertmanager logs: $($_.Exception.Message)"
    return ""
  }
}

function Check-ContainerUp {
  try {
    $ps = docker ps --format "{{.Names}}|{{.Status}}" | Select-String -Pattern "^alertmanager\|"
    return ($ps -ne $null)
  } catch {
    return $false
  }
}

function Summarize-Logs {
  param([string]$logs)
  $summary = [ordered]@{}
  $summary["errors"] = @()
  $summary["warnings"] = @()
  $summary["info"] = @()

  if (!$logs) { return $summary }

  $errorPatterns = @("error", "ERROR", "channel_not_found", "invalid", "yaml:")
  $warnPatterns = @("warn", "WARN", "535 5.7.8")
  $infoPatterns = @("Listening on", "Loading configuration file", "notify", "Starting Alertmanager")

  foreach ($line in $logs.Split([Environment]::NewLine)) {
    foreach ($p in $errorPatterns) { if ($line -match $p) { $summary["errors"] += $line; break } }
    foreach ($p in $warnPatterns) { if ($line -match $p) { $summary["warnings"] += $line; break } }
    foreach ($p in $infoPatterns) { if ($line -match $p) { $summary["info"] += $line; break } }
  }
  return $summary
}

function Check-MockSlackLog {
  param([string]$alertName, [string]$logPath)
  if (-not (Test-Path $logPath)) { return $false }
  try {
    $content = Get-Content -Path $logPath -ErrorAction Stop
    foreach ($line in $content) {
      if ($line -match [Regex]::Escape($alertName)) { return $true }
    }
    return $false
  } catch {
    return $false
  }
}

function Check-MockSlackDockerLogs {
  param([string]$alertName, [int]$sinceSeconds)
  try {
    $since = "$sinceSeconds" + "s"
    $logs = & cmd /c "docker logs mock-slack --since $since" 2>&1
    foreach ($line in $logs.Split([Environment]::NewLine)) {
      if ($line -match [Regex]::Escape($alertName)) { return $true }
    }
    return $false
  } catch {
    return $false
  }
}

# Main
Write-Host "=== Alertmanager Health Check ==="
$up = Check-ContainerUp
if (-not $up) {
  Write-Warning "Alertmanager container is not running. Please start it with: docker compose up -d alertmanager"
}

$code = Post-TestAlert
# Wait long enough to pass typical Alertmanager group_wait (30s)
$initialWait = 5
if ($CheckMockSlack) { $initialWait = 35 }
Start-Sleep -Seconds $initialWait
$logs = Get-AlertmanagerLogs -SinceSeconds $LogWindowSeconds
$sum = Summarize-Logs -logs $logs

Write-Host "HTTP status code: $code"
Write-Host "Errors found: $($sum.errors.Count)"; if ($sum.errors.Count) { $sum.errors | ForEach-Object { Write-Host "  ERR: $_" } }
Write-Host "Warnings found: $($sum.warnings.Count)"; if ($sum.warnings.Count) { $sum.warnings | ForEach-Object { Write-Host "  WARN: $_" } }
Write-Host "Info lines: $($sum.info.Count)"; if ($sum.info.Count) { $sum.info | ForEach-Object { Write-Host "  INFO: $_" } }

if ($CheckMockSlack) {
  $mockOkFile = Check-MockSlackLog -alertName $AlertName -logPath $MockSlackLogPath
  $mockOkDocker = Check-MockSlackDockerLogs -alertName $AlertName -sinceSeconds $LogWindowSeconds
  Write-Host "Mock Slack received (file): $mockOkFile"
  Write-Host "Mock Slack received (docker logs): $mockOkDocker"
  $mockOk = $mockOkFile -or $mockOkDocker
  Write-Host "Mock Slack received alert '$AlertName': $mockOk"
}

if ($code -eq 200 -and $sum.errors.Count -eq 0 -and (!$CheckMockSlack -or $mockOk)) {
  Write-Host "Health check looks OK: Alert posted in Alertmanager brez napak." 
  if ($CheckMockSlack) { Write-Host "Mock Slack dostava potrjena." }
  exit 0
} else {
  Write-Warning "Health check kaže težave. Preglejte izpis zgoraj."
  exit 1
}