# Omni daily backup script
# Compress omni_platform and upload to GCS bucket using gcloud storage
$ErrorActionPreference = 'Stop'

# Config
$Project = 'refined-graph-471712-n9'
$Bucket = 'gs://omni-markec-backups-471712-n9'
$SourceDir = 'C:\Users\admin\Downloads\copy-of-copy-of-omniscient-ai-platform\omni_platform'
$BackupRoot = 'C:\OmniSingularity\backups'
$GcloudExe = 'C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.exe'
$CredsPath = 'C:\OmniSingularity\keys\omnigc-key.json'

# Prepare paths
$timestamp = (Get-Date).ToString('yyyy-MM-dd_HH-mm')
$zipName = "omni_platform_$timestamp.zip"
$zipPath = Join-Path $BackupRoot $zipName

# Ensure folders exist
New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null

# Verify source exists
if (-not (Test-Path $SourceDir)) {
    Write-Error "Source directory not found: $SourceDir"
}

# Compress directory
Compress-Archive -Path $SourceDir -DestinationPath $zipPath -Force

# Set credentials for gcloud in this process
$env:GOOGLE_APPLICATION_CREDENTIALS = $CredsPath

# Ensure project is set
& $GcloudExe config set project $Project --quiet | Out-Null

# Upload to bucket
& $GcloudExe storage cp $zipPath "$Bucket/$zipName" --quiet

# Optional: keep only last 14 local backups
Get-ChildItem -Path $BackupRoot -Filter 'omni_platform_*.zip' | Sort-Object CreationTime -Descending | Select-Object -Skip 14 | Remove-Item -Force -ErrorAction SilentlyContinue

Write-Output "Backup completed: $zipPath -> $Bucket/$zipName"