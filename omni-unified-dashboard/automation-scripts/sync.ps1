# Preprost PowerShell sync skript (lokalna kopija)
$source = "$(Resolve-Path ../web)"
$target = "$(Resolve-Path ../deployment-packages/web)"
if (!(Test-Path $target)) { New-Item -ItemType Directory -Path $target | Out-Null }
Robocopy $source $target /MIR /NFL /NDL /NP /R:1 /W:1 | Out-Null
Write-Host "Sync končan -> $target"