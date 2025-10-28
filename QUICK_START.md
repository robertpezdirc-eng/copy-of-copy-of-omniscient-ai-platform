# 🎬 Omni Platform Demo - Quick Start

## 🚀 3 Načini Zagona

### 1️⃣ Avtomatski Zagon (.bat)
```bash
.\Start-Autoplay-OBS.bat
```
- **1-klik** → celoten demo (~95s)
- Odpre celozaslonski brskalnik + OBS snemanje

### 2️⃣ PowerShell Launcher (Priporočeno)
```powershell
.\Launch-Omni-Demo.ps1
```
- **Preveri strežnike** pred zagonom
- **Boljše error handling**
- **Koristni URL-ji** in nasveti

### 3️⃣ Bližnjica na Namizju
```powershell
.\Create-Desktop-Shortcut.ps1  # Ustvari bližnjico
```
- **Dvoklik** na namizju → "🎬 Omni Platform Demo"
- **Najlažji** dostop

---

## 📋 OBS Setup (Enkrat)

### Uvoz Scene Collection
1. **OBS → Scene Collection → Import**
2. **Izberi:** `omni-platform/docs/obs/omni_scene_collection.json`
3. **Klikni checkbox** levo ob vrstici
4. **Import** → izberi "Omni Demo"

### Uvoz Profile
1. **OBS → Profile → Import**
2. **Izberi:** `omni-platform/docs/obs/omni_demo_profile.json`
3. **Import** → izberi "Omni Demo Profile"

---

## ⌨️ Hotkeys (Avtomatsko)

| Tipka | Akcija |
|-------|--------|
| **F1** | Intro Scene |
| **F2** | Demo Scene (UI + Overlay) |
| **F3** | Health Scene |
| **F4** | Brief Scene (PDF) |
| **F5** | Outro Scene |
| **SPACE** | ▶️ Start Recording |
| **ESC** | ⏹️ Stop Recording |

---

## 🎯 URL-ji za Browser Sources

```
Title:      http://localhost:8009/omni-platform/docs/overlays/title.html
Lower 3rd:  http://localhost:8009/omni-platform/docs/overlays/lower-third.html
Outro:      http://localhost:8009/omni-platform/docs/overlays/outro.html
Autoplay:   http://localhost:8009/omni-platform/docs/overlays/demo_autoplay.html
Frontend:   http://localhost:5175/
Backend:    http://localhost:8004/api/health
PDF:        http://localhost:8009/omni-platform/docs/investor_brief.pdf
```

---

## 🔧 Potrebni Strežniki

```bash
# Frontend (Terminal 1)
cd omni-platform/frontend
npm run dev  # → http://localhost:5175/

# Backend (Terminal 2)  
cd omni-platform/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8004 --reload

# Assets (Terminal 3)
python -m http.server 8009  # → http://localhost:8009/
```

---

## 📁 Datoteke

```
📂 omni-platform/docs/obs/
├── 🎬 omni_scene_collection.json    # Scene z hotkeys
├── ⚙️ omni_demo_profile.json        # Optimalne nastavitve
├── 📖 OBS_SETUP_NAVODILA.md        # Podrobna navodila
└── 📂 overlays/
    ├── title.html                  # Title card
    ├── lower-third.html            # Overlay
    ├── outro.html                  # Outro card
    └── demo_autoplay.html          # Avtomatski demo

📂 Root/
├── 🚀 Start-Autoplay-OBS.bat       # 1-klik zagon
├── 💻 Launch-Omni-Demo.ps1          # PowerShell launcher
├── 🔗 Create-Desktop-Shortcut.ps1   # Ustvari bližnjico
└── 📋 QUICK_START.md               # Ta datoteka
```

---

## ✅ Hitri Test

1. **Zaženi strežnike** (3 terminali)
2. **Uvozi v OBS** (scene + profile)
3. **Zaženi demo:** `.\Launch-Omni-Demo.ps1`
4. **OBS hotkeys:** F1-F5, SPACE, ESC

**🎯 Rezultat:** Profesionalen demo video z 1-klikom!