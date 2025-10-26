# Safely set SMTP environment variables in .env
# Usage example:
#   pwsh -File scripts/set-smtp-env.ps1 -Smarthost "smtp.example.com:587" -From "alerts@example.com" -To "ops@example.com" -RequireTLS true -User "smtpuser" -Pass "smtppass"

param(
  [string]$Smarthost,
  [string]$From,
  [string]$To,
  [bool]$RequireTLS = $false,
  [string]$User,
  [string]$Pass
)

$ErrorActionPreference = "Stop"
$envFile = Join-Path (Resolve-Path ".").Path ".env"

if (-not (Test-Path $envFile)) { New-Item -Path $envFile -ItemType File | Out-Null }

function Upsert-EnvLine([string]$Key, [string]$Value) {
  $content = Get-Content -Path $envFile -Raw
  if ($content -match "(?m)^$Key=.+$") {
    $content = [regex]::Replace($content, "(?m)^$Key=.+$", "$Key=$Value")
  } else {
    if ($content.Length -gt 0 -and -not $content.EndsWith("`n")) { $content += "`n" }
    $content += "$Key=$Value`n"
  }
  Set-Content -Path $envFile -Value $content -Encoding UTF8
}

if ($Smarthost) { Upsert-EnvLine "SMTP_SMARTHOST" $Smarthost }
if ($From) { Upsert-EnvLine "SMTP_FROM" $From }
if ($To) { Upsert-EnvLine "SMTP_TO" $To }
Upsert-EnvLine "SMTP_REQUIRE_TLS" ($RequireTLS.ToString().ToLower())

if ($User) { Upsert-EnvLine "SMTP_USER" $User }
if ($Pass) { Upsert-EnvLine "SMTP_PASS" $Pass }

Write-Host "Updated .env with SMTP settings."