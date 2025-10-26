# Preprost PowerShell backup skript
$source = "$(Resolve-Path ../docs)"
$destRoot = "$(Resolve-Path ../backups)"
if (!(Test-Path $destRoot)) { New-Item -ItemType Directory -Path $destRoot | Out-Null }
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$dest = Join-Path $destRoot "docs_backup_$ts"
Copy-Item -Path $source -Destination $dest -Recurse
Write-Host "Backup končan -> $dest"