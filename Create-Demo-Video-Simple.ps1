# Omni Platform - PREPROSTA IZDELAVA DEMO VIDEA
# Avtomatska izdelava demo videa brez potrebe po FFmpeg

param(
    [string]$ProjectName = "Omni-Demo-$(Get-Date -Format 'yyyy-MM-dd-HH-mm')",
    [int]$DemoLength = 95
)

# Barve za konzolo
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"
$Cyan = "Cyan"
$Magenta = "Magenta"

Clear-Host
Write-Host "OMNI PLATFORM - PREPROSTA IZDELAVA DEMO VIDEA" -ForegroundColor $Magenta
Write-Host "===============================================" -ForegroundColor $Magenta
Write-Host "AVTOMATSKA 1-KLIK RESITEV" -ForegroundColor $Cyan
Write-Host ""

$StartTime = Get-Date
Write-Host "[INFO] Zacenjam avtomatsko izdelavo videa: $ProjectName" -ForegroundColor $Cyan

# KORAK 1: PREVERI PREDPOGOJE
Write-Host ""
Write-Host "KORAK 1/3: Preverjam predpogoje..." -ForegroundColor $Magenta
Write-Host "===================================" -ForegroundColor $Magenta

# Preveri OBS
if (-not (Get-Process "obs64" -ErrorAction SilentlyContinue)) {
    Write-Host "[INFO] Zaganjam OBS Studio..." -ForegroundColor $Cyan
    try {
        Start-Process "obs64" -WindowStyle Normal
        Write-Host "[INFO] Cakam 10 sekund za zagon OBS..." -ForegroundColor $Yellow
        Start-Sleep 10
    } catch {
        Write-Host "[ERROR] OBS Studio ni namescen!" -ForegroundColor $Red
        Write-Host "[INFO] Namesti OBS Studio iz: https://obsproject.com/" -ForegroundColor $Cyan
        Read-Host "Pritisni Enter za izhod"
        exit 1
    }
} else {
    Write-Host "[SUCCESS] OBS Studio je ze zagnan" -ForegroundColor $Green
}

# Preveri streznike
Write-Host "[INFO] Preverjam streznike..." -ForegroundColor $Cyan

$serversOK = $true
try {
    $null = Invoke-WebRequest -Uri "http://localhost:3000" -Method GET -TimeoutSec 3 -ErrorAction Stop
    Write-Host "[SUCCESS] Frontend streznik (port 3000) - OK" -ForegroundColor $Green
} catch {
    Write-Host "[WARNING] Frontend streznik ni aktiven" -ForegroundColor $Yellow
    $serversOK = $false
}

try {
    $null = Invoke-WebRequest -Uri "http://localhost:8004/health" -Method GET -TimeoutSec 3 -ErrorAction Stop
    Write-Host "[SUCCESS] Backend streznik (port 8004) - OK" -ForegroundColor $Green
} catch {
    Write-Host "[WARNING] Backend streznik ni aktiven" -ForegroundColor $Yellow
    $serversOK = $false
}

try {
    $null = Invoke-WebRequest -Uri "http://localhost:8009" -Method GET -TimeoutSec 3 -ErrorAction Stop
    Write-Host "[SUCCESS] Assets streznik (port 8009) - OK" -ForegroundColor $Green
} catch {
    Write-Host "[WARNING] Assets streznik ni aktiven" -ForegroundColor $Yellow
    $serversOK = $false
}

if (-not $serversOK) {
    Write-Host "[WARNING] Nekateri strezniki niso aktivni!" -ForegroundColor $Yellow
    Write-Host "[INFO] Zazeni streznike z: .\Launch-Omni-Demo.ps1" -ForegroundColor $Cyan
    Write-Host "[INFO] Nadaljujem z demo snemanjem..." -ForegroundColor $Cyan
}

# KORAK 2: PRIPRAVI SNEMANJE
Write-Host ""
Write-Host "KORAK 2/3: Pripravljam snemanje..." -ForegroundColor $Magenta
Write-Host "===================================" -ForegroundColor $Magenta

# Ustvari mapo za videje
$videoPath = ".\videos\"
if (-not (Test-Path $videoPath)) {
    New-Item -ItemType Directory -Path $videoPath -Force | Out-Null
    Write-Host "[INFO] Ustvarjena mapa: $videoPath" -ForegroundColor $Cyan
}

# Odpri demo stran
Write-Host "[INFO] Odpiranje demo strani..." -ForegroundColor $Cyan
try {
    Start-Process "http://localhost:3000" -ErrorAction SilentlyContinue
    Start-Sleep 3
} catch {
    Write-Host "[WARNING] Ni mogel odpreti brskalnika" -ForegroundColor $Yellow
}

# KORAK 3: AVTOMATSKO SNEMANJE
Write-Host ""
Write-Host "KORAK 3/3: Avtomatsko snemanje..." -ForegroundColor $Magenta
Write-Host "==================================" -ForegroundColor $Magenta

Write-Host ""
Write-Host "DEMO SCENARIJ ($DemoLength sekund):" -ForegroundColor $Yellow
Write-Host "===================================" -ForegroundColor $Yellow

$scenarios = @(
    @{ Scene = "F1"; Name = "Intro"; Duration = 8; Description = "Uvod v Omni Platform" },
    @{ Scene = "F2"; Name = "Demo"; Duration = 50; Description = "Glavna demonstracija funkcionalnosti" },
    @{ Scene = "F3"; Name = "Health"; Duration = 12; Description = "Preverjanje zdravja sistema" },
    @{ Scene = "F4"; Name = "Brief"; Duration = 20; Description = "Povzetek in prednosti" },
    @{ Scene = "F5"; Name = "Outro"; Duration = 5; Description = "Zakljucek in kontakt" }
)

# Robustno izračunaj skupno trajanje in dodaj varnostni fallback
$totalDuration = ($scenarios | ForEach-Object { [int]$_['Duration'] } | Measure-Object -Sum).Sum
if (-not $totalDuration -or $totalDuration -eq 0) { $totalDuration = [int]$DemoLength }
Write-Host "Skupno trajanje: $totalDuration sekund" -ForegroundColor $Cyan
Write-Host ""

foreach ($scenario in $scenarios) {
    Write-Host "- $($scenario.Scene): $($scenario.Name) ($($scenario.Duration)s) - $($scenario.Description)" -ForegroundColor White
}

Write-Host ""
Write-Host "NAVODILA ZA UPORABNIKA:" -ForegroundColor $Yellow
Write-Host "======================" -ForegroundColor $Yellow
Write-Host "1. Prepricaj se, da je OBS pravilno nastavljen" -ForegroundColor $Cyan
Write-Host "2. Nastavi scene F1-F5 v OBS (Intro, Demo, Health, Brief, Outro)" -ForegroundColor $Cyan
Write-Host "3. Preveri, da je demo stran odprta v brskalniku" -ForegroundColor $Cyan
Write-Host "4. Pripravi se na avtomatsko snemanje" -ForegroundColor $Cyan
Write-Host ""

Write-Host "ZACENJAM AVTOMATSKO SNEMANJE V 10 SEKUNDAH..." -ForegroundColor $Yellow
Write-Host "Pripravi OBS in demo stran!" -ForegroundColor $Yellow

# Odštevanje
for ($i = 10; $i -gt 0; $i--) {
    Write-Host "$i..." -ForegroundColor $Red
    Start-Sleep 1
}

Write-Host ""
Write-Host "ZACETEK SNEMANJA!" -ForegroundColor $Green
Write-Host "=================" -ForegroundColor $Green

# Simulacija tipkovnih udarcev za OBS
Add-Type -AssemblyName System.Windows.Forms

# Zacni snemanje (SPACE)
Write-Host "[ACTION] Zacenjam snemanje..." -ForegroundColor $Magenta
[System.Windows.Forms.SendKeys]::SendWait(" ")
Start-Sleep 3

# Izvedi scenarij
$currentTime = 0
foreach ($scenario in $scenarios) {
    Write-Host ""
    Write-Host "[SCENE] $($scenario.Name) - $($scenario.Duration) sekund" -ForegroundColor $Cyan
    Write-Host "Opis: $($scenario.Description)" -ForegroundColor White
    
    # Preklopi sceno
    Write-Host "[HOTKEY] Pritiskam $($scenario.Scene)" -ForegroundColor $Yellow
    [System.Windows.Forms.SendKeys]::SendWait("{$($scenario.Scene)}")
    Start-Sleep 1
    
    # Cakaj trajanje scene z napredkom
    for ($i = 1; $i -le $scenario.Duration; $i++) {
        $currentTime++
        $percent = [math]::Min(100, [math]::Round(($currentTime / [double]$totalDuration) * 100, 1))
        Write-Progress -Activity "Snemanje demo videa" -Status "Scena: $($scenario.Name) ($i/$($scenario.Duration)s) - Skupno: $currentTime/$totalDuration s" -PercentComplete $percent
        Start-Sleep 1
    }
}

Write-Progress -Activity "Snemanje demo videa" -Completed

# Koncaj snemanje (SPACE)
Write-Host ""
Write-Host "[ACTION] Koncavam snemanje..." -ForegroundColor $Magenta
[System.Windows.Forms.SendKeys]::SendWait(" ")
Start-Sleep 2

Write-Host ""
Write-Host "SNEMANJE KONCANO!" -ForegroundColor $Green
Write-Host "=================" -ForegroundColor $Green

# Pocakaj, da se video shrani
Write-Host "[INFO] Cakam, da se video shrani..." -ForegroundColor $Cyan
Start-Sleep 8

# Najdi najnovejsi video
Write-Host "[INFO] Iscem posneti video..." -ForegroundColor $Cyan

# Preveri različne možne lokacije
$possiblePaths = @(
    $videoPath,
    "$env:USERPROFILE\Videos\",
    "$env:USERPROFILE\Desktop\",
    ".\",
    "$env:USERPROFILE\Documents\OBS\"
)

$foundVideo = $null
foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $videoFiles = Get-ChildItem -Path $path -Filter "*.mp4" -ErrorAction SilentlyContinue | 
                     Where-Object { $_.LastWriteTime -gt $StartTime } | 
                     Sort-Object LastWriteTime -Descending
        
        if ($videoFiles.Count -gt 0) {
            $foundVideo = $videoFiles[0]
            Write-Host "[SUCCESS] Video najden v: $path" -ForegroundColor $Green
            break
        }
    }
}

$EndTime = Get-Date
$Duration = $EndTime - $StartTime

Write-Host ""
Write-Host "REZULTAT AVTOMATSKE IZDELAVE VIDEA" -ForegroundColor $Magenta
Write-Host "===================================" -ForegroundColor $Magenta

Write-Host "Projekt: $ProjectName" -ForegroundColor $Cyan
Write-Host "Cas izvajanja: $($Duration.ToString('mm\:ss'))" -ForegroundColor $Cyan
Write-Host "Trajanje snemanja: $totalDuration sekund" -ForegroundColor $Cyan

if ($foundVideo) {
    $videoSize = [math]::Round($foundVideo.Length / 1MB, 2)
    
    Write-Host ""
    Write-Host "[SUCCESS] VIDEO USPESNO USTVARJEN!" -ForegroundColor $Green
    Write-Host "Datoteka: $($foundVideo.Name)" -ForegroundColor $Cyan
    Write-Host "Velikost: $videoSize MB" -ForegroundColor $Cyan
    Write-Host "Lokacija: $($foundVideo.FullName)" -ForegroundColor $Cyan
    Write-Host "Ustvarjen: $($foundVideo.LastWriteTime.ToString('dd.MM.yyyy HH:mm:ss'))" -ForegroundColor $Cyan
    
    # Odpri mapo z videom
    Write-Host ""
    Write-Host "[INFO] Odpiranje mape z videom..." -ForegroundColor $Cyan
    Start-Process "explorer.exe" -ArgumentList "/select,`"$($foundVideo.FullName)`""
    
    # Ustvari porocilo
    $reportPath = ".\VIDEO-REPORT-$ProjectName.md"
    $reportContent = @"
# Omni Platform Demo Video Report

**Projekt:** $ProjectName  
**Datum:** $(Get-Date -Format 'dd.MM.yyyy HH:mm')  
**Trajanje izdelave:** $($Duration.ToString('mm\:ss'))  
**Trajanje videa:** $totalDuration sekund

## Video Details

- **Datoteka:** $($foundVideo.Name)
- **Velikost:** $videoSize MB
- **Lokacija:** $($foundVideo.FullName)
- **Ustvarjen:** $($foundVideo.LastWriteTime.ToString('dd.MM.yyyy HH:mm:ss'))

## Scenarij

$(foreach ($scenario in $scenarios) {
    "- **$($scenario.Scene):** $($scenario.Name) ($($scenario.Duration)s) - $($scenario.Description)"
}) -join "`n"

## Status

✅ **USPESNO USTVARJEN**

## Naslednji koraki

1. Preveri kakovost videa
2. Po potrebi uredi z video urejevalnikom
3. Izvozi v različne formate za platforme
4. Objavi na želene kanale

---
*Ustvarjeno z Omni Platform Video Automation System*
"@

    $reportContent | Out-File -FilePath $reportPath -Encoding UTF8
    Write-Host "[INFO] Porocilo ustvarjeno: $reportPath" -ForegroundColor $Cyan
    
} else {
    Write-Host ""
    Write-Host "[WARNING] Video datoteka ni bila najdena!" -ForegroundColor $Yellow
    Write-Host "Možni razlogi:" -ForegroundColor Yellow
    Write-Host "- OBS ni bil pravilno nastavljen" -ForegroundColor White
    Write-Host "- Snemanje ni bilo zagnano" -ForegroundColor White
    Write-Host "- Video se shranjuje v drugo mapo" -ForegroundColor White
    Write-Host ""
    Write-Host "Preveri OBS nastavitve:" -ForegroundColor $Cyan
    Write-Host "1. File > Settings > Output" -ForegroundColor White
    Write-Host "2. Preveri Recording Path" -ForegroundColor White
    Write-Host "3. Preveri Recording Format (MP4)" -ForegroundColor White
    
    # Odpri mapo za videje
    if (Test-Path $videoPath) {
        Start-Process "explorer.exe" -ArgumentList $videoPath
    }
}

Write-Host ""
Write-Host "DODATNE MOZNOSTI:" -ForegroundColor $Yellow
Write-Host "=================" -ForegroundColor $Yellow
Write-Host "1. Ponovi snemanje: .\Create-Demo-Video-Simple.ps1" -ForegroundColor $Cyan
Write-Host "2. Ročno snemanje: .\Simple-Auto-Record.ps1" -ForegroundColor $Cyan
Write-Host "3. Zaženi OBS: obs64" -ForegroundColor $Cyan
Write-Host "4. Nastavi OBS scene: F1-F5" -ForegroundColor $Cyan

Write-Host ""
Write-Host "HVALA ZA UPORABO OMNI PLATFORM VIDEO SISTEMA!" -ForegroundColor $Magenta
Write-Host "Video je pripravljen za uporabo!" -ForegroundColor $Green

Read-Host "`nPritisni Enter za izhod"