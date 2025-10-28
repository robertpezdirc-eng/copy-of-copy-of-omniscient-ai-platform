# Omni Platform - KOMPLETNA VIDEO AVTOMATIZACIJA
# 1-KLIK RESITEV: Snemanje -> Postprodukcija -> Izvoz -> Objava

param(
    [string]$ProjectName = "Omni-Demo-$(Get-Date -Format 'yyyy-MM-dd-HH-mm')",
    [int]$DemoLength = 95,
    [switch]$SkipRecording = $false,
    [switch]$SkipPostProduction = $false,
    [switch]$SkipExport = $false,
    [switch]$YouTube = $true,
    [switch]$LinkedIn = $true,
    [switch]$Twitter = $true,
    [switch]$OpenResults = $true
)

# Barve za konzolo
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"
$Cyan = "Cyan"
$Magenta = "Magenta"

Clear-Host
Write-Host "OMNI PLATFORM - KOMPLETNA VIDEO AVTOMATIZACIJA" -ForegroundColor $Magenta
Write-Host "===============================================" -ForegroundColor $Magenta
Write-Host "1-KLIK RESITEV ZA PROFESIONALEN VIDEO" -ForegroundColor $Cyan
Write-Host ""

# Globalne spremenljivke
$StartTime = Get-Date
$LogFile = ".\video-automation-$(Get-Date -Format 'yyyy-MM-dd-HH-mm').log"
$Results = @{
    Recording = $null
    PostProduction = $null
    Exports = @()
    Errors = @()
    Duration = $null
}

# Funkcija za logiranje
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $LogFile -Value $logEntry
    
    switch ($Level) {
        "ERROR" { Write-Host "[ERROR] $Message" -ForegroundColor $Red }
        "WARNING" { Write-Host "[WARNING] $Message" -ForegroundColor $Yellow }
        "SUCCESS" { Write-Host "[SUCCESS] $Message" -ForegroundColor $Green }
        "INFO" { Write-Host "[INFO] $Message" -ForegroundColor $Cyan }
        "STEP" { Write-Host "[STEP] $Message" -ForegroundColor $Magenta }
    }
}

Write-Log "Zacenjam kompletno video avtomatizacijo za projekt: $ProjectName" "STEP"

# KORAK 1: PREVERI PREDPOGOJE
Write-Log "KORAK 1/4: Preverjam predpogoje..." "STEP"

# Preveri strežnike
$serversOK = $true
try {
    $null = Invoke-WebRequest -Uri "http://localhost:3000" -Method GET -TimeoutSec 2 -ErrorAction Stop
    Write-Log "Frontend streznik (port 3000) - OK" "SUCCESS"
} catch {
    Write-Log "Frontend streznik ni aktiven" "ERROR"
    $serversOK = $false
}

try {
    $null = Invoke-WebRequest -Uri "http://localhost:8004/health" -Method GET -TimeoutSec 2 -ErrorAction Stop
    Write-Log "Backend streznik (port 8004) - OK" "SUCCESS"
} catch {
    Write-Log "Backend streznik ni aktiven" "ERROR"
    $serversOK = $false
}

try {
    $null = Invoke-WebRequest -Uri "http://localhost:8009" -Method GET -TimeoutSec 2 -ErrorAction Stop
    Write-Log "Assets streznik (port 8009) - OK" "SUCCESS"
} catch {
    Write-Log "Assets streznik ni aktiven" "ERROR"
    $serversOK = $false
}

if (-not $serversOK) {
    Write-Log "Zaganjam streznike..." "WARNING"
    Write-Host "Zazeni streznike z: .\Launch-Omni-Demo.ps1" -ForegroundColor $Yellow
    Write-Host "Cakam 10 sekund za zagon streznikov..." -ForegroundColor $Yellow
    Start-Sleep 10
}

# Preveri orodja
$toolsOK = $true

# Preveri OBS
if (-not (Get-Process "obs64" -ErrorAction SilentlyContinue)) {
    Write-Log "Zaganjam OBS Studio..." "INFO"
    try {
        Start-Process "obs64" -WindowStyle Minimized
        Start-Sleep 5
    } catch {
        Write-Log "OBS Studio ni namescen ali ni v PATH" "ERROR"
        $toolsOK = $false
    }
}

# Preveri FFmpeg
try {
    $null = & ffmpeg -version 2>$null
    Write-Log "FFmpeg - OK" "SUCCESS"
} catch {
    Write-Log "FFmpeg ni namescen" "ERROR"
    $toolsOK = $false
}

if (-not $toolsOK) {
    Write-Log "Manjkajo potrebna orodja!" "ERROR"
    $Results.Errors += "Manjkajo potrebna orodja (OBS/FFmpeg)"
    exit 1
}

# KORAK 2: SNEMANJE
if (-not $SkipRecording) {
    Write-Log "KORAK 2/4: Avtomatsko snemanje..." "STEP"
    
    try {
        $recordingResult = & ".\Auto-Record-Demo.ps1" -VideoName $ProjectName -DemoLength $DemoLength -OutputPath ".\videos\"
        
        # Najdi posneti video
        $recordedVideo = Get-ChildItem -Path ".\videos\" -Filter "$ProjectName.mp4" | Select-Object -First 1
        if ($recordedVideo) {
            $Results.Recording = $recordedVideo.FullName
            Write-Log "Snemanje uspesno: $($recordedVideo.Name)" "SUCCESS"
        } else {
            throw "Video datoteka ni bila najdena"
        }
        
    } catch {
        Write-Log "Napaka pri snemanju: $($_.Exception.Message)" "ERROR"
        $Results.Errors += "Napaka pri snemanju"
        
        # Poskusi najti najnovejši video
        $latestVideo = Get-ChildItem -Path ".\videos\" -Filter "*.mp4" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($latestVideo) {
            $Results.Recording = $latestVideo.FullName
            Write-Log "Uporabim najnovejsi video: $($latestVideo.Name)" "WARNING"
        } else {
            Write-Log "Ni najdenih video datotek!" "ERROR"
            exit 1
        }
    }
} else {
    Write-Log "Preskacam snemanje (SkipRecording = true)" "INFO"
    $latestVideo = Get-ChildItem -Path ".\videos\" -Filter "*.mp4" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($latestVideo) {
        $Results.Recording = $latestVideo.FullName
        Write-Log "Uporabim obstoječi video: $($latestVideo.Name)" "INFO"
    }
}

# KORAK 3: POSTPRODUKCIJA
if (-not $SkipPostProduction -and $Results.Recording) {
    Write-Log "KORAK 3/4: Postprodukcija..." "STEP"
    
    try {
        $postProdResult = & ".\Post-Process-Video.ps1" -InputVideo $Results.Recording -OutputPath ".\videos\final\"
        
        # Najdi končni video
        $baseName = [System.IO.Path]::GetFileNameWithoutExtension($Results.Recording)
        $finalVideo = ".\videos\final\$baseName-FINAL.mp4"
        
        if (Test-Path $finalVideo) {
            $Results.PostProduction = $finalVideo
            Write-Log "Postprodukcija uspesna: $baseName-FINAL.mp4" "SUCCESS"
        } else {
            throw "Koncni video ni bil ustvarjen"
        }
        
    } catch {
        Write-Log "Napaka pri postprodukciji: $($_.Exception.Message)" "ERROR"
        $Results.Errors += "Napaka pri postprodukciji"
        $Results.PostProduction = $Results.Recording
    }
} else {
    Write-Log "Preskacam postprodukcijo" "INFO"
    $Results.PostProduction = $Results.Recording
}

# KORAK 4: IZVOZ ZA PLATFORME
if (-not $SkipExport -and $Results.PostProduction) {
    Write-Log "KORAK 4/4: Izvoz za platforme..." "STEP"
    
    try {
        $exportArgs = @(
            "-InputVideo", $Results.PostProduction
            "-OutputPath", ".\videos\export\"
        )
        
        if ($YouTube) { $exportArgs += "-YouTube" }
        if ($LinkedIn) { $exportArgs += "-LinkedIn" }
        if ($Twitter) { $exportArgs += "-Twitter" }
        
        & ".\Create-Final-Video.ps1" @exportArgs
        
        # Preveri ustvarjene izvozne datoteke
        $exportFiles = Get-ChildItem -Path ".\videos\export\" -Filter "*.mp4" | Where-Object { $_.LastWriteTime -gt $StartTime }
        foreach ($file in $exportFiles) {
            $Results.Exports += $file.FullName
            Write-Log "Izvoz ustvarjen: $($file.Name)" "SUCCESS"
        }
        
    } catch {
        Write-Log "Napaka pri izvozu: $($_.Exception.Message)" "ERROR"
        $Results.Errors += "Napaka pri izvozu"
    }
} else {
    Write-Log "Preskacam izvoz" "INFO"
}

# KONCNI POVZETEK
$EndTime = Get-Date
$Results.Duration = $EndTime - $StartTime

Write-Host ""
Write-Host "KOMPLETNA AVTOMATIZACIJA KONCANA!" -ForegroundColor $Green
Write-Host "==================================" -ForegroundColor $Green

Write-Log "Skupen cas izvajanja: $($Results.Duration.ToString('hh\:mm\:ss'))" "SUCCESS"

if ($Results.Recording) {
    Write-Host "Posnetek: $([System.IO.Path]::GetFileName($Results.Recording))" -ForegroundColor $Cyan
}

if ($Results.PostProduction) {
    Write-Host "Koncni video: $([System.IO.Path]::GetFileName($Results.PostProduction))" -ForegroundColor $Cyan
}

if ($Results.Exports.Count -gt 0) {
    Write-Host "Izvozi za platforme:" -ForegroundColor $Cyan
    foreach ($export in $Results.Exports) {
        $fileName = [System.IO.Path]::GetFileName($export)
        $fileSize = (Get-Item $export).Length / 1MB
        Write-Host "  • $fileName ($([math]::Round($fileSize, 2)) MB)" -ForegroundColor $Yellow
    }
}

if ($Results.Errors.Count -gt 0) {
    Write-Host "Napake:" -ForegroundColor $Red
    foreach ($error in $Results.Errors) {
        Write-Host "  • $error" -ForegroundColor $Red
    }
}

# Ustvari končno poročilo
$reportPath = ".\VIDEO-REPORT-$(Get-Date -Format 'yyyy-MM-dd-HH-mm').md"
$reportContent = @"
# Omni Platform Video Automation Report

**Projekt:** $ProjectName  
**Datum:** $(Get-Date -Format 'dd.MM.yyyy HH:mm')  
**Trajanje:** $($Results.Duration.ToString('hh\:mm\:ss'))

## Rezultati

### Snemanje
$(if ($Results.Recording) { "Uspesno: $([System.IO.Path]::GetFileName($Results.Recording))" } else { "Neuspesno" })

### Postprodukcija
$(if ($Results.PostProduction) { "Uspesno: $([System.IO.Path]::GetFileName($Results.PostProduction))" } else { "Neuspesno" })

### Izvozi
$(if ($Results.Exports.Count -gt 0) {
    "Ustvarjenih $($Results.Exports.Count) verzij:`n" + 
    ($Results.Exports | ForEach-Object { "- $([System.IO.Path]::GetFileName($_))" }) -join "`n"
} else { "Ni izvozov" })

### Napake
$(if ($Results.Errors.Count -gt 0) {
    ($Results.Errors | ForEach-Object { "- $_" }) -join "`n"
} else { "Brez napak" })

## Datoteke

### Lokacije:
- **Posnetki:** .\videos\
- **Koncni videji:** .\videos\final\
- **Izvozi:** .\videos\export\
- **Log:** $LogFile

### Naslednji koraki:
1. Preveri kakovost videjev
2. Objavi na izbrane platforme
3. Arhiviraj projekt

---
*Ustvarjeno z Omni Platform Video Automation System*
"@

$reportContent | Out-File -FilePath $reportPath -Encoding UTF8
Write-Host "Porocilo ustvarjeno: $reportPath" -ForegroundColor $Green

# Odpri rezultate
if ($OpenResults) {
    if ($Results.Exports.Count -gt 0) {
        Write-Host "Odpiranje mape z izvozi..." -ForegroundColor $Cyan
        Start-Process "explorer.exe" -ArgumentList ".\videos\export\"
    } elseif ($Results.PostProduction) {
        Write-Host "Odpiranje mape s koncnim videom..." -ForegroundColor $Cyan
        Start-Process "explorer.exe" -ArgumentList "/select,`"$($Results.PostProduction)`""
    } elseif ($Results.Recording) {
        Write-Host "Odpiranje mape s posnetkom..." -ForegroundColor $Cyan
        Start-Process "explorer.exe" -ArgumentList "/select,`"$($Results.Recording)`""
    }
}

Write-Host ""
Write-Host "VIDEJI PRIPRAVLJENI ZA OBJAVO!" -ForegroundColor $Magenta
Write-Host "Hvala za uporabo Omni Platform Video Automation!" -ForegroundColor $Cyan

# Ponudi dodatne možnosti
Write-Host ""
Write-Host "DODATNE MOZNOSTI:" -ForegroundColor $Yellow
Write-Host "1. Ponovi celoten proces: .\Create-Complete-Video.ps1" -ForegroundColor $Cyan
Write-Host "2. Samo snemanje: .\Auto-Record-Demo.ps1" -ForegroundColor $Cyan
Write-Host "3. Samo postprodukcija: .\Post-Process-Video.ps1" -ForegroundColor $Cyan
Write-Host "4. Samo izvoz: .\Create-Final-Video.ps1" -ForegroundColor $Cyan

if (-not $OpenResults) {
    Read-Host "`nPritisni Enter za izhod"
}