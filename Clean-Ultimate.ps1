# Ultimate Aggressive Cleanup - Maximum Space for DaVinci Resolve
param([switch]$WhatIf)

function Get-DirectorySize {
    param([string]$Path)
    if (Test-Path $Path) {
        try {
            $size = (Get-ChildItem -Path $Path -Recurse -Force -ErrorAction SilentlyContinue | 
                    Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
            return [math]::Max($size, 0)
        } catch { return 0 }
    }
    return 0
}

function Format-BytesToGB {
    param([long]$Bytes)
    return [math]::Round($Bytes / 1GB, 2)
}

function Force-RemoveDirectory {
    param([string]$Path, [string]$Name)
    if (Test-Path $Path) {
        $size = Get-DirectorySize -Path $Path
        $sizeGB = Format-BytesToGB -Bytes $size
        Write-Host "Removing $Name ($sizeGB GB)..." -ForegroundColor Yellow
        
        if (-not $WhatIf) {
            try {
                # Force unlock files and remove
                Get-ChildItem -Path $Path -Recurse -Force -ErrorAction SilentlyContinue | 
                    ForEach-Object { 
                        try { $_.Attributes = 'Normal' } catch {}
                    }
                Remove-Item -Path $Path -Recurse -Force -ErrorAction SilentlyContinue
                Write-Host "  Deleted $Name" -ForegroundColor Green
                return $size
            } catch {
                Write-Host "  Error removing $Name`: $_" -ForegroundColor Red
                return 0
            }
        } else {
            Write-Host "  Would delete $Name ($sizeGB GB)" -ForegroundColor Cyan
            return $size
        }
    }
    return 0
}

Write-Host "=== ULTIMATE AGGRESSIVE CLEANUP ===" -ForegroundColor Red
Write-Host "Preparing maximum space for DaVinci Resolve..." -ForegroundColor Yellow

$totalFreed = 0

# Game Launchers - Complete Removal
$launchers = @(
    @{Path="C:\Program Files (x86)\Epic Games"; Name="Epic Games Launcher"},
    @{Path="C:\Program Files\Epic Games"; Name="Epic Games Launcher (64-bit)"},
    @{Path="C:\Users\admin\AppData\Local\EpicGamesLauncher"; Name="Epic Games Data"},
    
    @{Path="C:\Program Files (x86)\GOG Galaxy"; Name="GOG Galaxy"},
    @{Path="C:\Program Files\GOG Galaxy"; Name="GOG Galaxy (64-bit)"},
    @{Path="C:\Users\admin\AppData\Local\GOG.com"; Name="GOG Data"},
    
    @{Path="C:\Program Files (x86)\Ubisoft"; Name="Ubisoft Connect"},
    @{Path="C:\Program Files\Ubisoft"; Name="Ubisoft Connect (64-bit)"},
    @{Path="C:\Users\admin\AppData\Local\Ubisoft Game Launcher"; Name="Ubisoft Data"},
    
    @{Path="C:\Program Files (x86)\Origin"; Name="EA Origin"},
    @{Path="C:\Program Files\EA Desktop"; Name="EA Desktop"},
    @{Path="C:\Users\admin\AppData\Local\Origin"; Name="Origin Data"},
    @{Path="C:\Users\admin\AppData\Roaming\Origin"; Name="Origin Settings"},
    
    @{Path="C:\Program Files (x86)\Riot Games"; Name="Riot Games"},
    @{Path="C:\Users\admin\AppData\Local\Riot Games"; Name="Riot Games Data"},
    
    @{Path="C:\Program Files (x86)\Battle.net"; Name="Battle.net"},
    @{Path="C:\Users\admin\AppData\Local\Battle.net"; Name="Battle.net Data"},
    @{Path="C:\Users\admin\AppData\Roaming\Battle.net"; Name="Battle.net Settings"},
    
    @{Path="C:\Program Files\Rockstar Games"; Name="Rockstar Games Launcher"},
    @{Path="C:\Program Files (x86)\Rockstar Games"; Name="Rockstar Games Launcher (32-bit)"},
    @{Path="C:\Users\admin\AppData\Local\Rockstar Games"; Name="Rockstar Games Data"}
)

Write-Host "`nRemoving Game Launchers..." -ForegroundColor Yellow
foreach ($launcher in $launchers) {
    $totalFreed += Force-RemoveDirectory -Path $launcher.Path -Name $launcher.Name
}

# Force Clear Temp Files (including blocked ones)
$tempPaths = @(
    @{Path="C:\Users\admin\AppData\Local\Temp"; Name="User Temp"},
    @{Path="C:\Windows\Temp"; Name="System Temp"},
    @{Path="C:\Temp"; Name="Root Temp"},
    @{Path="C:\tmp"; Name="Root tmp"}
)

Write-Host "`nForce clearing temporary files..." -ForegroundColor Yellow
foreach ($temp in $tempPaths) {
    if (Test-Path $temp.Path) {
        Write-Host "Clearing $($temp.Name)..." -ForegroundColor Yellow
        if (-not $WhatIf) {
            try {
                # Force unlock and delete individual files
                Get-ChildItem -Path $temp.Path -Force -ErrorAction SilentlyContinue | 
                    ForEach-Object {
                        try {
                            $_.Attributes = 'Normal'
                            Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
                        } catch {}
                    }
                Write-Host "  Cleared $($temp.Name)" -ForegroundColor Green
            } catch {
                Write-Host "  Partial clear of $($temp.Name)" -ForegroundColor Yellow
            }
        }
    }
}

# Additional System Cleanup
$systemCleanup = @(
    @{Path="C:\Windows\SoftwareDistribution\Download"; Name="Windows Update Cache"},
    @{Path="C:\Windows\Logs"; Name="Windows Logs"},
    @{Path="C:\ProgramData\Microsoft\Windows\WER"; Name="Windows Error Reports"},
    @{Path="C:\Users\admin\AppData\Local\Microsoft\Windows\INetCache"; Name="Internet Cache"},
    @{Path="C:\Users\admin\AppData\Local\Microsoft\Windows\WebCache"; Name="Web Cache"}
)

Write-Host "`nSystem cleanup..." -ForegroundColor Yellow
foreach ($cleanup in $systemCleanup) {
    $totalFreed += Force-RemoveDirectory -Path $cleanup.Path -Name $cleanup.Name
}

# Clear Recycle Bin
Write-Host "`nClearing Recycle Bin..." -ForegroundColor Yellow
if (-not $WhatIf) {
    try {
        Clear-RecycleBin -Force -ErrorAction SilentlyContinue
        Write-Host "  Recycle Bin cleared" -ForegroundColor Green
    } catch {
        Write-Host "  Could not clear Recycle Bin" -ForegroundColor Yellow
    }
}

# Final Space Report
Write-Host "`n=== FINAL SPACE REPORT ===" -ForegroundColor Green
$drive = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
$freeGB = [math]::Round($drive.FreeSpace / 1GB, 2)
$totalGB = [math]::Round($drive.Size / 1GB, 2)
$usedGB = [math]::Round(($drive.Size - $drive.FreeSpace) / 1GB, 2)
$freedGB = Format-BytesToGB -Bytes $totalFreed

Write-Host "Drive C: Status:" -ForegroundColor White
Write-Host "  Free Space: $freeGB GB" -ForegroundColor Green
Write-Host "  Used Space: $usedGB GB" -ForegroundColor Yellow
Write-Host "  Total Size: $totalGB GB" -ForegroundColor White
Write-Host "  Space Freed This Session: $freedGB GB" -ForegroundColor Cyan

if ($freeGB -gt 10) {
    Write-Host "`nREADY FOR DAVINCI RESOLVE INSTALLATION!" -ForegroundColor Green
    Write-Host "Recommended: Download DaVinci Resolve now." -ForegroundColor Cyan
} else {
    Write-Host "`nWARNING: May need more space for DaVinci Resolve" -ForegroundColor Yellow
    Write-Host "Consider removing additional programs or files." -ForegroundColor Yellow
}