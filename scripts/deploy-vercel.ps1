#requires -version 5.1
Param(
  [Parameter(Mandatory=$true)] [string]$ProjectName,
  [Parameter(Mandatory=$false)] [string]$ApiUrl = "/api",
  [Parameter(Mandatory=$false)] [string]$NodeEnv = "production",
  [Parameter(Mandatory=$false)] [string]$DemoMode = "false",
  [Parameter(Mandatory=$false)] [string]$KvRestApiUrl,
  [Parameter(Mandatory=$false)] [string]$KvRestApiToken,
  [switch]$ProdOnly
)

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[ERR]  $msg" -ForegroundColor Red }

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Info "Checking Vercel CLI availability"
try {
  $ver = vercel --version 2>$null
  Write-Ok "Vercel CLI found: $ver"
} catch {
  Write-Warn "Vercel CLI not found. Installing globally via npm..."
  npm i -g vercel | Out-Host
  $ver = vercel --version
  Write-Ok "Installed Vercel CLI: $ver"
}

# Ensure we are at repo root
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
if (Test-Path (Join-Path $root "..\vercel.json")) {
  Set-Location (Join-Path $root "..")
} elseif (Test-Path (Join-Path (Get-Location) "vercel.json")) {
  # already at root
} else {
  Write-Err "vercel.json not found. Run from repo root or ensure vercel.json exists."
  exit 1
}

Write-Info "Linking directory to Vercel project: $ProjectName"
vercel link --name $ProjectName --confirm | Out-Host

Write-Info "Setting environment variables (non-interactive)"
function Set-EnvAll([string]$name, [string]$value) {
  vercel env set $name $value production --yes | Out-Host
  vercel env set $name $value preview --yes   | Out-Host
  vercel env set $name $value development --yes | Out-Host
}

Set-EnvAll -name "NODE_ENV" -value $NodeEnv
Set-EnvAll -name "VITE_DEMO_MODE" -value $DemoMode
Set-EnvAll -name "VITE_API_URL" -value $ApiUrl

if ($KvRestApiUrl) { Set-EnvAll -name "KV_REST_API_URL" -value $KvRestApiUrl }
if ($KvRestApiToken) { Set-EnvAll -name "KV_REST_API_TOKEN" -value $KvRestApiToken }

Write-Info "Triggering deployment(s)"
if (-not $ProdOnly) {
  Write-Info "Starting preview deployment"
  $previewOut = vercel --yes 2>&1
  $previewOut | Out-Host
  $previewUrl = ($previewOut | Select-String -Pattern "https://.*vercel\.app" -AllMatches).Matches | Select-Object -Last 1 | ForEach-Object { $_.Value }
  if ($previewUrl) { Write-Ok "Preview URL: $previewUrl" } else { Write-Warn "Could not detect preview URL from output." }
}

Write-Info "Starting production deployment"
$prodOut = vercel --prod --yes 2>&1
$prodOut | Out-Host
$prodUrl = ($prodOut | Select-String -Pattern "https://.*vercel\.app" -AllMatches).Matches | Select-Object -Last 1 | ForEach-Object { $_.Value }
if ($prodUrl) { Write-Ok "Production URL: $prodUrl" } else { Write-Warn "Could not detect production URL from output." }

Write-Ok "Deployment complete. Use scripts/health-check.ps1 to verify endpoints."