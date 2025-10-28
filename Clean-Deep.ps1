# Clean-Deep.ps1 - Globoko ciscenje za sprostitev prostora (ASCII-only)
# POZOR: Agresivno brisanje launcherjev in iger. Uporabljaj na lastno odgovornost.

param(
    [switch]$Aggressive
)

$ErrorActionPreference = 'Stop'

function Get-DirSizeBytes {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return 0 }
    try {
        $sum = (Get-ChildItem -LiteralPath $Path -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        if ($null -eq $sum) { return 0 } else { return [int64]$sum }
    } catch { return 0 }
}

function FormatGB {
    param([int64]$Bytes)
    if ($Bytes -le 0) { return "0 GB" }
    return ('{0:N2} GB' -f ($Bytes / 1GB))
}

Write-Host "Zacetek globokega ciscenja" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Gray

# Prostor pred
$drive = Get-PSDrive -Name C
$beforeFree  = [int64]$drive.Free
$beforeUsed  = [int64]$drive.Used
$beforeTotal = [int64]$drive.Maximum
Write-Host ("C: skupaj: {0}, prosto: {1}, zasedeno: {2}" -f (FormatGB $beforeTotal), (FormatGB $beforeFree), (FormatGB $beforeUsed))

# Izkljucitve (ne brisemo trenutnega delovnega projekta)
$workspace = "C:\Users\admin\Downloads\copy-of-copy-of-omniscient-ai-platform"
$exclusions = @($workspace)

# Tarce za brisanje (igre in launcherji)
$pathsGames = @(
    "C:\Games",
    "C:\Program Files (x86)\Steam\steamapps\common",
    "C:\Program Files\Steam\steamapps\common"
)

$pathsLaunchers = @(
    "C:\Program Files (x86)\Steam",
    "C:\Program Files\Steam",
    "C:\Program Files\Epic Games",
    "C:\Program Files (x86)\GOG Galaxy",
    "C:\Program Files (x86)\Origin Games",
    "C:\Program Files\EA Games",
    "C:\Program Files (x86)\Ubisoft\Ubisoft Game Launcher",
    "C:\Riot Games",
    "C:\Program Files (x86)\Battle.net",
    "C:\Program Files\Battle.net",
    "C:\Program Files (x86)\Rockstar Games",
    "C:\Program Files\Rockstar Games",
    "C:\Program Files (x86)\Bethesda.net Launcher",
    "C:\Program Files\Bethesda Softworks",
    "C:\Program Files (x86)\2K Games",
    "C:\Program Files\Paradox Interactive"
)

# Cache mape
$pathsCaches = @(
    "$env:LOCALAPPDATA\Temp",
    "$env:WINDIR\Temp",
    "$env:WINDIR\Prefetch",
    "$env:WINDIR\SoftwareDistribution\Download",
    "$env:ProgramData\USOShared\Logs",
    "$env:ProgramData\NVIDIA Corporation\Downloader",
    "$env:ProgramData\Battle.net",
    "$env:ProgramData\Epic",
    "$env:ProgramData\Origin",
    "$env:ProgramData\Ubisoft",
    "$env:ProgramData\Riot Games",
    "$env:LOCALAPPDATA\Steam",
    "$env:LOCALAPPDATA\EpicGamesLauncher",
    "$env:LOCALAPPDATA\Battle.net",
    "$env:LOCALAPPDATA\Origin",
    "$env:LOCALAPPDATA\Ubisoft Game Launcher",
    "$env:LOCALAPPDATA\Riot Games"
)

# Zbere vse tarce
$targets = @()
foreach ($p in ($pathsGames + $pathsCaches)) {
    if (Test-Path -LiteralPath $p) {
        $targets += $p
    }
}
if ($Aggressive) {
    foreach ($p in $pathsLaunchers) {
        if (Test-Path -LiteralPath $p) { $targets += $p }
    }
}

# Filtrira izkljucitve
$targets = $targets | Where-Object { $exclusions -notcontains $_ }

# Izpis tarc
Write-Host "Najdene tarce:" -ForegroundColor Yellow
foreach ($t in $targets) { Write-Host ("  - {0}" -f $t) }

# Brisanje
$deletedBytes = [int64]0
$failed = @()
foreach ($t in $targets) {
    try {
        $size = Get-DirSizeBytes -Path $t
        Write-Host ("Brisem: {0} ({1})" -f $t, (FormatGB $size)) -ForegroundColor Red
        Remove-Item -LiteralPath $t -Recurse -Force -ErrorAction Stop
        $deletedBytes += [int64]$size
    } catch {
        Write-Host ("Napaka brisanja: {0} - {1}" -f $t, $_.Exception.Message) -ForegroundColor Magenta
        $failed += $t
    }
}

# Ciscenje kozarca za smeti (Recycle Bin)
try { Clear-RecycleBin -Force -ErrorAction SilentlyContinue } catch {}

# Prostor po
$driveAfter = Get-PSDrive -Name C
$afterFree  = [int64]$driveAfter.Free
$afterUsed  = [int64]$driveAfter.Used
$afterTotal = [int64]$driveAfter.Maximum
$gained = $afterFree - $beforeFree

Write-Host ""; Write-Host "Porocilo" -ForegroundColor Cyan
Write-Host ("=" * 50)
Write-Host ("C: skupaj: {0}" -f (FormatGB $afterTotal))
Write-Host ("Prosto: {0}" -f (FormatGB $afterFree)) -ForegroundColor Green
Write-Host ("Zasedeno: {0}" -f (FormatGB $afterUsed))
Write-Host ("Pridobljeno: {0}" -f (FormatGB $gained)) -ForegroundColor Green
Write-Host ("Izbrisano skupaj (ocena): {0}" -f (FormatGB $deletedBytes))

if ($failed.Count -gt 0) {
    Write-Host "Nekaterih map ni bilo mogoce izbrisati:" -ForegroundColor Yellow
    $failed | ForEach-Object { Write-Host ("  - {0}" -f $_) }
}

Write-Output "Globoko ciscenje koncano."