#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Post-deploy health check for Vercel site

.DESCRIPTION
  Verifies /api/health and /live page. Optionally upserts demo metrics via /api/metrics/upsert.

.PARAMETER Url
  Base URL of deployed Vercel site, e.g. https://your-app.vercel.app

.PARAMETER SeedDemo
  If true, seeds metrics for finance/analytics via API.

.EXAMPLE
  .\scripts\health-check.ps1 -Url https://your-app.vercel.app -SeedDemo $true
#>

param(
  [Parameter(Mandatory=$true)] [string]$Url,
  [Parameter(Mandatory=$false)] [bool]$SeedDemo = $false
)

function Write-Ok($msg) { Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Fail($msg) { Write-Host "❌ $msg" -ForegroundColor Red }
function Write-Info($msg) { Write-Host "ℹ️  $msg" -ForegroundColor Cyan }

Write-Info "Checking $Url"

try {
  $h = Invoke-WebRequest -Uri "$Url/api/health" -UseBasicParsing -TimeoutSec 20
  if ($h.StatusCode -eq 200) { Write-Ok "/api/health OK" } else { Write-Fail "/api/health status $($h.StatusCode)" }
} catch { Write-Fail "/api/health error: $($_.Exception.Message)" }

try {
  $live = Invoke-WebRequest -Uri "$Url/live" -UseBasicParsing -TimeoutSec 20
  if ($live.StatusCode -eq 200) { Write-Ok "/live page OK" } else { Write-Fail "/live status $($live.StatusCode)" }
} catch { Write-Fail "/live error: $($_.Exception.Message)" }

if ($SeedDemo) {
  Write-Info "Seeding demo metrics via /api/metrics/upsert"
  $payloads = @(
    @{ module = "finance"; entry = @{ ts = [DateTime]::UtcNow.ToString("o"); revenue = 120000; expenses = 45000 } },
    @{ module = "analytics"; entry = @{ ts = [DateTime]::UtcNow.ToString("o"); visitors = 10234; conversion = 3.4 } }
  )
  foreach ($p in $payloads) {
    try {
      $json = ($p | ConvertTo-Json -Depth 4)
      $res = Invoke-WebRequest -Uri "$Url/api/metrics/upsert" -Method Post -ContentType "application/json" -Body $json -UseBasicParsing
      if ($res.StatusCode -eq 200) { Write-Ok "Seeded $($p.module)" } else { Write-Fail "Seed $($p.module) status $($res.StatusCode)" }
    } catch { Write-Fail "Seed $($p.module) error: $($_.Exception.Message)" }
  }
}

Write-Host "Done." -ForegroundColor Gray