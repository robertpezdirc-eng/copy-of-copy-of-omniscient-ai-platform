param(
  [switch]$AutoRestart = $false,
  [string]$ComposeProfile = "monitoring",
  [switch]$RunSmokeTest = $true
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($msg)  { Write-Host "[INFO ] $msg"  -ForegroundColor Cyan }
function Write-Warn($msg)  { Write-Host "[WARN ] $msg"  -ForegroundColor Yellow }
function Write-ErrorMsg($msg){ Write-Host "[ERROR] $msg" -ForegroundColor Red }

function Test-DockerEngine {
  try {
    $json = docker version --format '{{json .}}' 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $json) { return $false }
    return ($json -notmatch '"Server":null')
  } catch { return $false }
}

function Restart-DockerDesktop {
  Write-Warn "Restarting Docker Desktop (this may take ~30-90s)"
  try { Get-Process "Docker Desktop" -ErrorAction SilentlyContinue | Stop-Process -Force } catch {}
  try { Stop-Process -Name "com.docker.backend" -Force -ErrorAction SilentlyContinue } catch {}
  $exe = Join-Path $env:ProgramFiles "Docker/Docker/Docker Desktop.exe"
  if (-not (Test-Path $exe)) {
    Write-Warn "Docker Desktop executable not found at: $exe"
  } else {
    Start-Process -FilePath $exe | Out-Null
  }
}

function Shutdown-WSL {
  Write-Warn "Shutting down WSL backend (wsl --shutdown)"
  try { wsl --shutdown | Out-Null } catch { Write-Warn "WSL shutdown error: $($_.Exception.Message)" }
}

function Wait-Docker([int]$TimeoutSec = 180) {
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  while ($sw.Elapsed.TotalSeconds -lt $TimeoutSec) {
    if (Test-DockerEngine) { return $true }
    Start-Sleep -Seconds 3
  }
  return $false
}

function Ensure-Image([string]$Image) {
  Write-Info "Ensuring image present: $Image"
  docker image inspect $Image 2>$null | Out-Null
  if ($LASTEXITCODE -ne 0) {
    Write-Info "Pulling $Image"
    docker pull $Image | Write-Host
  }
}

function Run-ComposeUp([string]$Profile) {
  Write-Info "docker compose --profile $Profile up -d"
  docker compose --profile $Profile up -d | Write-Host
}

function Run-SmokeTest {
  $scriptPath = Join-Path (Split-Path -Parent $PSCommandPath) "observability_smoketest.ps1"
  if (-not (Test-Path $scriptPath)) {
    Write-Warn "Smoke test script not found: $scriptPath"
    return
  }
  Write-Info "Running smoke test: $scriptPath"
  & $scriptPath
}

Write-Info "Checking Docker engine health"
if (-not (Test-DockerEngine)) {
  Write-Warn "Docker server not responding or returns 500."
  if ($AutoRestart) {
    Shutdown-WSL
    Restart-DockerDesktop
    if (-not (Wait-Docker -TimeoutSec 240)) {
      Write-ErrorMsg "Docker did not become healthy after restart. Aborting."
      exit 2
    }
  } else {
    Write-ErrorMsg "Engine is unhealthy. Rerun with -AutoRestart to attempt repair or restart Docker Desktop manually (Troubleshoot → Restart)."
    exit 2
  }
}

Write-Info "Testing basic pull (alpine:3.19)"
try {
  Ensure-Image "alpine:3.19"
} catch {
  Write-ErrorMsg "Image pull failed: $($_.Exception.Message)"
  exit 3
}

Write-Info "Bringing up monitoring profile"
try {
  Run-ComposeUp -Profile $ComposeProfile
} catch {
  Write-ErrorMsg "Compose up failed: $($_.Exception.Message)"
  exit 4
}

Write-Info "docker compose --profile $ComposeProfile ps"
docker compose --profile $ComposeProfile ps | Write-Host

if ($RunSmokeTest) {
  Run-SmokeTest
}

Write-Info "Done."
exit 0