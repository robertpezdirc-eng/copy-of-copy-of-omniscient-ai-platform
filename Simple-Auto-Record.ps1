# Omni Platform - PREPROSTO AVTOMATSKO SNEMANJE
# Enostavno snemanje demo videa z OBS brez FFmpeg

param(
    [string]$VideoName = "Omni-Demo-$(Get-Date -Format 'yyyy-MM-dd-HH-mm')",
    [int]$DemoLength = 95,
    [string]$OutputPath = ".\videos\"
)

# Barve za konzolo
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"
$Cyan = "Cyan"
$Magenta = "Magenta"

Clear-Host
Write-Host "OMNI PLATFORM - PREPROSTO AVTOMATSKO SNEMANJE" -ForegroundColor $Magenta
Write-Host "===============================================" -ForegroundColor $Magenta
Write-Host ""

# Ustvari mapo za videje
if (-not (Test-Path $OutputPath)) {
    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
    Write-Host "[INFO] Ustvarjena mapa: $OutputPath" -ForegroundColor $Cyan
}

# Preveri OBS
if (-not (Get-Process "obs64" -ErrorAction SilentlyContinue)) {
    Write-Host "[INFO] Zaganjam OBS Studio..." -ForegroundColor $Cyan
    try {
        Start-Process "obs64" -WindowStyle Normal
        Write-Host "[INFO] Cakam 10 sekund za zagon OBS..." -ForegroundColor $Yellow
        Start-Sleep 10
    } catch {
        Write-Host "[ERROR] OBS Studio ni namescen!" -ForegroundColor $Red
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

if (-not $serversOK) {
    Write-Host "[WARNING] Nekateri strezniki niso aktivni!" -ForegroundColor $Yellow
    Write-Host "[INFO] Zazeni streznike z: .\Launch-Omni-Demo.ps1" -ForegroundColor $Cyan
    Write-Host "[INFO] Nadaljujem z demo snemanjem..." -ForegroundColor $Cyan
}

# Odpri demo stran
Write-Host "[INFO] Odpiranje demo strani..." -ForegroundColor $Cyan
try {
    Start-Process "http://localhost:3000" -ErrorAction SilentlyContinue
} catch {
    Write-Host "[WARNING] Ni mogel odpreti brskalnika" -ForegroundColor $Yellow
}

Write-Host ""
Write-Host "PRIPRAVLJENO ZA SNEMANJE!" -ForegroundColor $Green
Write-Host "=========================" -ForegroundColor $Green
Write-Host ""
Write-Host "NAVODILA ZA SNEMANJE:" -ForegroundColor $Yellow
Write-Host "1. V OBS nastavi sceno za snemanje" -ForegroundColor $Cyan
Write-Host "2. Pritisni F1-F5 za preklop med scenami:" -ForegroundColor $Cyan
Write-Host "   - F1: Intro scena" -ForegroundColor White
Write-Host "   - F2: Demo scena (glavna)" -ForegroundColor White
Write-Host "   - F3: Health Check scena" -ForegroundColor White
Write-Host "   - F4: Brief scena" -ForegroundColor White
Write-Host "   - F5: Outro scena" -ForegroundColor White
Write-Host "3. Pritisni SPACE za zacetek/konec snemanja" -ForegroundColor $Cyan
Write-Host "4. Pritisni ESC za izhod iz snemanja" -ForegroundColor $Cyan
Write-Host ""

# Avtomatski scenarij
Write-Host "AVTOMATSKI SCENARIJ ($DemoLength sekund):" -ForegroundColor $Magenta
Write-Host "=========================================" -ForegroundColor $Magenta

$scenarios = @(
    @{ Scene = "F1"; Name = "Intro"; Duration = 5; Description = "Uvod v Omni Platform" },
    @{ Scene = "F2"; Name = "Demo"; Duration = 60; Description = "Glavna demonstracija" },
    @{ Scene = "F3"; Name = "Health"; Duration = 10; Description = "Preverjanje zdravja sistema" },
    @{ Scene = "F4"; Name = "Brief"; Duration = 15; Description = "Povzetek funkcionalnosti" },
    @{ Scene = "F5"; Name = "Outro"; Duration = 5; Description = "Zakljucek" }
)

foreach ($scenario in $scenarios) {
    Write-Host "- $($scenario.Scene): $($scenario.Name) ($($scenario.Duration)s) - $($scenario.Description)" -ForegroundColor White
}

Write-Host ""
Write-Host "ZACENJAM AVTOMATSKO SNEMANJE V 5 SEKUNDAH..." -ForegroundColor $Yellow
Write-Host "Pripravi OBS in demo stran!" -ForegroundColor $Yellow

# Odštevanje
for ($i = 5; $i -gt 0; $i--) {
    Write-Host "$i..." -ForegroundColor $Red
    Start-Sleep 1
}

Write-Host ""
Write-Host "ZACETEK SNEMANJA!" -ForegroundColor $Green

# Simulacija tipkovnih udarcev za OBS
Add-Type -AssemblyName System.Windows.Forms

# Zacni snemanje (SPACE)
Write-Host "[ACTION] Zacenjam snemanje..." -ForegroundColor $Magenta
[System.Windows.Forms.SendKeys]::SendWait(" ")
Start-Sleep 2

# Izvedi scenarij
foreach ($scenario in $scenarios) {
    Write-Host "[SCENE] $($scenario.Name) - $($scenario.Duration) sekund" -ForegroundColor $Cyan

    # Preklopi sceno
    [System.Windows.Forms.SendKeys]::SendWait($scenario.Scene)

    # Cakaj trajanje scene
    for ($i = 1; $i -le $scenario.Duration; $i++) {
        Write-Progress -Activity "Snemanje scene: $($scenario.Name)" -Status "$i/$($scenario.Duration) sekund" -PercentComplete (($i / $scenario.Duration) * 100)
        Start-Sleep 1
    }

    Write-Progress -Activity "Snemanje scene: $($scenario.Name)" -Completed
}

# Koncaj snemanje (SPACE)
Write-Host "[ACTION] Koncavam snemanje..." -ForegroundColor $Magenta
[System.Windows.Forms.SendKeys]::SendWait(" ")

Write-Host ""
Write-Host "SNEMANJE KONCANO!" -ForegroundColor $Green
Write-Host "=================" -ForegroundColor $Green

# Pocakaj, da se video shrani
Write-Host "[INFO] Cakam, da se video shrani..." -ForegroundColor $Cyan
Start-Sleep 5

# Najdi najnovejsi video
$videoFiles = Get-ChildItem -Path $OutputPath -Filter "*.mp4" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending

if ($videoFiles.Count -gt 0) {
    $latestVideo = $videoFiles[0]
    $videoSize = [math]::Round($latestVideo.Length / 1MB, 2)

    Write-Host "[SUCCESS] Video uspesno posnet!" -ForegroundColor $Green
    Write-Host "Datoteka: $($latestVideo.Name)" -ForegroundColor $Cyan
    Write-Host "Velikost: $videoSize MB" -ForegroundColor $Cyan
    Write-Host "Lokacija: $($latestVideo.FullName)" -ForegroundColor $Cyan

    # Odpri mapo z videom
    Write-Host "[INFO] Odpiranje mape z videom..." -ForegroundColor $Cyan
    Start-Process "explorer.exe" -ArgumentList "/select,`"$($latestVideo.FullName)`""

} else {
    Write-Host "[WARNING] Video datoteka ni bila najdena v $OutputPath" -ForegroundColor $Yellow
    Write-Host "[INFO] Preveri OBS nastavitve za shranjevanje" -ForegroundColor $Cyan

    # Odpri mapo za videje
    if (Test-Path $OutputPath) {
        Start-Process "explorer.exe" -ArgumentList $OutputPath
    }
}

Write-Host ""
Write-Host "NASLEDNJI KORAKI:" -ForegroundColor $Yellow
Write-Host "1. Preveri kakovost posnetka" -ForegroundColor $Cyan
Write-Host "2. Zazeni postprodukcijo: .\Post-Process-Video.ps1" -ForegroundColor $Cyan
Write-Host "3. Ustvari izvozne verzije: .\Create-Final-Video.ps1" -ForegroundColor $Cyan
Write-Host "4. Ali zazeni celoten proces: .\Create-Complete-Video.ps1" -ForegroundColor $Cyan

Write-Host ""
Write-Host "HVALA ZA UPORABO OMNI PLATFORM VIDEO SISTEMA!" -ForegroundColor $Magenta

Read-Host "`nPritisni Enter za izhod"
