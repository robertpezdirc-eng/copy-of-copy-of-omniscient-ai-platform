#!/usr/bin/env pwsh
# Requires: gcloud CLI
# Disable one or more Cloud Monitoring alert policies by displayName (exact or regex).
# Usage examples:
#   ./Disable-Policy.ps1 -ProjectId omni-dev-420223 -Filter "Uptime Check Failed"            # regex
#   ./Disable-Policy.ps1 -ProjectId omni-dev-420223 -Filter "OMNI Dashboard - Uptime Check (MQL Multi-Region)" -Exact
#   ./Disable-Policy.ps1 -Filter "^Cloud Run P95 Latency" -Yes                               # uses default gcloud project
#   ./Disable-Policy.ps1 -Filter "Uptime Check Failed" -DryRun
#   ./Disable-Policy.ps1 -Filter "Uptime Check Failed" -ExcludePatterns "MQL (>=2 checker locations)","MQL Multi-Region" -Yes

param(
  [string]$ProjectId,
  [Parameter(Mandatory = $true)][string]$Filter,
  [switch]$Exact,
  [string[]]$ExcludePatterns,
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
$filterParts = @()
if ($Exact) {
  $filterParts += "displayName=\"$Filter\""
} else {
  $filterParts += "displayName ~ \"$Filter\""
}
if ($ExcludePatterns) {
  foreach ($ex in $ExcludePatterns) {
    if ($null -ne $ex -and $ex.Trim() -ne '') {
      $filterParts += "NOT displayName ~ \"$ex\""
    }
  }
}
$gcloudFilter = [string]::Join(' AND ', $filterParts)

Write-Host "Project: $ProjectId"
if ($Exact) { Write-Host "Filter (exact): $Filter" } else { Write-Host "Filter (regex): $Filter" }
if ($ExcludePatterns) { Write-Host ("Exclude patterns: " + ($ExcludePatterns -join ', ')) }

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
  Write-Host "Dry-run: would disable $($policyIds.Count) policy(ies)."
  exit 0
}

if (-not $Yes) {
  $ans = Read-Host "Disable $($policyIds.Count) policy(ies)? [y/N]"
  if ($ans -notin @('y','Y','yes','YES')) {
    Write-Host "Aborted."
    exit 0
  }
}

foreach ($pid in $policyIds) {
  Write-Host "Disabling $pid ..."
  $json = & gcloud alpha monitoring policies describe $pid --project="$ProjectId" --format=json | ConvertFrom-Json
  $json.enabled = $false
  $tmp = [System.IO.Path]::GetTempFileName()
  $json | ConvertTo-Json -Depth 100 | Set-Content -Path $tmp -Encoding utf8
  & gcloud alpha monitoring policies update --project="$ProjectId" --policy-from-file="$tmp" | Out-Null
  & gcloud monitoring policies describe $pid --project="$ProjectId" --format='value(name,enabled)'
}

Write-Host "Done." -ForegroundColor Green