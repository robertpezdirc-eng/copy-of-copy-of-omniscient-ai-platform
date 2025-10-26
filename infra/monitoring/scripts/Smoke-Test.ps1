#!/usr/bin/env pwsh
# Smoke-Test.ps1
# Reusable Cloud Run uptime smoke test (PowerShell) with retries and optional content validation.
# Resolves SERVICE_URL from (priority): -Url -> -UrlFile (cloudrun-url.json) -> gcloud run services describe.
# Supports multiple endpoints, mode All/Any, expected status, substring check, simple JSON path equality, and diagnostics on failure.
#
# Examples:
#   ./Smoke-Test.ps1 -Url https://your.run.app -Paths /health -Retries 20 -DelaySec 5
#   ./Smoke-Test.ps1 -ServiceName omni-dashboard -Region europe-west1 -Paths '/health','/readyz' -Mode All
#   ./Smoke-Test.ps1 -UrlFile cloudrun-url.json -Paths /health -ExpectedStatus 200 -ExpectContains ok
#   ./Smoke-Test.ps1 -UrlFile cloudrun-url.json -Paths /health -ExpectJsonPath status -ExpectJsonEquals ok

param(
  [string]$Url,
  [string]$UrlFile = 'cloudrun-url.json',
  [string]$ServiceName,
  [string]$Region,
  [string[]]$Paths = @('/health'),
  [ValidateSet('All','Any')][string]$Mode = 'All',
  [int]$Retries = 20,
  [int]$DelaySec = 5,
  [int]$TimeoutSec = 10,
  [int]$ExpectedStatus = 200,
  [string]$ExpectContains,
  [string]$ExpectJsonPath,    # dot-path, e.g., "status" or "data.health"
  [string]$ExpectJsonEquals   # string value to compare at ExpectJsonPath
)

$ErrorActionPreference = 'Stop'

function Resolve-Url {
  param([string]$Url, [string]$UrlFile, [string]$ServiceName, [string]$Region)
  if ($Url) { return $Url }
  if (Test-Path -Path $UrlFile) {
    try {
      $json = Get-Content -Raw -Encoding UTF8 -Path $UrlFile | ConvertFrom-Json
      if ($json.url) { return [string]$json.url }
      if ($json.status -and $json.status.url) { return [string]$json.status.url }
    } catch {
      Write-Warning "Failed to parse $UrlFile: $($_.Exception.Message)"
    }
  }
  if ($ServiceName -and $Region) {
    $u = (& gcloud run services describe $ServiceName --region $Region --format 'value(status.url)')
    if ($u) { return $u }
  }
  throw "Unable to resolve service URL. Provide -Url or -UrlFile or -ServiceName/-Region"
}

function Normalize-Path([string]$p) {
  if (-not $p) { return $p }
  if ($p.StartsWith('/')) { return $p }
  return '/' + $p
}

function Get-JsonPathValue([object]$obj, [string]$path) {
  $cur = $obj
  foreach ($seg in $path.Split('.')) {
    if ($null -eq $cur) { return $null }
    $cur = $cur.PSObject.Properties[$seg].Value
  }
  return $cur
}

# Normalize paths
$Paths = $Paths | ForEach-Object { Normalize-Path $_ }

# Resolve URL
$BaseUrl = Resolve-Url -Url $Url -UrlFile $UrlFile -ServiceName $ServiceName -Region $Region
Write-Host "Base URL: $BaseUrl"
Write-Host "Paths: $($Paths -join ', ')"
Write-Host "Mode: $Mode, Retries: $Retries, Delay: ${DelaySec}s, Timeout: ${TimeoutSec}s"

$lastBody = ''
$lastCode = ''

function Test-AllPathsOnce {
  $passedAny = $false
  $allPass = $true
  foreach ($path in $Paths) {
    $full = "$($BaseUrl.TrimEnd('/'))$path"
    Write-Host "Requesting: $full"
    try {
      $resp = Invoke-WebRequest -Uri $full -Method GET -UseBasicParsing -TimeoutSec $TimeoutSec
      $code = [int]$resp.StatusCode
      $body = [string]$resp.Content
    } catch {
      $code = 0
      $body = ""
    }
    $script:lastCode = $code
    $script:lastBody = $body
    Write-Host "HTTP $code"

    if ($code -ne $ExpectedStatus) { $allPass = $false; continue }

    if ($ExpectContains) {
      if (-not ($body -like "*${ExpectContains}*")) { $allPass = $false; continue }
    }

    if ($ExpectJsonPath) {
      try {
        $obj = $body | ConvertFrom-Json -ErrorAction Stop
        $val = Get-JsonPathValue -obj $obj -path $ExpectJsonPath
        if ($PSBoundParameters.ContainsKey('ExpectJsonEquals')) {
          if (-not ("$val" -eq "$ExpectJsonEquals")) { $allPass = $false; continue }
        } elseif (-not $val) {
          # If only path specified, require it to exist/non-empty
          $allPass = $false; continue
        }
      } catch {
        $allPass = $false; continue
      }
    }

    $passedAny = $true
  }
  if ($Mode -eq 'Any') { return $passedAny } else { return $allPass }
}

$ok = $false
for ($i = 1; $i -le $Retries; $i++) {
  Write-Host "Attempt $i/$Retries"
  if (Test-AllPathsOnce) { $ok = $true; break }
  Start-Sleep -Seconds $DelaySec
}

if (-not $ok) {
  Write-Host "Smoke test FAILED." -ForegroundColor Red
  if ($lastCode) { Write-Host "Last HTTP status: $lastCode" -ForegroundColor Yellow }
  if ($lastBody) {
    $trunc = if ($lastBody.Length -gt 1000) { $lastBody.Substring(0,1000) } else { $lastBody }
    Write-Host "Last response body (first 1000 chars):" -ForegroundColor Yellow
    Write-Host $trunc
  }
  if ($ServiceName -and $Region) {
    Write-Host "Recent Cloud Run error logs (last 5m):" -ForegroundColor Yellow
    try {
      gcloud logging read `
        "resource.type=cloud_run_revision AND resource.labels.service_name=$ServiceName AND resource.labels.location=$Region AND severity>=ERROR" `
        --freshness=5m --limit=50 --format='value(textPayload)' | Out-Host
    } catch {}
  }
  exit 1
}

Write-Host "Smoke test PASSED." -ForegroundColor Green