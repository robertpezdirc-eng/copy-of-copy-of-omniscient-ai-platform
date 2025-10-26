param(
  [Parameter(Mandatory=$true)]
  [string]$Webhook
)

$ErrorActionPreference = "Stop"

$envPath = Join-Path (Resolve-Path ".").Path ".env"
if (-not (Test-Path $envPath)) {
  New-Item -ItemType File -Path $envPath -Force | Out-Null
}
$lines = Get-Content -Path $envPath -ErrorAction SilentlyContinue
if ($null -eq $lines) { $lines = @() }

$newLine = "SLACK_WEBHOOK_URL=$Webhook"
$updated = $false
$out = foreach ($l in $lines) {
  if ($l -match '^SLACK_WEBHOOK_URL=') { $updated = $true; $newLine } else { $l }
}
if (-not $updated) { $out += $newLine }

$out | Set-Content -Path $envPath -Encoding UTF8

Write-Host "SLACK_WEBHOOK_URL set in .env: $Webhook"