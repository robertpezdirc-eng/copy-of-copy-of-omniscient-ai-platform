# OBS Setup Navodila - Omni Platform Demo

## 🎬 Avtomatiziran Setup za OBS Recording

### 1️⃣ Uvoz Scene Collection z Hotkeys

**Datoteka:** `omni_scene_collection.json`

1. **Odpri OBS Studio**
2. **Scene Collection → Import**
3. **Izberi datoteko:** `omni_scene_collection.json`
4. **POMEMBNO:** Na Import zaslonu klikni **majhen checkbox levo** ob vrstici (pogosto je privzeto odkljukan)
5. **Klikni Import**
6. **Po uvozu:** Scene Collections → izberi **"Omni Demo"**

### 2️⃣ Uvoz Profile z Optimalnimi Nastavitvami

**Datoteka:** `omni_demo_profile.json`

1. **Profile → Import**
2. **Izberi datoteko:** `omni_demo_profile.json`
3. **Klikni Import**
4. **Po uvozu:** Profile → izberi **"Omni Demo Profile"**

---

## ⌨️ Hotkeys za Preklapljanje Scen

| Tipka | Scena | Vsebina |
|-------|-------|---------|
| **F1** | Intro | Title Card |
| **F2** | Demo | Frontend UI + Lower Third |
| **F3** | Health | Backend Health Check |
| **F4** | Brief | Investor Brief PDF |
| **F5** | Outro | Outro Card |

### 🎥 Recording Hotkeys

| Tipka | Akcija |
|-------|--------|
| **SPACE** | Start Recording |
| **ESC** | Stop Recording |
| **F9** | Start Streaming |
| **F10** | Stop Streaming |

---

## 🎨 Prehodi med Scenami

- **Privzeto:** Fade (500ms)
- **Alternativa:** Cut (0ms)
- **Nastavi v:** Settings → Video → Transition

---

## 📹 Optimalne Nastavitve (Avtomatsko)

### Video
- **Resolucija:** 1920x1080 (Full HD)
- **FPS:** 30
- **Format:** MP4
- **Encoder:** NVENC H.264 (NVIDIA) ali AMF H.264 (AMD)

### Recording
- **Bitrate:** 8000 kbps
- **Keyframe:** 2s
- **Preset:** High Quality
- **Profile:** High
- **B-frames:** 2

### Audio
- **Sample Rate:** 48 kHz
- **Channels:** Stereo
- **Noise Suppression:** Vključeno
- **Noise Gate:** Vključeno
- **Compressor:** Vključeno

---

## 🚀 Quick Start Recording

### Metoda 1: Avtomatski Autoplay
```bash
# Zaženi .bat datoteko
Start-Autoplay-OBS.bat
```
- Odpre autoplay demo v celozaslonskem brskalniku
- Avtomatsko zažene OBS recording
- Trajanje: ~95 sekund

### Metoda 2: Ročno z Hotkeys
1. **F1** → Intro (5s)
2. **F2** → Demo (30s)
3. **F3** → Health (10s)
4. **F4** → Brief (30s)
5. **F5** → Outro (10s)

---

## 🔧 Troubleshooting

### Če Browser Sources ne delujejo:
1. Preveri, da tečejo strežniki:
   - Frontend: `http://localhost:5175/`
   - Assets: `http://localhost:8009/`
   - Backend: `http://localhost:8004/`

### Če Hotkeys ne delujejo:
1. Settings → Hotkeys
2. Preveri, da so tipke pravilno nastavljene
3. Ponovno uvozi scene collection

### Če Recording ne deluje:
1. Settings → Output
2. Preveri Recording Path
3. Preveri Encoder (NVENC/AMF)

---

## 📁 Datoteke za Uvoz

```
omni-platform/docs/obs/
├── omni_scene_collection.json    # Scene z hotkeys
├── omni_demo_profile.json        # Optimalne nastavitve
├── OBS_SETUP_NAVODILA.md        # Ta datoteka
└── overlays/
    ├── title.html               # Title card
    ├── lower-third.html         # Overlay
    ├── outro.html              # Outro card
    └── demo_autoplay.html      # Avtomatski demo
```

---

## 🎯 URL-ji za Browser Sources

| Vir | URL |
|-----|-----|
| **Title** | `http://localhost:8009/omni-platform/docs/overlays/title.html` |
| **Lower Third** | `http://localhost:8009/omni-platform/docs/overlays/lower-third.html` |
| **Outro** | `http://localhost:8009/omni-platform/docs/overlays/outro.html` |
| **Autoplay Demo** | `http://localhost:8009/omni-platform/docs/overlays/demo_autoplay.html` |
| **Frontend UI** | `http://localhost:5175/` |
| **Backend Health** | `http://localhost:8004/api/health` |
| **Investor Brief** | `http://localhost:8009/omni-platform/docs/investor_brief.pdf` |

---

**✅ Po uvozu boš imel popolnoma avtomatiziran OBS setup z enim klikom!**