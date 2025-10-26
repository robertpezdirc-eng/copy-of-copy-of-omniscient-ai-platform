Param(
  [Parameter(Mandatory=$false)][string]$NewKey,
  [switch]$Restart
)

# Rotates the OpenAI API key stored in 'openai key.txt' (file-based secret).
# - Backs up the existing key file
# - Writes the new key without trailing newline
# - Optionally rebuilds and restarts blue/green containers

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[ERR]  $msg" -ForegroundColor Red }

try {
  $root = Split-Path -Parent $PSCommandPath | Split-Path -Parent
  Set-Location $root
  $keyFile = Join-Path $root 'openai key.txt'

  if (-not $NewKey) {
    Write-Info 'Vnesite nov OpenAI API ključ (ne bo prikazan):'
    $NewKey = Read-Host -AsSecureString | ForEach-Object { [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($_)) }
  }

  if (-not $NewKey -or $NewKey.Trim().Length -lt 10) {
    throw 'Neveljaven ključ – vnos je prazen ali prekratek.'
  }

  # Sanitize: remove control characters and whitespace; trim non-ASCII just in case
  $sanitized = ($NewKey -replace "[\p{C}]", "" -replace "\s+", "").Trim()
  $sanitized = [System.Text.Encoding]::ASCII.GetString([System.Text.Encoding]::ASCII.GetBytes($sanitized))

  # Backup existing file
  if (Test-Path $keyFile) {
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $backup = Join-Path $root ("openai key.txt.bak-$stamp")
    Copy-Item $keyFile $backup -Force
    Write-Info "Backup ustvarjen: $backup"
  }

  # Write without newline
  Set-Content -Path $keyFile -Value $sanitized -Encoding ASCII -NoNewline
  Write-Ok "OpenAI ključ posodobljen v: $keyFile"

  # Optional: comment out OPENAI_API_KEY in root .env for safety
  $envFile = Join-Path $root '.env'
  if (Test-Path $envFile) {
    $lines = Get-Content $envFile
    $updated = @()
    foreach ($l in $lines) {
      if ($l -match '^\s*OPENAI_API_KEY\s*=') {
        $updated += '# OPENAI_API_KEY='
      } else {
        $updated += $l
      }
    }
    $updated | Set-Content -Path $envFile -Encoding UTF8
    Write-Info 'Root .env posodobljen (OPENAI_API_KEY zakomentiran)'
  }

  if ($Restart.IsPresent) {
    Write-Info 'Ponovni zagon blue/green API storitev...'
    $cmd = 'docker compose -f docker-compose.blue-green.yml up -d --build'
    $proc = Start-Process -FilePath 'powershell' -ArgumentList $cmd -NoNewWindow -Wait -PassThru
    if ($proc.ExitCode -eq 0) {
      Write-Ok 'Storitev uspešno ponovno zagnana.'
    } else {
      Write-Warn "Ukaz končan z izhodno kodo: $($proc.ExitCode)"
    }
  }
} catch {
  Write-Err $_.Exception.Message
  exit 1
}