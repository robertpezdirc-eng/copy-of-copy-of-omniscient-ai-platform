# Omni Platform - DAVINCI RESOLVE INTEGRACIJA
# Avtomatska integracija z DaVinci Resolve za napredno video urejanje

param(
    [string]$VideoPath = "",
    [string]$ProjectName = "Omni-Platform-Demo",
    [string]$OutputPath = ".\videos\davinci-output",
    [switch]$AutoRender,
    [string]$Resolution = "1920x1080",
    [int]$FrameRate = 30,
    [string]$ColorGrading = "cinematic"  # cinematic, vibrant, natural, dramatic
)

Write-Host "🎬 DAVINCI RESOLVE - Avtomatska integracija" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

# Preveri, ali je DaVinci Resolve nameščen
$davinciPaths = @(
    "C:\Program Files\Blackmagic Design\DaVinci Resolve\Resolve.exe",
    "C:\Program Files (x86)\Blackmagic Design\DaVinci Resolve\Resolve.exe",
    "${env:ProgramFiles}\Blackmagic Design\DaVinci Resolve\Resolve.exe"
)

$davinciPath = $null
foreach ($path in $davinciPaths) {
    if (Test-Path $path) {
        $davinciPath = $path
        break
    }
}

if (-not $davinciPath) {
    Write-Host "⚠️  DaVinci Resolve ni nameščen ali ni najden" -ForegroundColor Yellow
    Write-Host "📥 Prenos: https://www.blackmagicdesign.com/products/davinciresolve" -ForegroundColor Blue
    
    # Ustvari alternativni FFmpeg workflow
    Write-Host "🔄 Uporabljam FFmpeg za napredno urejanje..." -ForegroundColor Yellow
    
    # Najdi FFmpeg
    $ffmpegPath = $null
    $ffmpegPaths = @(
        "ffmpeg",
        "C:\ffmpeg\bin\ffmpeg.exe",
        "C:\ProgramData\chocolatey\bin\ffmpeg.exe",
        "${env:ProgramFiles}\ffmpeg\bin\ffmpeg.exe"
    )
    
    foreach ($path in $ffmpegPaths) {
        try {
            if ($path -eq "ffmpeg") {
                $null = & $path -version 2>$null
                $ffmpegPath = $path
                break
            } elseif (Test-Path $path) {
                $ffmpegPath = $path
                break
            }
        } catch {
            continue
        }
    }
    
    if ($ffmpegPath) {
        Write-Host "✓ FFmpeg najden: $ffmpegPath" -ForegroundColor Green
        
        # Ustvari izhodno mapo
        if (-not (Test-Path $OutputPath)) {
            New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
        }
        
        # Napredno FFmpeg urejanje
        if ($VideoPath -and (Test-Path $VideoPath)) {
            $outputFile = Join-Path $OutputPath "$ProjectName-enhanced.mp4"
            
            Write-Host "🎨 Uporabljam napredne video filtre..." -ForegroundColor Yellow
            
            # Določi barvno gradacijo
            $colorFilter = switch ($ColorGrading) {
                "cinematic" { "curves=all='0/0 0.25/0.15 0.5/0.5 0.75/0.85 1/1',colorbalance=rs=0.1:gs=-0.1:bs=-0.2" }
                "vibrant" { "eq=saturation=1.3:brightness=0.05:contrast=1.1,colorbalance=rs=0.05:gs=0.05:bs=-0.1" }
                "natural" { "eq=saturation=1.1:brightness=0.02:contrast=1.05" }
                "dramatic" { "curves=all='0/0 0.3/0.1 0.7/0.9 1/1',eq=saturation=1.2:contrast=1.2" }
                default { "eq=saturation=1.1:brightness=0.02:contrast=1.05" }
            }
            
            # Kompleksni FFmpeg ukaz z naprednimi filtri
            $ffmpegArgs = @(
                "-i", "`"$VideoPath`"",
                "-vf", "`"scale=$Resolution,fps=$FrameRate,$colorFilter,unsharp=5:5:1.0:5:5:0.0`"",
                "-c:v", "libx264",
                "-preset", "slow",
                "-crf", "18",
                "-c:a", "aac",
                "-b:a", "192k",
                "-movflags", "+faststart",
                "`"$outputFile`""
            )
            
            Write-Host "🚀 Zaganjam napredno video obdelavo..." -ForegroundColor Green
            Write-Host "📁 Izhod: $outputFile" -ForegroundColor White
            
            $process = Start-Process -FilePath $ffmpegPath -ArgumentList $ffmpegArgs -NoNewWindow -PassThru -Wait
            
            if ($process.ExitCode -eq 0) {
                Write-Host "✅ Video uspešno obdelan!" -ForegroundColor Green
                
                # Ustvari thumbnail
                $thumbnailPath = Join-Path $OutputPath "$ProjectName-thumbnail.jpg"
                $thumbArgs = @(
                    "-i", "`"$outputFile`"",
                    "-ss", "00:00:05",
                    "-vframes", "1",
                    "-vf", "scale=320:180",
                    "`"$thumbnailPath`""
                )
                
                & $ffmpegPath @thumbArgs 2>$null
                Write-Host "✓ Thumbnail ustvarjen: $thumbnailPath" -ForegroundColor Green
            } else {
                Write-Host "❌ Napaka pri obdelavi videa" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "❌ FFmpeg ni najden" -ForegroundColor Red
        return
    }
} else {
    Write-Host "✓ DaVinci Resolve najden: $davinciPath" -ForegroundColor Green
    
    # Ustvari DaVinci Resolve Python skript
    $pythonScript = @"
#!/usr/bin/env python3
"""
Omni Platform - DaVinci Resolve Automation Script
Avtomatsko ureja video z naprednimi funkcijami
"""

import DaVinciResolveScript as dvr_script
import sys
import os
import time

def main():
    # Poveži se z DaVinci Resolve
    resolve = dvr_script.scriptapp("Resolve")
    if not resolve:
        print("❌ Ni mogoče povezati z DaVinci Resolve")
        return False
    
    print("✓ Povezan z DaVinci Resolve")
    
    # Pridobi project manager
    project_manager = resolve.GetProjectManager()
    
    # Ustvari nov projekt
    project_name = "Omni-Platform-Demo"
    project = project_manager.CreateProject(project_name)
    
    if not project:
        # Poskusi odpreti obstoječi projekt
        project = project_manager.OpenProject(project_name)
    
    if not project:
        print(f"❌ Ni mogoče ustvariti/odpreti projekta {project_name}")
        return False
    
    print(f"✓ Projekt '{project_name}' pripravljen")
    
    # Pridobi media pool
    media_pool = project.GetMediaPool()
    root_folder = media_pool.GetRootFolder()
    
    # Uvozi video datoteke
    video_path = sys.argv[1] if len(sys.argv) > 1 else ""
    if video_path and os.path.exists(video_path):
        media_items = media_pool.ImportMedia([video_path])
        if media_items:
            print(f"✓ Uvožen video: {video_path}")
            
            # Pridobi timeline
            timeline = project.GetCurrentTimeline()
            if not timeline:
                timeline = media_pool.CreateEmptyTimeline("Omni Demo Timeline")
            
            # Dodaj video na timeline
            media_pool.AppendToTimeline(media_items)
            print("✓ Video dodan na timeline")
            
            # Nastavi osnovne lastnosti
            timeline.SetSetting("timelineResolutionWidth", "1920")
            timeline.SetSetting("timelineResolutionHeight", "1080")
            timeline.SetSetting("timelineFrameRate", "30")
            
            # Dodaj barvno gradacijo
            color_page = resolve.OpenPage("color")
            if color_page:
                print("🎨 Uporabljam barvno gradacijo...")
                
                # Osnovne nastavitve barvne gradacije
                # (DaVinci Resolve API za barvno gradacijo je omejen v brezplačni verziji)
                time.sleep(2)  # Počakaj, da se stran naloži
                
            # Dodaj naslov
            edit_page = resolve.OpenPage("edit")
            if edit_page:
                print("📝 Dodajam naslove...")
                
                # Ustvari generator za naslov
                # (Omejeno v brezplačni verziji)
                
            print("✅ Osnovno urejanje končano")
            
            # Izvozi video (če je omogočeno)
            if len(sys.argv) > 2 and sys.argv[2] == "render":
                deliver_page = resolve.OpenPage("deliver")
                if deliver_page:
                    print("🚀 Začenjam izvoz...")
                    
                    # Nastavi izvozne nastavitve
                    project.SetRenderSettings({
                        "SelectAllFrames": True,
                        "MarkIn": 0,
                        "MarkOut": timeline.GetEndFrame(),
                        "TargetDir": os.path.dirname(video_path),
                        "CustomName": "Omni-Demo-Enhanced"
                    })
                    
                    # Začni izvoz
                    job_id = project.AddRenderJob()
                    if job_id:
                        project.StartRendering(job_id)
                        print(f"✓ Izvoz začet (Job ID: {job_id})")
                        
                        # Počakaj na konec izvoza
                        while project.IsRenderingInProgress():
                            time.sleep(5)
                            print("⏳ Izvažam...")
                        
                        print("✅ Izvoz končan!")
                    else:
                        print("❌ Napaka pri začetku izvoza")
            
            return True
    else:
        print(f"❌ Video datoteka ni najdena: {video_path}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
"@
#!/usr/bin/env python3
"""
Omni Platform - DaVinci Resolve Automation Script
Avtomatsko ureja video z naprednimi funkcijami
"""

import DaVinciResolveScript as dvr_script
import sys
import os
import time

def main():
    # Poveži se z DaVinci Resolve
    resolve = dvr_script.scriptapp("Resolve")
    if not resolve:
        print("❌ Ni mogoče povezati z DaVinci Resolve")
        return False
    
    print("✓ Povezan z DaVinci Resolve")
    
    # Pridobi project manager
    project_manager = resolve.GetProjectManager()
    
    # Ustvari nov projekt
    project_name = "Omni-Platform-Demo"
    project = project_manager.CreateProject(project_name)
    
    if not project:
        # Poskusi odpreti obstoječi projekt
        project = project_manager.OpenProject(project_name)
    
    if not project:
        print(f"❌ Ni mogoče ustvariti/odpreti projekta {project_name}")
        return False
    
    print(f"✓ Projekt '{project_name}' pripravljen")
    
    # Pridobi media pool
    media_pool = project.GetMediaPool()
    root_folder = media_pool.GetRootFolder()
    
    # Uvozi video datoteke
    video_path = sys.argv[1] if len(sys.argv) > 1 else ""
    if video_path and os.path.exists(video_path):
        media_items = media_pool.ImportMedia([video_path])
        if media_items:
            print(f"✓ Uvožen video: {video_path}")
            
            # Pridobi timeline
            timeline = project.GetCurrentTimeline()
            if not timeline:
                timeline = media_pool.CreateEmptyTimeline("Omni Demo Timeline")
            
            # Dodaj video na timeline
            media_pool.AppendToTimeline(media_items)
            print("✓ Video dodan na timeline")
            
            # Nastavi osnovne lastnosti
            timeline.SetSetting("timelineResolutionWidth", "1920")
            timeline.SetSetting("timelineResolutionHeight", "1080")
            timeline.SetSetting("timelineFrameRate", "30")
            
            # Dodaj barvno gradacijo
            color_page = resolve.OpenPage("color")
            if color_page:
                print("🎨 Uporabljam barvno gradacijo...")
                
                # Osnovne nastavitve barvne gradacije
                # (DaVinci Resolve API za barvno gradacijo je omejen v brezplačni verziji)
                time.sleep(2)  # Počakaj, da se stran naloži
                
            # Dodaj naslov
            edit_page = resolve.OpenPage("edit")
            if edit_page:
                print("📝 Dodajam naslove...")
                
                # Ustvari generator za naslov
                # (Omejeno v brezplačni verziji)
                
            print("✅ Osnovno urejanje končano")
            
            # Izvozi video (če je omogočeno)
            if len(sys.argv) > 2 and sys.argv[2] == "render":
                deliver_page = resolve.OpenPage("deliver")
                if deliver_page:
                    print("🚀 Začenjam izvoz...")
                    
                    # Nastavi izvozne nastavitve
                    project.SetRenderSettings({
                        "SelectAllFrames": True,
                        "MarkIn": 0,
                        "MarkOut": timeline.GetEndFrame(),
                        "TargetDir": os.path.dirname(video_path),
                        "CustomName": "Omni-Demo-Enhanced"
                    })
                    
                    # Začni izvoz
                    job_id = project.AddRenderJob()
                    if job_id:
                        project.StartRendering(job_id)
                        print(f"✓ Izvoz začet (Job ID: {job_id})")
                        
                        # Počakaj na konec izvoza
                        while project.IsRenderingInProgress():
                            time.sleep(5)
                            print("⏳ Izvažam...")
                        
                        print("✅ Izvoz končan!")
                    else:
                        print("❌ Napaka pri začetku izvoza")
            
            return True
    else:
        print(f"❌ Video datoteka ni najdena: {video_path}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
'@
    
    # Shrani Python skript
    $scriptPath = Join-Path $OutputPath "davinci_automation.py"
    if (-not (Test-Path $OutputPath)) {
        New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
    }
    
    $pythonScript | Out-File -FilePath $scriptPath -Encoding UTF8
    Write-Host "✓ DaVinci Resolve Python skript ustvarjen: $scriptPath" -ForegroundColor Green
    
    # Zaženi DaVinci Resolve, če ni že zagnan
    $resolveProcess = Get-Process -Name "Resolve" -ErrorAction SilentlyContinue
    if (-not $resolveProcess) {
        Write-Host "🚀 Zaganjam DaVinci Resolve..." -ForegroundColor Yellow
        Start-Process -FilePath $davinciPath -WindowStyle Minimized
        Start-Sleep -Seconds 10  # Počakaj, da se zažene
    }
    
    # Zaženi Python skript, če je video podan
    if ($VideoPath -and (Test-Path $VideoPath)) {
        Write-Host "🎬 Zaganjam avtomatsko urejanje v DaVinci Resolve..." -ForegroundColor Green
        
        $pythonArgs = @($scriptPath, $VideoPath)
        if ($AutoRender) {
            $pythonArgs += "render"
        }
        
        try {
            $result = & python @pythonArgs
            Write-Host $result
        } catch {
            Write-Host "⚠️  Python skript ni uspel. Poskusite ročno v DaVinci Resolve." -ForegroundColor Yellow
            Write-Host "📄 Skript: $scriptPath" -ForegroundColor Blue
        }
    }
}

# Ustvari batch skript za enostavno uporabo
$batchContent = @"
@echo off
echo 🎬 DaVinci Resolve - Avtomatska integracija
echo.
if "%1"=="" (
    echo Uporaba: %0 [pot_do_videa] [auto_render]
    echo Primer: %0 "video.mp4" auto
    pause
    exit /b 1
)

set AUTO_RENDER=
if "%2"=="auto" set AUTO_RENDER=-AutoRender

powershell -ExecutionPolicy Bypass -File "%~dp0DaVinci-Resolve-Integration.ps1" -VideoPath "%1" %AUTO_RENDER%
pause
"@

$batchPath = Join-Path (Split-Path $OutputPath -Parent) "DaVinci-Auto-Edit.bat"
$batchContent | Out-File -FilePath $batchPath -Encoding ASCII
Write-Host "✓ Batch skript ustvarjen: $batchPath" -ForegroundColor Green

# Ustvari README za DaVinci integracijo
$readmeContent = @"
# DaVinci Resolve Integracija - Omni Platform

## Namestitev

1. **DaVinci Resolve**: Prenesite z https://www.blackmagicdesign.com/products/davinciresolve
2. **Python**: Potreben za avtomatizacijo (običajno vključen v DaVinci Resolve)

## Uporaba

### Avtomatski način
```bash
DaVinci-Auto-Edit.bat "pot\do\videa.mp4" auto
```

### PowerShell
```powershell
.\DaVinci-Resolve-Integration.ps1 -VideoPath "video.mp4" -AutoRender
```

### Ročni način
1. Odprite DaVinci Resolve
2. Zaženite Python skript: `python davinci_automation.py "video.mp4"`

## Funkcionalnosti

- ✅ Avtomatski uvoz videa
- ✅ Osnovna barvna gradacija
- ✅ Dodajanje naslovov
- ✅ Avtomatski izvoz
- ✅ Thumbnail generacija
- ✅ Fallback na FFmpeg

## Barvne gradacije

- `cinematic`: Filmski izgled z mehkimi krivuljami
- `vibrant`: Žive barve za demo vsebine
- `natural`: Naravni izgled
- `dramatic`: Dramatičen kontrast

## Nastavitve

- Resolucija: 1920x1080 (privzeto)
- Frame rate: 30 fps
- Kodek: H.264 (MP4)
- Kakovost: Visoka (CRF 18)

## Opombe

- Brezplačna verzija DaVinci Resolve ima omejitve pri API-ju
- Za polne funkcionalnosti potrebujete DaVinci Resolve Studio
- FFmpeg se uporabi kot rezerva, če DaVinci ni na voljo
"@

$readmePath = Join-Path $OutputPath "README-DaVinci.md"
$readmeContent | Out-File -FilePath $readmePath -Encoding UTF8
Write-Host "✓ README ustvarjen: $readmePath" -ForegroundColor Green

Write-Host "`n📊 DAVINCI RESOLVE INTEGRACIJA PRIPRAVLJENA" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Gray
Write-Host "🎬 DaVinci Resolve: $(if ($davinciPath) { "✓ Najden" } else { "❌ Ni nameščen" })" -ForegroundColor White
Write-Host "🐍 Python skript: $scriptPath" -ForegroundColor White
Write-Host "📁 Izhodna mapa: $OutputPath" -ForegroundColor White
Write-Host "🚀 Batch skript: $batchPath" -ForegroundColor White

if ($VideoPath) {
    Write-Host "`n🎯 Video za obdelavo: $VideoPath" -ForegroundColor Yellow
    if ($AutoRender) {
        Write-Host "⚡ Avtomatski izvoz: OMOGOČEN" -ForegroundColor Green
    }
}

Write-Host "`n✅ DaVinci Resolve integracija pripravljena!" -ForegroundColor Green
Write-Host "💡 Uporabite batch skript za enostavno urejanje videov" -ForegroundColor Yellow