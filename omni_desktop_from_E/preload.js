/**
 * 🔒 OMNI Desktop - Preload Script
 * Varnostna komunikacija med main in renderer procesoma
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
    // System information
    getSystemInfo: () => ipcRenderer.invoke('get-system-info'),

    // Backend status
    checkBackendStatus: () => ipcRenderer.invoke('check-backend-status'),
    restartBackend: () => ipcRenderer.invoke('restart-backend'),

    // Platform info
    platform: process.platform,

    // Version info
    versions: {
        node: process.versions.node,
        chrome: process.versions.chrome,
        electron: process.versions.electron
    }
});

// Log successful preload
console.log('🔒 OMNI Desktop preload script loaded successfully');