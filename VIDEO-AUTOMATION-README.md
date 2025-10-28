# 🎬 Omni Platform - Kompletna Video Avtomatizacija

## 🚀 1-KLIK REŠITEV ZA PROFESIONALEN VIDEO

Sistem za samodejno ustvarjanje profesionalnih demo videjev z OBS Studio in FFmpeg.

---

## 📋 Pregled Sistema

### ✨ Funkcionalnosti
- **Avtomatsko snemanje** z OBS Studio (95 sekund)
- **Postprodukcija** z intro/outro in audio izboljšavami
- **Izvoz za platforme** (YouTube, LinkedIn, Twitter)
- **1-klik avtomatizacija** celotnega procesa
- **Profesionalne nastavitve** (1080p/30fps, NVENC/AMF)

### 🎯 Rezultat
- Profesionalen demo video pripravljen za objavo
- Optimizirane verzije za različne platforme
- Avtomatski intro/outro in prehodi
- Izboljšan zvok z filtri

---

## 🛠️ Zahteve

### Programska oprema
- **OBS Studio** (https://obsproject.com/)
- **FFmpeg** (https://ffmpeg.org/)
- **PowerShell 5.0+**

### Strežniki (morajo biti aktivni)
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8004`
- Assets: `http://localhost:8009`

---

## 🎬 Uporaba

### 🚀 Metoda 1: Kompletna Avtomatizacija (PRIPOROČENO)
```powershell
.\Create-Complete-Video.ps1
```
**Ali uporabi namizno bližnjico:** `Omni Video Automation`

### 📹 Metoda 2: Po korakih
```powershell
# 1. Snemanje
.\Auto-Record-Demo.ps1

# 2. Postprodukcija
.\Post-Process-Video.ps1

# 3. Izvoz za platforme
.\Create-Final-Video.ps1
```

### ⚙️ Metoda 3: Ročno z OBS
```powershell
# Zaženi demo
.\Launch-Omni-Demo.ps1

# Uvozi OBS nastavitve (enkrat)
# Scene Collection: omni_scene_collection.json
# Profile: omni_demo_profile.json

# Hotkeys:
# F1-F5: Scena switching
# Space: Start recording
# Esc: Stop recording
```

---

## 📁 Struktura Datotek

```
📁 videos/
├── 📹 Omni-Demo-YYYY-MM-DD-HH-mm.mp4    # Surovi posnetki
├── 📁 final/
│   └── 🎬 Omni-Demo-YYYY-MM-DD-HH-mm-FINAL.mp4  # Postprodukcija
└── 📁 export/
    ├── 🚀 Omni-Demo-YYYY-MM-DD-HH-mm-YouTube.mp4
    ├── 💼 Omni-Demo-YYYY-MM-DD-HH-mm-LinkedIn.mp4
    └── 🐦 Omni-Demo-YYYY-MM-DD-HH-mm-Twitter.mp4
```

---

## 🎛️ Skripti in Funkcionalnosti

### 🎬 Create-Complete-Video.ps1
**Glavna 1-klik rešitev**
- Preveri predpogoje
- Avtomatsko snemanje (95s)
- Postprodukcija z intro/outro
- Izvoz za platforme
- Ustvari poročilo

**Parametri:**
```powershell
-ProjectName "Moj-Demo"          # Ime projekta
-DemoLength 95                   # Trajanje v sekundah
-SkipRecording                   # Preskoči snemanje
-SkipPostProduction             # Preskoči postprodukcijo
-SkipExport                     # Preskoči izvoz
-YouTube                        # Izvozi za YouTube
-LinkedIn                       # Izvozi za LinkedIn
-Twitter                        # Izvozi za Twitter
```

### 📹 Auto-Record-Demo.ps1
**Avtomatsko snemanje z OBS**
- Preveri strežnike in OBS
- Zažene demo stran
- Avtomatsko preklaplja scene (F1-F5)
- Snema 95 sekund
- Shrani v `.\videos\`

### 🎨 Post-Process-Video.ps1
**Postprodukcija**
- Ustvari intro/outro (če ne obstajata)
- Združi videoe z prehodi
- Izboljša zvok (volume, noise reduction)
- Shrani v `.\videos\final\`

### 🚀 Create-Final-Video.ps1
**Izvoz za platforme**
- YouTube: 1080p, 8Mbps
- LinkedIn: 720p, 5Mbps
- Twitter: 720p, 6Mbps (max 2:20)
- Instagram: 1080x1080 (kvadrat)
- TikTok: 1080x1920 (vertikalno)
- Dodaj watermark logo
- Shrani v `.\videos\export\`

---

## 🎯 OBS Nastavitve

### 📋 Scene Collection (omni_scene_collection.json)
- **Intro** (15s): Title card
- **Demo** (45s): Frontend UI + Lower third
- **Health** (10s): Backend health
- **Brief** (15s): Investor brief PDF
- **Outro** (10s): Outro card

### ⌨️ Hotkeys
- **F1-F5**: Preklapljanje scen
- **Space**: Start recording
- **Escape**: Stop recording

### 🎞️ Video Nastavitve
- **Resolucija**: 1920x1080
- **FPS**: 30
- **Encoder**: NVENC/AMF (GPU) ali x264 (CPU)
- **Format**: MP4
- **Bitrate**: 8000 kbps

### 🎵 Audio Nastavitve
- **Noise Suppression**: -30dB
- **Noise Gate**: -32dB threshold
- **Compressor**: 3:1 ratio
- **Sample Rate**: 48kHz

---

## 🔧 Namestitev

### 1. Kloniraj repozitorij
```bash
git clone <repo-url>
cd omni-platform
```

### 2. Namesti odvisnosti
```powershell
# OBS Studio
winget install OBSProject.OBSStudio

# FFmpeg
winget install FFmpeg

# Ali ročno iz https://obsproject.com/ in https://ffmpeg.org/
```

### 3. Zaženi strežnike
```powershell
.\Launch-Omni-Demo.ps1
```

### 4. Uvozi OBS nastavitve (enkrat)
1. Odpri OBS Studio
2. **Scene Collection** → **Import** → `omni_scene_collection.json` ✅
3. **Profile** → **Import** → `omni_demo_profile.json`

### 5. Ustvari namizno bližnjico
```powershell
.\Create-Video-Shortcut.ps1
```

---

## 🎬 Workflow

### Avtomatski (1-klik)
1. **Klikni** namizno bližnjico `Omni Video Automation`
2. **Počakaj** 95 sekund
3. **Preveri** rezultate v `.\videos\export\`
4. **Objavi** na platforme

### Ročni
1. **Zaženi** strežnike: `.\Launch-Omni-Demo.ps1`
2. **Odpri** OBS Studio
3. **Zaženi** snemanje: **Space**
4. **Preklapljaj** scene: **F1-F5**
5. **Ustavi** snemanje: **Escape**
6. **Postprodukcija**: `.\Post-Process-Video.ps1`
7. **Izvoz**: `.\Create-Final-Video.ps1`

---

## 📊 Platforme in Specifikacije

| Platforma | Resolucija | Bitrate | Max Trajanje | Format |
|-----------|------------|---------|--------------|--------|
| YouTube   | 1920x1080  | 8 Mbps  | Neomejeno    | MP4    |
| LinkedIn  | 1280x720   | 5 Mbps  | 10 min       | MP4    |
| Twitter   | 1280x720   | 6 Mbps  | 2:20         | MP4    |
| Instagram | 1080x1080  | 3.5 Mbps| 60s          | MP4    |
| TikTok    | 1080x1920  | 4 Mbps  | 10 min       | MP4    |

---

## 🐛 Odpravljanje Napak

### ❌ OBS se ne zažene
```powershell
# Preveri namestitev
Get-Process "obs64" -ErrorAction SilentlyContinue

# Ročni zagon
Start-Process "obs64"
```

### ❌ FFmpeg ni najden
```powershell
# Preveri namestitev
ffmpeg -version

# Namesti
winget install FFmpeg
```

### ❌ Strežniki niso aktivni
```powershell
# Zaženi vse strežnike
.\Launch-Omni-Demo.ps1

# Preveri porte
netstat -an | findstr "3000 8004 8009"
```

### ❌ Video ni ustvarjen
1. Preveri OBS nastavitve
2. Preveri disk prostor
3. Preveri dovoljenja za pisanje
4. Poglej log datoteke

### ❌ Slaba kakovost videa
1. Povečaj bitrate v OBS
2. Preveri GPU encoder (NVENC/AMF)
3. Zmanjšaj CPU obremenitev
4. Zapri druge aplikacije

---

## 📈 Optimizacija

### 🚀 Hitrost
- Uporabi GPU encoder (NVENC/AMF)
- SSD disk za shranjevanje
- Zapri nepotrebne aplikacije
- 16GB+ RAM priporočeno

### 🎨 Kakovost
- 1080p/30fps za splet
- 4K/60fps za premium
- Visok bitrate za YouTube
- Nizek bitrate za Twitter

### 📱 Platforme
- **YouTube**: Najvišja kakovost
- **LinkedIn**: Poslovna vsebina
- **Twitter**: Kratki posnetki
- **Instagram**: Kvadratni format
- **TikTok**: Vertikalni format

---

## 📞 Podpora

### 🔗 Koristne povezave
- [OBS Studio Dokumentacija](https://obsproject.com/wiki/)
- [FFmpeg Dokumentacija](https://ffmpeg.org/documentation.html)
- [PowerShell Dokumentacija](https://docs.microsoft.com/powershell/)

### 🆘 Pomoč
1. Preveri log datoteke
2. Zaženi diagnostiko
3. Pošlji poročilo o napaki

---

## 🎉 Uspešna Uporaba!

**Čestitke!** Sedaj imaš popolnoma avtomatiziran sistem za ustvarjanje profesionalnih demo videjev.

### 🚀 Naslednji koraki:
1. **Objavi** videoe na platforme
2. **Analiziraj** statistike
3. **Optimiziraj** vsebino
4. **Avtomatiziraj** objavljanje

---

*Ustvarjeno z ❤️ za Omni Platform*