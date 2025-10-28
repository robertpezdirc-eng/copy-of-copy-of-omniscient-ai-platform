# Omni Platform - Končni Video Izvoz
# Ustvari optimizirane verzije za različne platforme

param(
    [string]$InputVideo = "",
    [string]$OutputPath = ".\videos\export\",
    [switch]$YouTube = $true,
    [switch]$LinkedIn = $true,
    [switch]$Twitter = $true,
    [switch]$Instagram = $false,
    [switch]$TikTok = $false,
    [string]$Watermark = ".\omni-platform\docs\overlays\logo.png"
)

# Barve za konzolo
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"
$Cyan = "Cyan"

Write-Host "🎬 OMNI PLATFORM - KONČNI VIDEO IZVOZ" -ForegroundColor $Cyan
Write-Host "=====================================" -ForegroundColor $Cyan

# Najdi najnovejši FINAL video če ni podan
if ([string]::IsNullOrEmpty($InputVideo)) {
    $videoFiles = Get-ChildItem -Path ".\videos\final\" -Filter "*-FINAL.mp4" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    if ($videoFiles.Count -eq 0) {
        $videoFiles = Get-ChildItem -Path ".\videos\" -Filter "*.mp4" | Sort-Object LastWriteTime -Descending
    }
    
    if ($videoFiles.Count -eq 0) {
        Write-Host "❌ Ni najdenih video datotek!" -ForegroundColor $Red
        Write-Host "💡 Najprej zaženi: .\Auto-Record-Demo.ps1" -ForegroundColor $Cyan
        exit 1
    }
    
    $InputVideo = $videoFiles[0].FullName
    Write-Host "📹 Uporabim video: $($videoFiles[0].Name)" -ForegroundColor $Green
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
    exit 1
}

# Ustvari logo watermark če ne obstaja
if (-not (Test-Path $Watermark)) {
    Write-Host "🎨 Ustvarjam logo watermark..." -ForegroundColor $Yellow
    
    # Ustvari preprost SVG logo
    $logoSVG = @"
<svg width="200" height="60" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="60" fill="rgba(0,0,0,0.7)" rx="10"/>
  <text x="100" y="25" font-family="Arial" font-size="18" fill="white" text-anchor="middle" font-weight="bold">OMNI</text>
  <text x="100" y="45" font-family="Arial" font-size="12" fill="#00ff88" text-anchor="middle">PLATFORM</text>
</svg>
"@
    
    $logoPath = ".\omni-platform\docs\overlays\logo.svg"
    if (-not (Test-Path (Split-Path $logoPath))) {
        New-Item -ItemType Directory -Path (Split-Path $logoPath) -Force | Out-Null
    }
    $logoSVG | Out-File -FilePath $logoPath -Encoding UTF8
    
    # Konvertiraj v PNG
    if (Get-Command "magick" -ErrorAction SilentlyContinue) {
        & magick "$logoPath" "$Watermark"
        Write-Host "✅ Logo watermark ustvarjen" -ForegroundColor $Green
    } else {
        Write-Host "⚠️  ImageMagick ni nameščen - preskačem watermark" -ForegroundColor $Yellow
        $Watermark = ""
    }
}

# Pridobi osnovne informacije o videu
Write-Host "📊 Analiziram vhodni video..." -ForegroundColor $Yellow
$videoInfo = & ffprobe -v quiet -print_format json -show_format -show_streams "$InputVideo" | ConvertFrom-Json
$duration = [math]::Round([double]$videoInfo.format.duration, 1)
$videoStream = $videoInfo.streams | Where-Object { $_.codec_type -eq "video" } | Select-Object -First 1

Write-Host "⏱️  Trajanje: $duration sekund" -ForegroundColor $Cyan
Write-Host "📺 Resolucija: $($videoStream.width)x$($videoStream.height)" -ForegroundColor $Cyan

# Funkcija za izvoz
function Export-Video {
    param(
        [string]$Platform,
        [string]$Resolution,
        [string]$Bitrate,
        [string]$AudioBitrate = "128k",
        [string]$AdditionalFilters = "",
        [string]$MaxDuration = ""
    )
    
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($InputVideo)
    $outputFile = Join-Path $OutputPath "$baseName-$Platform.mp4"
    
    Write-Host "🎬 Izvažam za $Platform ($Resolution)..." -ForegroundColor $Yellow
    
    # Sestavi video filtre
    $videoFilters = @()
    
    # Dodaj watermark če obstaja
    if (-not [string]::IsNullOrEmpty($Watermark) -and (Test-Path $Watermark)) {
        $videoFilters += "movie=$Watermark [logo]; [in][logo] overlay=W-w-20:20:enable='gte(t,2)'"
    }
    
    # Dodaj resolucijo
    if ($Resolution -ne "original") {
        $videoFilters += "scale=$Resolution:force_original_aspect_ratio=decrease,pad=$Resolution:(ow-iw)/2:(oh-ih)/2:black"
    }
    
    # Dodaj dodatne filtre
    if (-not [string]::IsNullOrEmpty($AdditionalFilters)) {
        $videoFilters += $AdditionalFilters
    }
    
    # Sestavi ukaz
    $ffmpegArgs = @(
        "-i", "`"$InputVideo`""
    )
    
    if ($videoFilters.Count -gt 0) {
        $ffmpegArgs += "-vf", ($videoFilters -join ",")
    }
    
    $ffmpegArgs += @(
        "-c:v", "libx264"
        "-preset", "medium"
        "-crf", "23"
        "-maxrate", $Bitrate
        "-bufsize", ([int]($Bitrate.Replace("k","")) * 2).ToString() + "k"
        "-c:a", "aac"
        "-b:a", $AudioBitrate
        "-pix_fmt", "yuv420p"
        "-movflags", "+faststart"
    )
    
    # Dodaj omejitev trajanja če je podana
    if (-not [string]::IsNullOrEmpty($MaxDuration)) {
        $ffmpegArgs += "-t", $MaxDuration
    }
    
    $ffmpegArgs += @("-y", "`"$outputFile`"")
    
    # Izvrši ukaz
    $ffmpegCmd = "ffmpeg " + ($ffmpegArgs -join " ")
    Invoke-Expression $ffmpegCmd
    
    if (Test-Path $outputFile) {
        $fileSize = (Get-Item $outputFile).Length / 1MB
        Write-Host "✅ $Platform verzija ustvarjena ($([math]::Round($fileSize, 2)) MB)" -ForegroundColor $Green
        return $outputFile
    } else {
        Write-Host "❌ Napaka pri ustvarjanju $Platform verzije" -ForegroundColor $Red
        return $null
    }
}

# Izvozi za različne platforme
$exportedVideos = @()

if ($YouTube) {
    $video = Export-Video -Platform "YouTube" -Resolution "1920x1080" -Bitrate "8000k" -AudioBitrate "192k"
    if ($video) { $exportedVideos += @{Platform="YouTube"; File=$video; Description="Optimizirano za YouTube (1080p, 8Mbps)"} }
}

if ($LinkedIn) {
    $video = Export-Video -Platform "LinkedIn" -Resolution "1280x720" -Bitrate "5000k" -AudioBitrate "128k"
    if ($video) { $exportedVideos += @{Platform="LinkedIn"; File=$video; Description="Optimizirano za LinkedIn (720p, 5Mbps)"} }
}

if ($Twitter) {
    # Twitter ima omejitev 2:20 (140 sekund)
    $maxDuration = if ($duration -gt 140) { "140" } else { "" }
    $video = Export-Video -Platform "Twitter" -Resolution "1280x720" -Bitrate "6000k" -AudioBitrate="128k" -MaxDuration $maxDuration
    if ($video) { $exportedVideos += @{Platform="Twitter"; File=$video; Description="Optimizirano za Twitter (720p, max 2:20)"} }
}

if ($Instagram) {
    $video = Export-Video -Platform "Instagram" -Resolution "1080x1080" -Bitrate="3500k" -AudioBitrate="128k" -AdditionalFilters="crop=min(iw\,ih):min(iw\,ih)"
    if ($video) { $exportedVideos += @{Platform="Instagram"; File=$video; Description="Optimizirano za Instagram (kvadrat, 1080x1080)"} }
}

if ($TikTok) {
    $video = Export-Video -Platform "TikTok" -Resolution "1080x1920" -Bitrate="4000k" -AudioBitrate="128k" -AdditionalFilters="crop=ih*9/16:ih"
    if ($video) { $exportedVideos += @{Platform="TikTok"; File=$video; Description="Optimizirano za TikTok (vertikalno, 9:16)"} }
}

# Ustvari povzetek
Write-Host "`n🎉 IZVOZ KONČAN!" -ForegroundColor $Green
Write-Host "===============" -ForegroundColor $Green

if ($exportedVideos.Count -gt 0) {
    Write-Host "📹 Ustvarjene verzije:" -ForegroundColor $Cyan
    foreach ($video in $exportedVideos) {
        $fileSize = (Get-Item $video.File).Length / 1MB
        Write-Host "  • $($video.Platform): $([math]::Round($fileSize, 2)) MB" -ForegroundColor $Yellow
        Write-Host "    $($video.Description)" -ForegroundColor $Gray
        Write-Host "    📁 $($video.File)" -ForegroundColor $Gray
    }
    
    # Ustvari README z navodili
    $readmePath = Join-Path $OutputPath "README-EXPORT.md"
    $readmeContent = @"
# Omni Platform Demo - Izvoženi Videji

Datum izvoza: $(Get-Date -Format 'dd.MM.yyyy HH:mm')
Vhodni video: $InputVideo
Trajanje: $duration sekund

## Ustvarjene verzije:

"@
    
    foreach ($video in $exportedVideos) {
        $fileSize = (Get-Item $video.File).Length / 1MB
        $readmeContent += @"

### $($video.Platform)
- **Datoteka:** $([System.IO.Path]::GetFileName($video.File))
- **Velikost:** $([math]::Round($fileSize, 2)) MB
- **Opis:** $($video.Description)

"@
    }
    
    $readmeContent += @"

## Navodila za objavo:

### YouTube
- Optimalna kakovost za YouTube
- Priporočene oznake: #OmniPlatform #AI #Demo #Technology

### LinkedIn
- Primerno za poslovne objave
- Dodaj opis z ključnimi besedami

### Twitter
- Omejeno na 2:20 če je video daljši
- Uporabi relevantne hashtage

## Tehnične specifikacije:
- Kodek: H.264 (libx264)
- Audio: AAC
- Pixel format: yuv420p
- Optimizirano za spletno predvajanje (faststart)

---
Ustvarjeno z Omni Platform Video Automation System
"@
    
    $readmeContent | Out-File -FilePath $readmePath -Encoding UTF8
    Write-Host "📄 Ustvarjen README: $readmePath" -ForegroundColor $Green
    
    # Odpri mapo z videji
    Write-Host "📂 Odpiranje mape z videji..." -ForegroundColor $Cyan
    Start-Process "explorer.exe" -ArgumentList "`"$OutputPath`""
    
} else {
    Write-Host "❌ Nobena verzija ni bila uspešno ustvarjena!" -ForegroundColor $Red
}

Write-Host "`n🚀 VIDEJI PRIPRAVLJENI ZA OBJAVO!" -ForegroundColor $Green
Write-Host "📁 Lokacija: $OutputPath" -ForegroundColor $Cyan

Read-Host "`nPritisni Enter za izhod"