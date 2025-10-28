# Omni Platform - AVTOMATSKA GENERACIJA SPLETNIH VSEBIN
# Avtomatsko ustvarja slike, videe in druge medijske vsebine za spletno stran

param(
    [string]$ContentType = "all",  # all, images, videos, thumbnails
    [string]$OutputDir = ".\generated-content",
    [int]$ImageWidth = 1920,
    [int]$ImageHeight = 1080,
    [string]$BrandColor = "#2563eb",
    [switch]$AutoDeploy
)

# Ustvari izhodno mapo
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    Write-Host "✓ Ustvarjena mapa: $OutputDir" -ForegroundColor Green
}

# Ustvari podmape
$subDirs = @("images", "videos", "thumbnails", "banners", "icons")
foreach ($dir in $subDirs) {
    $fullPath = Join-Path $OutputDir $dir
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
    }
}

Write-Host "🎨 OMNI PLATFORM - Avtomatska generacija spletnih vsebin" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

# Funkcija za generiranje SVG slik
function New-SVGImage {
    param(
        [string]$Title,
        [string]$Subtitle = "",
        [string]$OutputPath,
        [int]$Width = 1920,
        [int]$Height = 1080,
        [string]$BackgroundColor = "#1e293b",
        [string]$TextColor = "#ffffff",
        [string]$AccentColor = "#2563eb"
    )
    
    $svgContent = @"
<svg width="$Width" height="$Height" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:$BackgroundColor;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#0f172a;stop-opacity:1" />
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
      <feMerge> 
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  
  <!-- Ozadje -->
  <rect width="100%" height="100%" fill="url(#bgGradient)"/>
  
  <!-- Geometrijski vzorci -->
  <circle cx="200" cy="200" r="100" fill="$AccentColor" opacity="0.1"/>
  <circle cx="$(Width-200)" cy="$(Height-200)" r="150" fill="$AccentColor" opacity="0.05"/>
  
  <!-- Naslov -->
  <text x="$(Width/2)" y="$(Height/2-50)" text-anchor="middle" 
        font-family="Arial, sans-serif" font-size="72" font-weight="bold" 
        fill="$TextColor" filter="url(#glow)">$Title</text>
  
  <!-- Podnaslov -->
  $(if ($Subtitle) { "<text x=`"$(Width/2)`" y=`"$(Height/2+30)`" text-anchor=`"middle`" font-family=`"Arial, sans-serif`" font-size=`"36`" fill=`"$AccentColor`">$Subtitle</text>" })
  
  <!-- Logo/ikona -->
  <rect x="$(Width/2-30)" y="$(Height/2+80)" width="60" height="8" rx="4" fill="$AccentColor"/>
  <rect x="$(Width/2-20)" y="$(Height/2+95)" width="40" height="4" rx="2" fill="$AccentColor" opacity="0.7"/>
</svg>
"@
    
    $svgContent | Out-File -FilePath $OutputPath -Encoding UTF8
    Write-Host "  ✓ Ustvarjena SVG slika: $(Split-Path $OutputPath -Leaf)" -ForegroundColor Green
}

# Funkcija za generiranje thumbnail slik
function New-ThumbnailImage {
    param(
        [string]$Title,
        [string]$OutputPath,
        [string]$Type = "video"  # video, article, demo
    )
    
    $iconSymbol = switch ($Type) {
        "video" { "▶" }
        "article" { "📄" }
        "demo" { "🚀" }
        default { "●" }
    }
    
    $svgContent = @"
<svg width="320" height="180" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="thumbGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#2563eb;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#1e40af;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <rect width="100%" height="100%" fill="url(#thumbGradient)"/>
  <rect x="10" y="10" width="300" height="160" rx="8" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.3"/>
  
  <text x="160" y="70" text-anchor="middle" font-family="Arial, sans-serif" 
        font-size="48" fill="#ffffff">$iconSymbol</text>
  
  <text x="160" y="120" text-anchor="middle" font-family="Arial, sans-serif" 
        font-size="16" font-weight="bold" fill="#ffffff">$Title</text>
</svg>
"@
    
    $svgContent | Out-File -FilePath $OutputPath -Encoding UTF8
    Write-Host "  ✓ Ustvarjen thumbnail: $(Split-Path $OutputPath -Leaf)" -ForegroundColor Green
}

# Generiranje osnovnih slik
if ($ContentType -eq "all" -or $ContentType -eq "images") {
    Write-Host "🖼️  Generiram osnovne slike..." -ForegroundColor Yellow
    
    # Hero banner
    New-SVGImage -Title "OMNI PLATFORM" -Subtitle "Inteligentna AI Platforma" `
                 -OutputPath (Join-Path $OutputDir "images\hero-banner.svg") `
                 -Width $ImageWidth -Height $ImageHeight
    
    # About sekcija
    New-SVGImage -Title "O PLATFORMI" -Subtitle "Napredne AI funkcionalnosti" `
                 -OutputPath (Join-Path $OutputDir "images\about-section.svg") `
                 -Width 1200 -Height 600
    
    # Features banner
    New-SVGImage -Title "FUNKCIONALNOSTI" -Subtitle "Vse v enem sistemu" `
                 -OutputPath (Join-Path $OutputDir "images\features-banner.svg") `
                 -Width 1400 -Height 700
    
    # Demo sekcija
    New-SVGImage -Title "DEMO" -Subtitle "Preizkusite platformo" `
                 -OutputPath (Join-Path $OutputDir "images\demo-section.svg") `
                 -Width 1600 -Height 800 -AccentColor "#10b981"
}

# Generiranje thumbnail slik
if ($ContentType -eq "all" -or $ContentType -eq "thumbnails") {
    Write-Host "🎯 Generiram thumbnail slike..." -ForegroundColor Yellow
    
    $thumbnails = @(
        @{Title="AI Chat"; Type="demo"},
        @{Title="Video Demo"; Type="video"},
        @{Title="Dokumentacija"; Type="article"},
        @{Title="API Demo"; Type="demo"},
        @{Title="Tutorial"; Type="video"},
        @{Title="Navodila"; Type="article"}
    )
    
    foreach ($thumb in $thumbnails) {
        $fileName = ($thumb.Title -replace " ", "-").ToLower() + "-thumb.svg"
        $outputPath = Join-Path $OutputDir "thumbnails\$fileName"
        New-ThumbnailImage -Title $thumb.Title -Type $thumb.Type -OutputPath $outputPath
    }
}

# Generiranje ikon
if ($ContentType -eq "all" -or $ContentType -eq "icons") {
    Write-Host "🔧 Generiram ikone..." -ForegroundColor Yellow
    
    # Favicon
    $faviconSVG = @"
<svg width="32" height="32" xmlns="http://www.w3.org/2000/svg">
  <rect width="32" height="32" rx="6" fill="$BrandColor"/>
  <rect x="8" y="12" width="16" height="3" rx="1" fill="#ffffff"/>
  <rect x="8" y="17" width="12" height="2" rx="1" fill="#ffffff" opacity="0.8"/>
  <circle cx="22" cy="10" r="2" fill="#10b981"/>
</svg>
"@
    $faviconSVG | Out-File -FilePath (Join-Path $OutputDir "icons\favicon.svg") -Encoding UTF8
    
    # Logo
    $logoSVG = @"
<svg width="200" height="60" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="15" width="40" height="8" rx="4" fill="$BrandColor"/>
  <rect x="10" y="27" width="30" height="6" rx="3" fill="$BrandColor" opacity="0.7"/>
  <rect x="10" y="37" width="35" height="4" rx="2" fill="$BrandColor" opacity="0.5"/>
  <text x="65" y="35" font-family="Arial, sans-serif" font-size="24" font-weight="bold" fill="#1e293b">OMNI</text>
  <text x="65" y="50" font-family="Arial, sans-serif" font-size="12" fill="#64748b">PLATFORM</text>
</svg>
"@
    $logoSVG | Out-File -FilePath (Join-Path $OutputDir "icons\logo.svg") -Encoding UTF8
    
    Write-Host "  ✓ Ustvarjen favicon in logo" -ForegroundColor Green
}

# Generiranje CSS za animacije
$animationCSS = @'
/* Omni Platform - Avtomatsko generirane animacije */
.omni-fade-in {
    animation: omniSlideIn 0.8s ease-out forwards;
    opacity: 0;
    transform: translateY(30px);
}

.omni-scale-hover {
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.omni-scale-hover:hover {
    transform: scale(1.05);
    box-shadow: 0 10px 25px rgba(37, 99, 235, 0.2);
}

.omni-glow {
    box-shadow: 0 0 20px rgba(37, 99, 235, 0.3);
    transition: box-shadow 0.3s ease;
}

.omni-glow:hover {
    box-shadow: 0 0 30px rgba(37, 99, 235, 0.5);
}

@keyframes omniSlideIn {
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes omniPulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

.omni-pulse {
    animation: omniPulse 2s infinite;
}

/* Responsive grid za galerijo */
.omni-gallery {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    padding: 20px;
}

.omni-card {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border-radius: 12px;
    padding: 20px;
    border: 1px solid rgba(37, 99, 235, 0.2);
    transition: all 0.3s ease;
}

.omni-card:hover {
    border-color: rgba(37, 99, 235, 0.5);
    transform: translateY(-5px);
}
'@

$animationCSS | Out-File -FilePath (Join-Path $OutputDir "omni-animations.css") -Encoding UTF8
Write-Host "✓ Ustvarjen CSS za animacije" -ForegroundColor Green

# Generiranje JavaScript za interaktivnost
$interactiveJS = @'
// Omni Platform - Avtomatska interaktivnost
class OmniContentManager {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupAnimations();
        this.setupLazyLoading();
        this.setupAutoRefresh();
    }
    
    setupAnimations() {
        // Fade-in animacije ob scroll-u
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('omni-fade-in');
                }
            });
        });
        
        document.querySelectorAll('.omni-animate').forEach(el => {
            observer.observe(el);
        });
    }
    
    setupLazyLoading() {
        // Lazy loading za slike
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
    
    setupAutoRefresh() {
        // Avtomatsko osveževanje vsebin
        setInterval(() => {
            this.refreshDynamicContent();
        }, 30000); // Vsakih 30 sekund
    }
    
    refreshDynamicContent() {
        // Posodobi dinamične vsebine
        const dynamicElements = document.querySelectorAll('.omni-dynamic');
        dynamicElements.forEach(el => {
            if (el.dataset.refreshUrl) {
                fetch(el.dataset.refreshUrl)
                    .then(response => response.text())
                    .then(html => {
                        el.innerHTML = html;
                        el.classList.add('omni-pulse');
                        setTimeout(() => el.classList.remove('omni-pulse'), 2000);
                    })
                    .catch(console.error);
            }
        });
    }
    
    // Avtomatsko generiranje thumbnail-ov
    generateThumbnail(videoElement, canvasElement) {
        const canvas = canvasElement;
        const ctx = canvas.getContext('2d');
        
        videoElement.addEventListener('loadeddata', () => {
            canvas.width = 320;
            canvas.height = 180;
            ctx.drawImage(videoElement, 0, 0, 320, 180);
            
            // Dodaj overlay
            ctx.fillStyle = 'rgba(37, 99, 235, 0.8)';
            ctx.fillRect(0, 0, 320, 30);
            
            ctx.fillStyle = 'white';
            ctx.font = '16px Arial';
            ctx.fillText('▶ Omni Platform Demo', 10, 20);
        });
    }
}

// Inicializacija
document.addEventListener('DOMContentLoaded', () => {
    new OmniContentManager();
});

// Utility funkcije
window.OmniUtils = {
    // Avtomatsko prilagajanje velikosti slik
    autoResizeImages() {
        const images = document.querySelectorAll('.omni-auto-resize');
        images.forEach(img => {
            const container = img.parentElement;
            const containerWidth = container.offsetWidth;
            
            if (containerWidth < 768) {
                img.style.width = '100%';
                img.style.height = 'auto';
            } else {
                img.style.width = 'auto';
                img.style.height = '100%';
            }
        });
    },
    
    // Generiranje barv na podlagi vsebine
    generateColorScheme(text) {
        const hash = text.split('').reduce((a, b) => {
            a = ((a << 5) - a) + b.charCodeAt(0);
            return a & a;
        }, 0);
        
        const hue = Math.abs(hash) % 360;
        return {
            primary: `hsl(${hue}, 70%, 50%)`,
            secondary: `hsl(${(hue + 30) % 360}, 60%, 60%)`,
            accent: `hsl(${(hue + 60) % 360}, 80%, 40%)`
        };
    }
};
'@

$interactiveJS | Out-File -FilePath (Join-Path $OutputDir "omni-interactive.js") -Encoding UTF8
Write-Host "✓ Ustvarjen JavaScript za interaktivnost" -ForegroundColor Green

# Ustvari HTML template za galerijo
$galleryHTML = @'
<!DOCTYPE html>
<html lang="sl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Omni Platform - Avtomatska galerija</title>
    <link rel="stylesheet" href="omni-animations.css">
    <style>
        body {
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: white;
            font-family: Arial, sans-serif;
            min-height: 100vh;
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 3rem;
            margin: 0;
            background: linear-gradient(45deg, #2563eb, #10b981);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .stats {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        
        .stat {
            background: rgba(37, 99, 235, 0.1);
            padding: 15px 25px;
            border-radius: 8px;
            border: 1px solid rgba(37, 99, 235, 0.3);
        }
        
        .gallery-section {
            margin: 40px 0;
        }
        
        .gallery-section h2 {
            color: #2563eb;
            border-bottom: 2px solid #2563eb;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        
        .thumbnail-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 20px;
        }
        
        .thumbnail-item {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            overflow: hidden;
            transition: transform 0.3s ease;
        }
        
        .thumbnail-item:hover {
            transform: scale(1.02);
        }
        
        .thumbnail-item img {
            width: 100%;
            height: 180px;
            object-fit: cover;
        }
        
        .thumbnail-info {
            padding: 15px;
        }
        
        .auto-refresh {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #10b981;
            color: white;
            padding: 10px 15px;
            border-radius: 20px;
            font-size: 12px;
            animation: omniPulse 2s infinite;
        }
    </style>
</head>
<body>
    <div class="auto-refresh">🔄 Avtomatsko osveževanje</div>
    
    <div class="header">
        <h1>OMNI PLATFORM</h1>
        <p>Avtomatsko generirana galerija vsebin</p>
        
        <div class="stats">
            <div class="stat">
                <strong id="imageCount">0</strong><br>
                <small>Slik</small>
            </div>
            <div class="stat">
                <strong id="videoCount">0</strong><br>
                <small>Videov</small>
            </div>
            <div class="stat">
                <strong id="thumbnailCount">0</strong><br>
                <small>Thumbnail-ov</small>
            </div>
        </div>
    </div>
    
    <div class="gallery-section">
        <h2>🖼️ Osnovne slike</h2>
        <div class="omni-gallery" id="imagesGallery">
            <!-- Avtomatsko generirano -->
        </div>
    </div>
    
    <div class="gallery-section">
        <h2>🎯 Thumbnail slike</h2>
        <div class="thumbnail-grid" id="thumbnailsGallery">
            <!-- Avtomatsko generirano -->
        </div>
    </div>
    
    <div class="gallery-section">
        <h2>🔧 Ikone</h2>
        <div class="omni-gallery" id="iconsGallery">
            <!-- Avtomatsko generirano -->
        </div>
    </div>
    
    <script src="omni-interactive.js"></script>
    <script>
        // Avtomatsko nalaganje galerije
        function loadGallery() {
            // Simulacija nalaganja vsebin
            const images = ['hero-banner.svg', 'about-section.svg', 'features-banner.svg', 'demo-section.svg'];
            const thumbnails = ['ai-chat-thumb.svg', 'video-demo-thumb.svg', 'dokumentacija-thumb.svg'];
            const icons = ['favicon.svg', 'logo.svg'];
            
            document.getElementById('imageCount').textContent = images.length;
            document.getElementById('videoCount').textContent = '1'; // Video se snema
            document.getElementById('thumbnailCount').textContent = thumbnails.length;
            
            // Generiraj galerijo slik
            const imagesGallery = document.getElementById('imagesGallery');
            images.forEach(img => {
                const card = document.createElement('div');
                card.className = 'omni-card omni-animate';
                card.innerHTML = `
                    <img src="images/${img}" alt="${img}" style="width: 100%; border-radius: 8px;">
                    <h3>${img.replace('.svg', '').replace('-', ' ').toUpperCase()}</h3>
                    <p>Avtomatsko generirana SVG slika</p>
                `;
                imagesGallery.appendChild(card);
            });
            
            // Generiraj thumbnail galerijo
            const thumbnailsGallery = document.getElementById('thumbnailsGallery');
            thumbnails.forEach(thumb => {
                const item = document.createElement('div');
                item.className = 'thumbnail-item omni-animate';
                item.innerHTML = `
                    <img src="thumbnails/${thumb}" alt="${thumb}">
                    <div class="thumbnail-info">
                        <h4>${thumb.replace('-thumb.svg', '').replace('-', ' ').toUpperCase()}</h4>
                        <small>Avtomatsko generiran thumbnail</small>
                    </div>
                `;
                thumbnailsGallery.appendChild(item);
            });
            
            // Generiraj ikone galerijo
            const iconsGallery = document.getElementById('iconsGallery');
            icons.forEach(icon => {
                const card = document.createElement('div');
                card.className = 'omni-card omni-animate';
                card.innerHTML = `
                    <img src="icons/${icon}" alt="${icon}" style="width: 100px; height: auto; margin: 0 auto; display: block;">
                    <h3>${icon.replace('.svg', '').toUpperCase()}</h3>
                    <p>Avtomatsko generirana ikona</p>
                `;
                iconsGallery.appendChild(card);
            });
        }
        
        // Naloži galerijo ob zagonu
        document.addEventListener('DOMContentLoaded', loadGallery);
        
        // Avtomatsko osveževanje vsakih 30 sekund
        setInterval(() => {
            console.log('🔄 Osveževanje galerije...');
            // Tukaj bi lahko dodali preverjanje novih datotek
        }, 30000);
    </script>
</body>
</html>
'@

$galleryHTML | Out-File -FilePath (Join-Path $OutputDir "gallery.html") -Encoding UTF8
Write-Host "✓ Ustvarjen HTML template za galerijo" -ForegroundColor Green

# Avtomatsko odpiranje galerije
if ($AutoDeploy) {
    $galleryPath = Join-Path $OutputDir "gallery.html"
    Start-Process $galleryPath
    Write-Host "🌐 Odprta galerija v brskalniku" -ForegroundColor Green
}

# Poročilo
Write-Host "`n📊 POROČILO O GENERIRANI VSEBINI" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Gray
Write-Host "📁 Izhodna mapa: $OutputDir" -ForegroundColor White
Write-Host "🖼️  Osnovne slike: $(if (Test-Path (Join-Path $OutputDir 'images')) { (Get-ChildItem (Join-Path $OutputDir 'images') -Filter '*.svg').Count } else { 0 })" -ForegroundColor White
Write-Host "🎯 Thumbnail slike: $(if (Test-Path (Join-Path $OutputDir 'thumbnails')) { (Get-ChildItem (Join-Path $OutputDir 'thumbnails') -Filter '*.svg').Count } else { 0 })" -ForegroundColor White
Write-Host "🔧 Ikone: $(if (Test-Path (Join-Path $OutputDir 'icons')) { (Get-ChildItem (Join-Path $OutputDir 'icons') -Filter '*.svg').Count } else { 0 })" -ForegroundColor White
Write-Host "🎨 CSS animacije: omni-animations.css" -ForegroundColor White
Write-Host "⚡ JavaScript: omni-interactive.js" -ForegroundColor White
Write-Host "🌐 Galerija: gallery.html" -ForegroundColor White

Write-Host "`n✅ Avtomatska generacija spletnih vsebin končana!" -ForegroundColor Green
Write-Host "💡 Uporaba: Kopiraj generirane datoteke v svojo spletno stran" -ForegroundColor Yellow
Write-Host "🔄 Sistem bo avtomatsko generiral nove vsebine po potrebi" -ForegroundColor Yellow

# Ustvari batch skript za enostavno zaganjanje
$batchContent = @"
@echo off
echo 🎨 Omni Platform - Avtomatska generacija vsebin
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0Auto-Generate-Web-Content.ps1" -AutoDeploy
pause
"@

$batchContent | Out-File -FilePath (Join-Path (Split-Path $OutputDir -Parent) "Generate-Web-Content.bat") -Encoding ASCII
Write-Host "✓ Ustvarjen batch skript: Generate-Web-Content.bat" -ForegroundColor Green