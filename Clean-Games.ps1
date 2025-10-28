# Clean-Games.ps1 — odstranitev iger in porocilo o prostem prostoru (ASCII)

param(
    [switch]$WhatIf
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

Write-Host "Ciscenje iger - zacetek" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Gray

# Prostor pred brisanjem
$drive = Get-PSDrive -Name C
$beforeFree  = [int64]$drive.Free
$beforeUsed  = [int64]$drive.Used
$beforeTotal = [int64]$drive.Maximum
Write-Host ("C: skupaj: {0}, prosto: {1}, zasedeno: {2}" -f (FormatGB $beforeTotal), (FormatGB $beforeFree), (FormatGB $beforeUsed)) -ForegroundColor White

# Tipicne mape iger
$paths = @(
    "C:\\Program Files (x86)\\Steam\\steamapps\\common",
    "C:\\Program Files\\Steam\\steamapps\\common",
    "C:\\Program Files\\Epic Games",
    "C:\\Program Files (x86)\\GOG Galaxy\\Games",
    "C:\\Program Files (x86)\\Origin Games",
    "C:\\Program Files\\EA Games",
    "C:\\Program Files (x86)\\Ubisoft\\Ubisoft Game Launcher\\games",
    "C:\\Riot Games",
    "C:\\Program Files (x86)\\Battle.net",
    "C:\\Users\\admin\\Games",
    "C:\\Games"
)

# Najdi obstojece mape in izracunaj velikosti
$targets = @()
foreach ($p in $paths) {
    if (Test-Path -LiteralPath $p) {
        $subdirs = @(Get-ChildItem -LiteralPath $p -Directory -ErrorAction SilentlyContinue)
        if ($subdirs.Count -gt 0) {
            foreach ($sd in $subdirs) {
                $size = Get-DirSizeBytes -Path $sd.FullName
                $targets += [pscustomobject]@{ Path=$sd.FullName; Size=$size; Root=$p }
            }
        } else {
            $size = Get-DirSizeBytes -Path $p
            $targets += [pscustomobject]@{ Path=$p; Size=$size; Root=$p }
        }
    }
}

if ($targets.Count -eq 0) {
    Write-Host "Ni najdenih map iger za brisanje." -ForegroundColor Yellow
} else {
    Write-Host "Najdene mape iger:" -ForegroundColor Yellow
    foreach ($t in ($targets | Sort-Object Size -Descending)) {
        Write-Host ("  - {0} ({1})" -f $t.Path, (FormatGB $t.Size)) -ForegroundColor White
    }
}

# Brisanje najdenih map
$deletedBytes = [int64]0
$failed = @()
if (-not $WhatIf) {
    foreach ($t in ($targets | Sort-Object Size -Descending)) {
        try {
            Write-Host ("Brisem: {0} ({1})" -f $t.Path, (FormatGB $t.Size)) -ForegroundColor Red
            Remove-Item -LiteralPath $t.Path -Recurse -Force -ErrorAction Stop
            $deletedBytes += [int64]$t.Size
        } catch {
            Write-Host ("Napaka brisanja: {0} - {1}" -f $t.Path, $_.Exception.Message) -ForegroundColor Magenta
            $failed += $t.Path
        }
    }
} else {
    Write-Host "WhatIf vklopljen - skript ne brise, samo poroca." -ForegroundColor Cyan
}

# Dodatno ciscenje predpomnilnikov (varno)
$cachePaths = @(
    "C:\\Users\\admin\\AppData\\Local\\Temp",
    "C:\\Windows\\Temp",
    "C:\\Program Files (x86)\\Steam\\steamapps\\downloading",
    "C:\\Program Files\\Epic Games\\Launcher\\Portal\\Engine\\Binaries\\Win64"
)
foreach ($cp in $cachePaths) {
    try {
        if (Test-Path -LiteralPath $cp) {
            Write-Host ("Cistim predpomnilnik: {0}" -f $cp) -ForegroundColor DarkYellow
            Remove-Item -LiteralPath $cp -Recurse -Force -ErrorAction SilentlyContinue
        }
    } catch {}
}

# Prostor po brisanju
$driveAfter = Get-PSDrive -Name C
$afterFree  = [int64]$driveAfter.Free
$afterUsed  = [int64]$driveAfter.Used
$afterTotal = [int64]$driveAfter.Maximum
$gained = $afterFree - $beforeFree

Write-Host ""; Write-Host "POROCILO O CISCENJU" -ForegroundColor Cyan
Write-Host ("=" * 50) -ForegroundColor Gray
Write-Host ("C: skupaj: {0}" -f (FormatGB $afterTotal)) -ForegroundColor White
Write-Host ("Prosto: {0}" -f (FormatGB $afterFree)) -ForegroundColor Green
Write-Host ("Zasedeno: {0}" -f (FormatGB $afterUsed)) -ForegroundColor White
Write-Host ("Pridobljeno: {0}" -f (FormatGB $gained)) -ForegroundColor Green

if ($failed.Count -gt 0) {
    Write-Host "Nekaterih map ni bilo mogoce izbrisati (morda potrebne pravice skrbnika):" -ForegroundColor Yellow
    $failed | ForEach-Object { Write-Host ("  - {0}" -f $_) -ForegroundColor Yellow }
}

Write-Output "Ciscenje koncano."
