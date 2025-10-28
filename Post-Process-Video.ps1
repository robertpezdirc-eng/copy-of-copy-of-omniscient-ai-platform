# Omni Platform - Video Postprodukcija
# Avtomatska obdelava posnetega videa z intro/outro, prehodi, zvok

param(
    [string]$InputVideo = "",
    [string]$OutputPath = ".\videos\final\",
    [string]$IntroVideo = ".\omni-platform\docs\overlays\intro.mp4",
    [string]$OutroVideo = ".\omni-platform\docs\overlays\outro.mp4",
    [switch]$SkipIntro = $false,
    [switch]$SkipOutro = $false
)

# Barve za konzolo
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"
$Cyan = "Cyan"

Write-Host "🎬 OMNI PLATFORM - VIDEO POSTPRODUKCIJA" -ForegroundColor $Cyan
Write-Host "=======================================" -ForegroundColor $Cyan

# Najdi najnovejši video če ni podan
if ([string]::IsNullOrEmpty($InputVideo)) {
    $videoFiles = Get-ChildItem -Path ".\videos\" -Filter "*.mp4" | Sort-Object LastWriteTime -Descending
    if ($videoFiles.Count -eq 0) {
        Write-Host "❌ Ni najdenih video datotek v .\videos\" -ForegroundColor $Red
        Write-Host "💡 Najprej zaženi: .\Auto-Record-Demo.ps1" -ForegroundColor $Cyan
        exit 1
    }
    $InputVideo = $videoFiles[0].FullName
    Write-Host "📹 Uporabim najnovejši video: $($videoFiles[0].Name)" -ForegroundColor $Green
}

# Preveri če datoteka obstaja
if (-not (Test-Path $InputVideo)) {
    Write-Host "❌ Video datoteka ne obstaja: $InputVideo" -ForegroundColor $Red
    exit 1
}

# Ustvari izhodno mapo
if (-not (Test-Path $OutputPath)) {
    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
    Write-Host "📁 Ustvarjena mapa: $OutputPath" -ForegroundColor $Green
}

# Preveri FFmpeg
function Test-FFmpeg {
    try {
        $null = & ffmpeg -version 2>$null
        return $true
    } catch {
        return $false
    }
}

if (-not (Test-FFmpeg)) {
    Write-Host "❌ FFmpeg ni nameščen ali ni v PATH" -ForegroundColor $Red
    Write-Host "💡 Namesti FFmpeg: https://ffmpeg.org/download.html" -ForegroundColor $Cyan
    Write-Host "💡 Ali uporabi: winget install FFmpeg" -ForegroundColor $Cyan
    exit 1
}

Write-Host "✅ FFmpeg je na voljo" -ForegroundColor $Green

# Ustvari intro/outro če ne obstajata
function Create-IntroOutro {
    Write-Host "🎨 Ustvarjam intro/outro videoe..." -ForegroundColor $Yellow
    
    # Ustvari intro (5 sekund)
    if (-not (Test-Path $IntroVideo) -and -not $SkipIntro) {
        Write-Host "📝 Ustvarjam intro video..." -ForegroundColor $Yellow
        $introText = "OMNI PLATFORM`nAI-Powered Demo"
        
        & ffmpeg -f lavfi -i "color=c=black:s=1920x1080:d=5" `
                 -vf "drawtext=text='$introText':fontcolor=white:fontsize=72:x=(w-text_w)/2:y=(h-text_h)/2:fontfile=arial.ttf" `
                 -c:v libx264 -pix_fmt yuv420p -y "$IntroVideo" 2>$null
        
        if (Test-Path $IntroVideo) {
            Write-Host "✅ Intro video ustvarjen" -ForegroundColor $Green
        }
    }
    
    # Ustvari outro (3 sekunde)
    if (-not (Test-Path $OutroVideo) -and -not $SkipOutro) {
        Write-Host "📝 Ustvarjam outro video..." -ForegroundColor $Yellow
        $outroText = "Hvala za ogled!`nwww.omni-platform.ai"
        
        & ffmpeg -f lavfi -i "color=c=black:s=1920x1080:d=3" `
                 -vf "drawtext=text='$outroText':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2:fontfile=arial.ttf" `
                 -c:v libx264 -pix_fmt yuv420p -y "$OutroVideo" 2>$null
        
        if (Test-Path $OutroVideo) {
            Write-Host "✅ Outro video ustvarjen" -ForegroundColor $Green
        }
    }
}

# Ustvari intro/outro
Create-IntroOutro

# Pripravi seznam videov za združevanje
$videoList = @()
$tempFiles = @()

if ((Test-Path $IntroVideo) -and -not $SkipIntro) {
    $videoList += $IntroVideo
    Write-Host "📹 Dodajam intro" -ForegroundColor $Cyan
}

$videoList += $InputVideo
Write-Host "📹 Dodajam glavni video" -ForegroundColor $Cyan

if ((Test-Path $OutroVideo) -and -not $SkipOutro) {
    $videoList += $OutroVideo
    Write-Host "📹 Dodajam outro" -ForegroundColor $Cyan
}

# Ustvari končno ime datoteke
$inputName = [System.IO.Path]::GetFileNameWithoutExtension($InputVideo)
$finalVideo = Join-Path $OutputPath "$inputName-FINAL.mp4"

Write-Host "🔧 Obdelavam video..." -ForegroundColor $Yellow

if ($videoList.Count -eq 1) {
    # Samo glavni video - dodaj audio filtre
    Write-Host "🎵 Dodajam audio izboljšave..." -ForegroundColor $Yellow
    
    & ffmpeg -i "$InputVideo" `
             -af "volume=1.2,highpass=f=80,lowpass=f=8000,dynaudnorm" `
             -c:v copy -c:a aac -b:a 192k `
             -y "$finalVideo"
             
} else {
    # Združi več videov
    Write-Host "🔗 Združujem videoe z prehodi..." -ForegroundColor $Yellow
    
    # Ustvari začasno datoteko s seznamom
    $listFile = Join-Path $env:TEMP "video_list.txt"
    $tempFiles += $listFile
    
    $listContent = ""
    foreach ($video in $videoList) {
        $listContent += "file '$video'`n"
    }
    $listContent | Out-File -FilePath $listFile -Encoding UTF8
    
    # Združi videoe z audio izboljšavami
    & ffmpeg -f concat -safe 0 -i "$listFile" `
             -af "volume=1.2,highpass=f=80,lowpass=f=8000,dynaudnorm" `
             -c:v libx264 -preset medium -crf 23 `
             -c:a aac -b:a 192k `
             -pix_fmt yuv420p `
             -y "$finalVideo"
}

# Počisti začasne datoteke
foreach ($tempFile in $tempFiles) {
    if (Test-Path $tempFile) {
        Remove-Item $tempFile -Force
    }
}

# Preveri rezultat
if (Test-Path $finalVideo) {
    $fileSize = (Get-Item $finalVideo).Length / 1MB
    Write-Host "✅ POSTPRODUKCIJA KONČANA!" -ForegroundColor $Green
    Write-Host "📁 Končni video: $finalVideo" -ForegroundColor $Cyan
    Write-Host "💾 Velikost: $([math]::Round($fileSize, 2)) MB" -ForegroundColor $Cyan
    
    # Pridobi informacije o videu
    Write-Host "📊 Informacije o videu:" -ForegroundColor $Yellow
    & ffprobe -v quiet -print_format json -show_format -show_streams "$finalVideo" | ConvertFrom-Json | ForEach-Object {
        $duration = [math]::Round([double]$_.format.duration, 1)
        Write-Host "⏱️  Trajanje: $duration sekund" -ForegroundColor $Cyan
        
        $videoStream = $_.streams | Where-Object { $_.codec_type -eq "video" } | Select-Object -First 1
        if ($videoStream) {
            Write-Host "📺 Resolucija: $($videoStream.width)x$($videoStream.height)" -ForegroundColor $Cyan
            Write-Host "🎞️  FPS: $($videoStream.r_frame_rate)" -ForegroundColor $Cyan
        }
    }
    
    # Odpri mapo z videom
    Write-Host "📂 Odpiranje mape z videom..." -ForegroundColor $Cyan
    Start-Process "explorer.exe" -ArgumentList "/select,`"$finalVideo`""
    
    return $finalVideo
    
} else {
    Write-Host "❌ Napaka pri postprodukciji!" -ForegroundColor $Red
    Write-Host "💡 Preveri FFmpeg nastavitve in poskusi znova" -ForegroundColor $Cyan
    exit 1
}

Write-Host "`n🎉 VIDEO PRIPRAVLJEN ZA OBJAVO!" -ForegroundColor $Green
Write-Host "📹 Lokacija: $finalVideo" -ForegroundColor $Cyan
Write-Host "🚀 Naslednji korak: .\Upload-Video.ps1" -ForegroundColor $Yellow