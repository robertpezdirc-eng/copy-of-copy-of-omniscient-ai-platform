param(
  [Parameter(Mandatory=$true)][string]$InstanceName,
  [Parameter(Mandatory=$true)][string]$Zone,
  [Parameter(Mandatory=$true)][string]$ProjectId,
  [Parameter(Mandatory=$true)][string]$Region,
  [Parameter(Mandatory=$false)][string]$OpenAIKey = "",
  [Parameter(Mandatory=$false)][string]$ServiceAccountJsonPath = ""
)

function Exec($cmd) {
  Write-Host "[CMD] $cmd" -ForegroundColor Cyan
  $res = Invoke-Expression $cmd
  return $res
}

# 0) Quick checks
try {
  Exec "gcloud --version" | Out-Null
} catch {
  Write-Error "gcloud not found. Please install Google Cloud SDK and run 'gcloud init' first."
  exit 1
}

# 1) Prepare local temp service file
$tmplPath = Join-Path $PSScriptRoot "..\deployment-packages\omni-autolearn.service.tmpl"
if (!(Test-Path $tmplPath)) {
  Write-Error "Template not found: $tmplPath"
  exit 1
}
$userName = [System.Environment]::UserName
$serviceContent = Get-Content $tmplPath -Raw
$serviceContent = $serviceContent.Replace("{{USER}}", $userName)
$serviceContent = $serviceContent.Replace("{{OPENAI_API_KEY}}", $OpenAIKey)
$tempService = Join-Path $env:TEMP "omni-autolearn.service"
Set-Content -Path $tempService -Value $serviceContent -Encoding UTF8
Write-Host "Prepared service unit at $tempService" -ForegroundColor Green

# 2) Optional: copy service account json to remote
if ($ServiceAccountJsonPath -and (Test-Path $ServiceAccountJsonPath)) {
  Exec "gcloud compute scp `"$ServiceAccountJsonPath`" $InstanceName:/opt/omni/service-account.json --zone=$Zone"
} else {
  Write-Host "No ServiceAccountJsonPath provided or file not found; skipping copy." -ForegroundColor Yellow
}

# 3) Copy auto-learn files and service unit to remote
$files = @(
  "omni_autolearn_starter.py",
  "omni_event_logger.py",
  "omni_data_listener.py",
  "omni_learning_core.py",
  "omni_autolearn_config.json"
)
foreach ($f in $files) {
  $src = Join-Path (Get-Location) $f
  if (!(Test-Path $src)) {
    Write-Error "Missing local file: $src"
    exit 1
  }
}
Exec "gcloud compute scp `"$tempService`" $InstanceName:/tmp/omni-autolearn.service --zone=$Zone"
Exec "gcloud compute scp `"omni_autolearn_starter.py`" `"omni_event_logger.py`" `"omni_data_listener.py`" `"omni_learning_core.py`" `"omni_autolearn_config.json`" $InstanceName:/opt/omni/ --zone=$Zone"

# 4) Remote setup: create venv (if missing), install deps, move unit, enable & start service
$remoteCmds = @(
  'set -e',
  'sudo mkdir -p /opt/omni/logs',
  'if [ ! -d "/opt/omni/omni_env" ]; then python3 -m venv /opt/omni/omni_env; fi',
  '/opt/omni/omni_env/bin/pip install --upgrade pip',
  '/opt/omni/omni_env/bin/pip install requests google-cloud-storage',
  'sudo mv /tmp/omni-autolearn.service /etc/systemd/system/omni-autolearn.service',
  'sudo systemctl daemon-reload',
  'sudo systemctl enable omni-autolearn',
  'sudo systemctl restart omni-autolearn'
)
$remoteCmd = ($remoteCmds -join '; ')
Exec "gcloud compute ssh $InstanceName --zone=$Zone --command='$remoteCmd'"

# 5) Create bucket (if missing) and show content
Exec "gcloud compute ssh $InstanceName --zone=$Zone --command='(gsutil ls gs://omni-meta-data || gsutil mb -p $ProjectId -l $Region gs://omni-meta-data) && gsutil ls gs://omni-meta-data/models/'"

# 6) Show status & follow logs instruction
Write-Host "Auto-learning service deployed. To follow logs:" -ForegroundColor Green
Write-Host "gcloud compute ssh $InstanceName --zone=$Zone --command='sudo journalctl -u omni-autolearn -f'"
Write-Host "Or check: /opt/omni/logs/autolearn.log" -ForegroundColor Green