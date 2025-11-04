#requires -version 5.1
Param(
  [Parameter(Mandatory=$true)] [string]$RepoUrl,
  [Parameter(Mandatory=$false)] [string]$Branch = "main",
  [Parameter(Mandatory=$false)] [string]$CommitMessage = "chore: vercel-ready deploy automation + upgrades"
)

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[ERR]  $msg" -ForegroundColor Red }

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Ensure we run at repo root (this script sits in scripts/)
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
if (Test-Path (Join-Path $root "..\.git")) {
  Set-Location (Join-Path $root "..")
} elseif (Test-Path (Join-Path (Get-Location) ".git")) {
  # already at root
} else {
  Set-Location (Join-Path $root "..")
}

Write-Info "Initializing git repository if needed"
if (-not (Test-Path ".git")) {
  git init | Out-Host
  Write-Ok "Initialized new git repo"
} else {
  Write-Info "Existing git repo detected"
}

Write-Info "Setting default branch: $Branch"
git branch -M $Branch | Out-Host

Write-Info "Staging all changes"
git add -A | Out-Host

Write-Info "Committing with message: $CommitMessage"
try {
  git commit -m $CommitMessage | Out-Host
} catch {
  Write-Warn "Commit may have been skipped (no changes). Proceeding."
}

Write-Info "Configuring remote origin: $RepoUrl"
try {
  git remote remove origin 2>$null
} catch {}
git remote add origin $RepoUrl | Out-Host

Write-Info "Pushing to origin/$Branch"
git push -u origin $Branch | Out-Host
Write-Ok "Push complete."