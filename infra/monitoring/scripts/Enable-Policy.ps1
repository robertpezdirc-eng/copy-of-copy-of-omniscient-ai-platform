#!/usr/bin/env pwsh
# Requires: gcloud CLI
# Enable one or more Cloud Monitoring alert policies by displayName (exact or regex).
# Usage examples:
#   ./Enable-Policy.ps1 -ProjectId omni-dev-420223 -Filter "Uptime Check Failed"            # regex
#   ./Enable-Policy.ps1 -ProjectId omni-dev-420223 -Filter "OMNI Dashboard - Uptime Check (MQL Multi-Region)" -Exact
#   ./Enable-Policy.ps1 -Filter "^Cloud Run P95 Latency" -Yes                               # uses default gcloud project
#   ./Enable-Policy.ps1 -Filter "Uptime Check Failed" -DryRun

param(
  [string]$ProjectId,
  [Parameter(Mandatory = $true)][string]$Filter,
  [switch]$Exact,
  [switch]$DryRun,
  [switch]$Yes
)

$ErrorActionPreference = 'Stop'

function Get-DefaultProjectId {
  try {
    $pid = (& gcloud config get-value project 2>$null).Trim()
  } catch {
    $pid = ''
  }
  return $pid
}

if (-not $ProjectId) {
  $ProjectId = Get-DefaultProjectId
  if (-not $ProjectId) {
    Write-Error "No --ProjectId provided and no default gcloud project is configured. Run: gcloud config set project <ID>"
    exit 1
  }
}

# Build gcloud filter
if ($Exact) {
  $gcloudFilter = "displayName=\"$Filter\""
} else {
  $gcloudFilter = "displayName ~ \"$Filter\""
}

Write-Host "Project: $ProjectId"
if ($Exact) { Write-Host "Filter (exact): $Filter" } else { Write-Host "Filter (regex): $Filter" }

# Get matching policy IDs
$policyIds = (& gcloud monitoring policies list `
  --project="$ProjectId" `
  --filter="$gcloudFilter" `
  --format='value(name)') | Where-Object { $_ -and $_.Trim() -ne '' }

if (-not $policyIds -or $policyIds.Count -eq 0) {
  Write-Error "No policies matched filter."
  exit 1
}

Write-Host "Matched policies:" -ForegroundColor Cyan
foreach ($pid in $policyIds) {
  & gcloud monitoring policies describe $pid --project="$ProjectId" --format='table(name,displayName,enabled)'
}

if ($DryRun) {
  Write-Host "Dry-run: would enable $($policyIds.Count) policy(ies)."
  exit 0
}

if (-not $Yes) {
  $ans = Read-Host "Enable $($policyIds.Count) policy(ies)? [y/N]"
  if ($ans -notin @('y','Y','yes','YES')) {
    Write-Host "Aborted."
    exit 0
  }
}

foreach ($pid in $policyIds) {
  Write-Host "Enabling $pid ..."
  $json = & gcloud alpha monitoring policies describe $pid --project="$ProjectId" --format=json | ConvertFrom-Json
  $json.enabled = $true
  $tmp = [System.IO.Path]::GetTempFileName()
  $json | ConvertTo-Json -Depth 100 | Set-Content -Path $tmp -Encoding utf8
  & gcloud alpha monitoring policies update --project="$ProjectId" --policy-from-file="$tmp" | Out-Null
  & gcloud monitoring policies describe $pid --project="$ProjectId" --format='value(name,enabled)'
}

Write-Host "Done." -ForegroundColor Green