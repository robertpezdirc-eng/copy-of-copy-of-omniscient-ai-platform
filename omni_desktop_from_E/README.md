# 🖥️ OMNI Desktop Application

## 📋 Overview

Electron-based desktop wrapper for the OMNI AI Web Dashboard. Provides a native desktop experience with hidden backend servers and no visible command prompts.

## ✨ Features

### 🖥️ Desktop Experience
- **Native window** with custom OMNI branding
- **No visible terminals** - everything runs silently
- **System tray integration** (planned)
- **Custom window controls** and behavior
- **Responsive design** for different screen sizes

### 🔧 Backend Integration
- **Hidden backend server** (port 3001)
- **Hidden frontend server** (port 8080)
- **Automatic startup** of all services
- **Error handling** and recovery
- **Process management** and monitoring

### 🎨 OMNI Branding
- **Custom icon** with neon OMNI logo
- **Dark theme** optimized for AI interface
- **Consistent styling** with web version
- **Professional appearance** for business use

## 🚀 Quick Start

### Prerequisites
```bash
# Node.js 16+ (already installed)
# Git (for cloning if needed)
```

### Installation
```bash
# Navigate to desktop app directory
cd omni_desktop

# Install Electron dependencies
npm install

# Install frontend dependencies (if not already done)
cd ../omni-search
npm install
cd ../omni_desktop
```

### Launch Options

#### Option 1: Complete Launch (Recommended)
```bash
# Double-click this file:
launch_omni_desktop.bat
```

#### Option 2: Manual Launch
```bash
# Terminal 1 - Backend API Server
cd ../omni-search && node server.js

# Terminal 2 - Frontend React App
cd ../omni-search && npm run dev -- --port 8080

# Terminal 3 - Electron Desktop App
npm start
```

#### Option 3: Development Mode
```bash
# With debug console
npm run dev
```

## 📁 Project Structure

```
omni_desktop/
├── electron_main.js       # Main Electron process
├── package.json           # Electron configuration
├── preload.js             # Security preload script
├── launch_omni_desktop.bat # Windows launcher
├── README.md              # This file
└── assets/
    ├── omni_icon.svg      # OMNI logo/icon
    └── [icon files]       # Platform-specific icons
```

## 🔧 Configuration

### Window Settings
```javascript
// In electron_main.js
const windowConfig = {
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    icon: 'assets/omni_icon.png',
    show: false  // Don't show until ready
}
```

### Server Ports
```javascript
const PORTS = {
    backend: 3001,   // API server
    frontend: 8080   // React dev server
}
```

### Security Settings
```javascript
const securityConfig = {
    nodeIntegration: false,      // Security best practice
    contextIsolation: true,      // Isolate contexts
    enableRemoteModule: false,   // Disable remote module
    preload: 'preload.js'        // Secure preload script
}
```

## 🎯 Usage

### Desktop Application
1. **Launch** using `launch_omni_desktop.bat`
2. **Wait** for all services to start
3. **Use** the OMNI interface in the desktop window
4. **Close** the window to exit (servers stop automatically)

### Development
1. **Start backend:** `node server.js` (in omni-search)
2. **Start frontend:** `npm run dev` (in omni-search)
3. **Start Electron:** `npm start` (in omni_desktop)
4. **Debug** using Chrome DevTools in the window

### Troubleshooting
1. **Check ports** - Ensure 3001 and 8080 are free
2. **Dependencies** - Run `npm install` in both directories
3. **API keys** - Set OPENAI_API_KEY for ChatGPT features
4. **Firewall** - Allow Node.js through Windows firewall

## 🔗 Integration

### OMNI Search Interface
- **Loads** `http://localhost:8080` in desktop window
- **All features** work identically to web version
- **Same API** endpoints and functionality
- **Identical UI/UX** experience

### Backend Services
- **Hidden Node.js server** on port 3001
- **ChatGPT integration** with your API key
- **Gemini integration** ready for setup
- **OMNI Director** AI coordination
- **Learning overlay** background processing

## 📦 Build & Distribution

### Build for Production
```bash
# Build Electron app
npm run build

# Platform-specific builds
npm run build-win    # Windows
npm run build-mac    # macOS
npm run build-linux  # Linux
```

### Distribution Files
- **Windows:** `.exe` installer + portable
- **macOS:** `.dmg` disk image
- **Linux:** `.AppImage` portable app

## 🔧 Development

### Adding Features
1. **Modify** `electron_main.js` for window behavior
2. **Update** `preload.js` for secure API access
3. **Edit** window configuration in `createWindow()`
4. **Test** with `npm run dev`

### Custom Integration
```javascript
// Add custom menu
const menuTemplate = [
    // Custom menu items
];

// Set application menu
Menu.setApplicationMenu(Menu.buildFromTemplate(menuTemplate));
```

### System Tray (Future)
```javascript
// Add to system tray
const tray = new Tray('assets/omni_icon.png');
tray.setToolTip('OMNI AI Dashboard');
```

## 🛠️ Troubleshooting

### Common Issues

**1. Window doesn't open**
```
Solution: Check if ports 3001 and 8080 are available
Fix: Change ports in electron_main.js
```

**2. Backend connection fails**
```
Solution: Ensure backend server is running
Fix: Check firewall and antivirus settings
```

**3. Dependencies missing**
```
Solution: Run npm install in both directories
Fix: Delete node_modules and reinstall
```

**4. API keys not working**
```
Solution: Set environment variables before starting
Fix: Use setup-keys.bat script
```

### Debug Mode
```bash
# Start with debug console
npm run dev

# Check console output for errors
# Use Chrome DevTools in the window
```

## 🚀 Advanced Features

### Auto-Update (Future)
```javascript
// Enable auto-updates
const updater = new ElectronUpdater();
updater.checkForUpdatesAndNotify();
```

### Multi-Window Support
```javascript
// Create additional windows
const settingsWindow = new BrowserWindow({...});
settingsWindow.loadURL('settings.html');
```

### Native Notifications
```javascript
// Desktop notifications
new Notification({
    title: 'OMNI Alert',
    body: 'Agent learning completed'
});
```

## 📞 Support

### Architecture
- **Main Process:** `electron_main.js` (Node.js)
- **Renderer Process:** Your React app (Browser)
- **Preload Script:** `preload.js` (Security bridge)
- **Backend Servers:** Hidden Node.js processes

### Communication
- **IPC:** Secure communication between processes
- **HTTP:** API calls to backend services
- **WebSocket:** Real-time updates (future)
- **File System:** Local data storage

---

**🖥️ Part of the OMNI AI Desktop Ecosystem**
**Seamlessly integrates web and desktop experiences**