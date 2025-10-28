# Omni Platform - Avtomatski Video Recorder
# Samodejno snema celoten demo z OBS WebSocket API

param(
    [string]$OutputPath = ".\videos\",
    [string]$VideoName = "Omni-Demo-$(Get-Date -Format 'yyyy-MM-dd-HH-mm')",
    [int]$DemoLength = 95,
    [string]$OBSWebSocketPort = "4455"
)

# Barve za konzolo
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"
$Cyan = "Cyan"

Write-Host "🎬 OMNI PLATFORM - AVTOMATSKI VIDEO RECORDER" -ForegroundColor $Cyan
Write-Host "=============================================" -ForegroundColor $Cyan

# Preveri če obstaja OBS
function Test-OBSRunning {
    $obsProcess = Get-Process "obs64" -ErrorAction SilentlyContinue
    return $obsProcess -ne $null
}

# Preveri WebSocket povezavo
function Test-OBSWebSocket {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$OBSWebSocketPort" -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue
        return $true
    } catch {
        return $false
    }
}

# OBS WebSocket ukazi
function Send-OBSCommand {
    param([string]$Command, [hashtable]$Data = @{})
    
    $payload = @{
        "request-type" = $Command
        "message-id" = [System.Guid]::NewGuid().ToString()
    }
    
    if ($Data.Count -gt 0) {
        $payload["request-data"] = $Data
    }
    
    try {
        $json = $payload | ConvertTo-Json -Depth 10
        $response = Invoke-RestMethod -Uri "http://localhost:$OBSWebSocketPort/api" -Method POST -Body $json -ContentType "application/json"
        return $response
    } catch {
        Write-Host "❌ OBS ukaz neuspešen: $Command" -ForegroundColor $Red
        return $null
    }
}

# Preveri predpogoje
Write-Host "🔍 Preverjam predpogoje..." -ForegroundColor $Yellow

# Preveri strežnike
$frontendRunning = $false
$backendRunning = $false
$assetsRunning = $false

try {
    $frontendTest = Invoke-WebRequest -Uri "http://localhost:3000" -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue
    $frontendRunning = $true
    Write-Host "✅ Frontend strežnik (port 3000)" -ForegroundColor $Green
} catch {
    Write-Host "❌ Frontend strežnik ni aktiven" -ForegroundColor $Red
}

try {
    $backendTest = Invoke-WebRequest -Uri "http://localhost:8004/health" -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue
    $backendRunning = $true
    Write-Host "✅ Backend strežnik (port 8004)" -ForegroundColor $Green
} catch {
    Write-Host "❌ Backend strežnik ni aktiven" -ForegroundColor $Red
}

try {
    $assetsTest = Invoke-WebRequest -Uri "http://localhost:8009" -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue
    $assetsRunning = $true
    Write-Host "✅ Assets strežnik (port 8009)" -ForegroundColor $Green
} catch {
    Write-Host "❌ Assets strežnik ni aktiven" -ForegroundColor $Red
}

if (-not ($frontendRunning -and $backendRunning -and $assetsRunning)) {
    Write-Host "⚠️  Nekateri strežniki niso aktivni. Zaganjam..." -ForegroundColor $Yellow
    Write-Host "💡 Uporabi: .\Launch-Omni-Demo.ps1 za zagon strežnikov" -ForegroundColor $Cyan
    Start-Sleep 3
}

# Preveri OBS
if (-not (Test-OBSRunning)) {
    Write-Host "🚀 Zaganjam OBS Studio..." -ForegroundColor $Yellow
    try {
        Start-Process "obs64" -WindowStyle Minimized
        Start-Sleep 5
    } catch {
        Write-Host "❌ OBS ni nameščen ali ni v PATH" -ForegroundColor $Red
        Write-Host "💡 Namesti OBS Studio: https://obsproject.com/" -ForegroundColor $Cyan
        exit 1
    }
}

Write-Host "✅ OBS Studio je aktiven" -ForegroundColor $Green

# Ustvari izhodno mapo
if (-not (Test-Path $OutputPath)) {
    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
    Write-Host "📁 Ustvarjena mapa: $OutputPath" -ForegroundColor $Green
}

# Nastavi OBS za snemanje
Write-Host "⚙️  Nastavljam OBS za snemanje..." -ForegroundColor $Yellow

# Nastavi izhodno datoteko
$outputFile = Join-Path $OutputPath "$VideoName.mp4"
Send-OBSCommand -Command "SetRecordingFolder" -Data @{"rec-folder" = $OutputPath}
Send-OBSCommand -Command "SetFilenameFormatting" -Data @{"filename-formatting" = $VideoName}

Write-Host "📹 Video se bo shranil kot: $outputFile" -ForegroundColor $Cyan

# Avtomatska sekvenca snemanja
Write-Host "🎬 ZAČENJAM AVTOMATSKO SNEMANJE..." -ForegroundColor $Green
Write-Host "⏱️  Trajanje: $DemoLength sekund" -ForegroundColor $Cyan

# Zaženi demo stran
Write-Host "🌐 Odpiranje demo strani..." -ForegroundColor $Yellow
Start-Process "http://localhost:8009/omni-platform/docs/overlays/demo_autoplay.html"
Start-Sleep 3

# Začni snemanje
Write-Host "🔴 ZAČENJAM SNEMANJE..." -ForegroundColor $Red
Send-OBSCommand -Command "StartRecording"

# Avtomatska sekvenca scen (95 sekund)
$scenes = @(
    @{name="Intro"; duration=15; hotkey="F1"},
    @{name="Demo"; duration=45; hotkey="F2"},
    @{name="Health"; duration=10; hotkey="F3"},
    @{name="Brief"; duration=15; hotkey="F4"},
    @{name="Outro"; duration=10; hotkey="F5"}
)

$totalTime = 0
foreach ($scene in $scenes) {
    Write-Host "🎭 Preklapljam na sceno: $($scene.name) ($($scene.duration)s)" -ForegroundColor $Cyan
    
    # Pošlji hotkey za sceno
    Send-OBSCommand -Command "TriggerHotkeyByName" -Data @{"hotkeyName" = $scene.hotkey}
    
    # Čakaj trajanje scene
    $remaining = $scene.duration
    while ($remaining -gt 0) {
        Write-Host "⏳ $($scene.name): $remaining sekund" -ForegroundColor $Yellow
        Start-Sleep 1
        $remaining--
        $totalTime++
    }
}

# Ustavi snemanje
Write-Host "⏹️  USTAVLJAM SNEMANJE..." -ForegroundColor $Red
Send-OBSCommand -Command "StopRecording"

Write-Host "✅ SNEMANJE KONČANO!" -ForegroundColor $Green
Write-Host "📁 Video shranjen: $outputFile" -ForegroundColor $Cyan
Write-Host "⏱️  Skupno trajanje: $totalTime sekund" -ForegroundColor $Cyan

# Počakaj da se datoteka shrani
Write-Host "💾 Čakam da se video shrani..." -ForegroundColor $Yellow
Start-Sleep 5

# Preveri če datoteka obstaja
if (Test-Path $outputFile) {
    $fileSize = (Get-Item $outputFile).Length / 1MB
    Write-Host "✅ Video uspešno shranjen ($([math]::Round($fileSize, 2)) MB)" -ForegroundColor $Green
    
    # Odpri mapo z videom
    Write-Host "📂 Odpiranje mape z videom..." -ForegroundColor $Cyan
    Start-Process "explorer.exe" -ArgumentList "/select,`"$outputFile`""
    
} else {
    Write-Host "❌ Video datoteka ni bila najdena!" -ForegroundColor $Red
    Write-Host "💡 Preveri OBS nastavitve in poskusi znova" -ForegroundColor $Cyan
}

Write-Host "`n🎉 AVTOMATSKO SNEMANJE KONČANO!" -ForegroundColor $Green
Write-Host "📹 Video: $outputFile" -ForegroundColor $Cyan
Write-Host "⏱️  Trajanje: $DemoLength sekund" -ForegroundColor $Cyan
Write-Host "🎬 Pripravljen za objavo!" -ForegroundColor $Green

# Ponudi dodatne možnosti
Write-Host "`n🔧 DODATNE MOŽNOSTI:" -ForegroundColor $Yellow
Write-Host "1. .\Post-Process-Video.ps1 - Postprodukcija" -ForegroundColor $Cyan
Write-Host "2. .\Create-Final-Video.ps1 - Končni izvoz" -ForegroundColor $Cyan
Write-Host "3. .\Upload-Video.ps1 - Nalaganje na platforme" -ForegroundColor $Cyan

Read-Host "`nPritisni Enter za izhod"