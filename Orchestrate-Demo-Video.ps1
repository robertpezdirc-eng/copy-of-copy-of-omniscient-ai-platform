# Omni Platform - Orkestrator snemanja in postprodukcije z glasovnim opisom
param(
    [int]$DemoLength = 60,
    [string]$ProjectName = "Omni-Demo-$(Get-Date -Format 'yyyy-MM-dd-HH-mm')"
)

$ErrorActionPreference = 'Stop'
$startTime = Get-Date
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$videosDir = Join-Path $root 'videos'
$finalDir = Join-Path $videosDir 'final'

if (-not (Test-Path $videosDir)) { New-Item -ItemType Directory -Path $videosDir -Force | Out-Null }
if (-not (Test-Path $finalDir)) { New-Item -ItemType Directory -Path $finalDir -Force | Out-Null }

Write-Host "[INFO] Zagon snemanja demo videa ($DemoLength s) in priprava glasovnega opisa" -ForegroundColor Cyan

# 1) Generiraj glasovni opis (TTS -> WAV)
Add-Type -AssemblyName System.Speech
$tts = New-Object System.Speech.Synthesis.SpeechSynthesizer
$tts.Rate = 0
$tts.Volume = 100
$voiceoverPath = Join-Path $videosDir "voiceover-$ProjectName.wav"

$voiceText = @'
Pozdravljeni v Omni Platform, enotni rešitvi za gradnjo in orkestracijo AI aplikacij.
V uvodu na kratko predstavimo namen in glavne prednosti platforme.
Sledi glavna demonstracija, kjer prikažemo uporabniški vmesnik, zajem podatkov in pametno obdelavo.
Nato preverimo zdravje sistema in integracije, da potrdimo stabilnost okolja.
Na kratko povzamemo ključne funkcije, nato zaključimo in nakažemo naslednje korake.
Hvala za pozornost.
'@
$tts.SetOutputToWaveFile($voiceoverPath)
$tts.Speak($voiceText)
$tts.SetOutputToNull()
Write-Host "[SUCCESS] Glasovni opis ustvarjen: $voiceoverPath" -ForegroundColor Green

# 2) Zaženi snemanje v ločenem procesu
$recordScript = Join-Path $root 'Create-Demo-Video-Simple.ps1'
if (-not (Test-Path $recordScript)) { throw "Skript ni najden: $recordScript" }
Write-Host "[INFO] Zagon snemanja: $recordScript -DemoLength $DemoLength" -ForegroundColor Magenta
Start-Process -FilePath "powershell" -ArgumentList "-ExecutionPolicy Bypass -File `"$recordScript`" -DemoLength $DemoLength" -WindowStyle Normal | Out-Null

# 3) Poišči najnovejši video posnetek, ustvarjen po $startTime
Write-Host "[INFO] Čakam na posneti video..." -ForegroundColor Yellow
$inputVideo = $null
$searchPaths = @(
    $videosDir,
    "$env:USERPROFILE\Videos\",
    "$env:USERPROFILE\Desktop\",
    (Join-Path $root '.')
)

while (-not $inputVideo) {
    foreach ($path in $searchPaths) {
        if (Test-Path $path) {
            $vf = Get-ChildItem -Path $path -Filter "*.mp4" -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -gt $startTime } | Sort-Object LastWriteTime -Descending
            if ($vf.Count -gt 0) { $inputVideo = $vf[0]; break }
        }
    }
    if (-not $inputVideo) { Start-Sleep -Seconds 5 }
}
Write-Host "[SUCCESS] Video najden: $($inputVideo.FullName)" -ForegroundColor Green

# 4) Najdi ffmpeg/ffprobe
function Find-Exe {
    param([string]$name)
    $cmd = (Get-Command $name -ErrorAction SilentlyContinue)
    if ($cmd) { return $cmd.Source }
    $candidates = @(
        "C:\\ffmpeg\\bin\\$name.exe",
        "C:\\Program Files\\ffmpeg\\bin\\$name.exe",
        "C:\\Program Files (x86)\\ffmpeg\\bin\\$name.exe",
        "C:\\ProgramData\\chocolatey\\bin\\$name.exe"
    )
    foreach ($c in $candidates) { if (Test-Path $c) { return $c } }
    return $null
}

$ffmpeg = Find-Exe 'ffmpeg'
$ffprobe = Find-Exe 'ffprobe'
if (-not $ffmpeg) { throw 'FFmpeg ni najden v PATH ali tipičnih lokacijah.' }
Write-Host "[INFO] Uporabljam FFmpeg: $ffmpeg" -ForegroundColor Cyan

# 5) Določi trajanje videa
function Get-DurationSeconds {
    param([string]$videoPath)
    if ($ffprobe) {
        $out = & $ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$videoPath"
        if ($out -and [double]::TryParse($out, [ref]([double]$null))) { return [double]$out }
    }
    $info = & $ffmpeg -i "$videoPath" 2>&1 | Out-String
    $m = [regex]::Match($info, 'Duration:\s*(\d{2}):(\d{2}):(\d{2})\.(\d{2})')
    if ($m.Success) {
        $h = [int]$m.Groups[1].Value; $mi = [int]$m.Groups[2].Value; $s = [int]$m.Groups[3].Value
        return [double]($h*3600 + $mi*60 + $s)
    }
    return 0
}

$duration = Get-DurationSeconds $inputVideo.FullName
if ($duration -le 0) { $duration = [double]$DemoLength }
$fadeOutStart = [math]::Max(1, $duration - 1)
Write-Host "[INFO] Trajanje videa: $duration s, fade-out start: $fadeOutStart s" -ForegroundColor Cyan

# 6) Ustvari intro in outro (črno ozadje + besedilo)
$intro = Join-Path $videosDir "intro-$ProjectName.mp4"
$outro = Join-Path $videosDir "outro-$ProjectName.mp4"

& $ffmpeg -y -f lavfi -i "color=c=black:s=1920x1080:d=4" -vf "drawtext=text='Omni Platform — Demo':fontcolor=white:fontsize=64:x=(w-text_w)/2:y=(h-text_h)/2" -c:v libx264 -pix_fmt yuv420p -r 30 -t 4 -c:a aac -ar 44100 -ac 2 "$intro"
& $ffmpeg -y -f lavfi -i "color=c=black:s=1920x1080:d=4" -vf "drawtext=text='Hvala za ogled':fontcolor=white:fontsize=64:x=(w-text_w)/2:y=(h-text_h)/2" -c:v libx264 -pix_fmt yuv420p -r 30 -t 4 -c:a aac -ar 44100 -ac 2 "$outro"
Write-Host "[SUCCESS] Intro in outro ustvarjena." -ForegroundColor Green

# 7) Obdelaj glavni video (fade in/out + mix z glasom + zmerna glasnost)
$processed = Join-Path $videosDir "processed-$ProjectName.mp4"
$fc = "[0:v]fade=t=in:st=0:d=1,fade=t=out:st=$fadeOutStart:d=1[v];[0:a][1:a]amix=inputs=2:duration=longest:weights=0.7 1.0[a]"
& $ffmpeg -y -i "$($inputVideo.FullName)" -i "$voiceoverPath" -filter_complex "$fc" -map "[v]" -map "[a]" -c:v libx264 -preset veryfast -crf 23 -c:a aac -b:a 192k "$processed"
Write-Host "[SUCCESS] Glavni video obdelan: $processed" -ForegroundColor Green

# 8) Združi intro + processed + outro v končni video
$final = Join-Path $finalDir "$ProjectName-final.mp4"
& $ffmpeg -y -i "$intro" -i "$processed" -i "$outro" -filter_complex "[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1[v][a]" -map "[v]" -map "[a]" -c:v libx264 -preset veryfast -crf 23 -c:a aac -b:a 192k "$final"
Write-Host "[SUCCESS] Končni video ustvarjen: $final" -ForegroundColor Green

# 9) Odpri mapo z rezultati
Start-Process "explorer.exe" -ArgumentList "/select,`"$final`""

# 10) Porocilo
$reportPath = Join-Path $finalDir ("VIDEO-REPORT-" + $ProjectName + ".md")
$report = @"
# Omni Platform Demo Video Report

**Projekt:** $ProjectName
**Datum:** $(Get-Date -Format 'dd.MM.yyyy HH:mm')
**Končni video:** $final

## Glasovni opis
- Datoteka: $voiceoverPath
- Besedilo:
$voiceText

## Postprodukcija
- Fade-in/out: 1s na začetku, 1s na koncu
- Glasnost: zmerna, z mešanjem glasovnega opisa in izvirnega zvoka
- Intro/Outro: črno ozadje z besedilom

— Ustvarjeno avtomatsko z Orchestrate-Demo-Video.ps1
"@
$report | Out-File -FilePath $reportPath -Encoding UTF8
Write-Host "[INFO] Porocilo zapisano: $reportPath" -ForegroundColor Cyan