/**
 * 🚀 OMNI Desktop Application - Electron Main Process
 * Desktop verzija OMNI Web Dashboarda z nevidnim backend-om
 */

const { app, BrowserWindow, Menu, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

// Globalne spremenljivke
let mainWindow;
let backendProcess;

// OMNI konfiguracija
const OMNI_CONFIG = {
    backendPort: 3001,
    frontendPort: 8080,
    windowSize: {
        width: 1400,
        height: 900,
        minWidth: 800,
        minHeight: 600
    }
};

function createWindow() {
    // Ustvari glavno okno
    mainWindow = new BrowserWindow({
        width: OMNI_CONFIG.windowSize.width,
        height: OMNI_CONFIG.windowSize.height,
        minWidth: OMNI_CONFIG.windowSize.minWidth,
        minHeight: OMNI_CONFIG.windowSize.minHeight,
        icon: path.join(__dirname, 'assets', 'omni_icon.png'),
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            enableRemoteModule: false,
            preload: path.join(__dirname, 'preload.js')
        },
        show: false, // Ne pokaži dokler ni pripravljen
        title: 'OMNI AI Dashboard',
        darkTheme: true
    });

    // Odstrani meni
    mainWindow.setMenuBarVisibility(false);

    // Naloži OMNI dashboard
    mainWindow.loadURL(`http://localhost:${OMNI_CONFIG.frontendPort}`);

    // Počakaj da se stran naloži
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
        console.log('🖥️ OMNI Desktop okno odprto');
    });

    // Error handling za naložitev strani
    mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
        console.error('❌ Napaka pri nalaganju:', errorDescription);

        // Poskusi znova čez nekaj sekund
        setTimeout(() => {
            mainWindow.loadURL(`http://localhost:${OMNI_CONFIG.frontendPort}`);
        }, 3000);
    });

    // Odpri DevTools v development načinu
    if (process.env.NODE_ENV === 'development') {
        mainWindow.webContents.openDevTools();
    }

    // Handle window closed
    mainWindow.on('closed', () => {
        mainWindow = null;
        if (backendProcess) {
            backendProcess.kill();
            console.log('🛑 Backend proces zaustavljen');
        }
    });
}

async function startBackendServer() {
    return new Promise((resolve, reject) => {
        console.log('🚀 Začenjam OMNI backend server...');

        try {
            // Zaženi Node.js server
            backendProcess = spawn('node', ['../omni-search/server.js'], {
                cwd: __dirname,
                detached: true,
                stdio: ['ignore', 'pipe', 'pipe']
            });

            // Počakaj da se server zažene
            setTimeout(async () => {
                try {
                    // Preveri če server deluje
                    await checkServerHealth();
                    console.log('✅ OMNI backend server deluje');
                    resolve();
                } catch (error) {
                    console.error('❌ Backend server ni dosegljiv:', error.message);
                    reject(error);
                }
            }, 3000);

            // Log output
            backendProcess.stdout.on('data', (data) => {
                console.log('📤 Backend:', data.toString().trim());
            });

            backendProcess.stderr.on('data', (data) => {
                console.error('📥 Backend Error:', data.toString().trim());
            });

        } catch (error) {
            console.error('❌ Napaka pri zagonu backend-a:', error);
            reject(error);
        }
    });
}

async function checkServerHealth() {
    return new Promise((resolve, reject) => {
        const req = http.request({
            hostname: 'localhost',
            port: OMNI_CONFIG.backendPort,
            path: '/api/health',
            method: 'GET',
            timeout: 5000
        }, (res) => {
            if (res.statusCode === 200) {
                resolve();
            } else {
                reject(new Error(`Server responded with status ${res.statusCode}`));
            }
        });

        req.on('error', reject);
        req.on('timeout', () => {
            req.destroy();
            reject(new Error('Server health check timeout'));
        });

        req.end();
    });
}

async function startFrontendServer() {
    return new Promise((resolve, reject) => {
        console.log('🎨 Začenjam OMNI frontend server...');

        try {
            const frontendProcess = spawn('npm', ['run', 'dev', '--', '--port', OMNI_CONFIG.frontendPort.toString()], {
                cwd: path.join(__dirname, '../omni-search'),
                detached: true,
                stdio: ['ignore', 'pipe', 'pipe']
            });

            // Počakaj da se frontend zažene
            setTimeout(async () => {
                try {
                    await checkFrontendHealth();
                    console.log('✅ OMNI frontend server deluje');
                    resolve();
                } catch (error) {
                    console.error('❌ Frontend server ni dosegljiv:', error.message);
                    reject(error);
                }
            }, 5000);

        } catch (error) {
            console.error('❌ Napaka pri zagonu frontend-a:', error);
            reject(error);
        }
    });
}

async function checkFrontendHealth() {
    return new Promise((resolve, reject) => {
        const req = http.request({
            hostname: 'localhost',
            port: OMNI_CONFIG.frontendPort,
            path: '/',
            method: 'GET',
            timeout: 5000
        }, (res) => {
            if (res.statusCode === 200) {
                resolve();
            } else {
                reject(new Error(`Frontend responded with status ${res.statusCode}`));
            }
        });

        req.on('error', reject);
        req.on('timeout', () => {
            req.destroy();
            reject(new Error('Frontend health check timeout'));
        });

        req.end();
    });
}

// App event handlers
app.whenReady().then(async () => {
    console.log('🌐 Inicializacija OMNI Desktop aplikacije...');

    try {
        // Zaženi backend server
        await startBackendServer();

        // Zaženi frontend server
        await startFrontendServer();

        // Ustvari glavno okno
        createWindow();

        console.log('✅ OMNI Desktop aplikacija pripravljena!');
        console.log(`🖥️ Okno: ${OMNI_CONFIG.windowSize.width}x${OMNI_CONFIG.windowSize.height}`);
        console.log(`🌐 Frontend: http://localhost:${OMNI_CONFIG.frontendPort}`);
        console.log(`🔗 Backend: http://localhost:${OMNI_CONFIG.backendPort}/api`);

    } catch (error) {
        console.error('❌ Napaka pri inicializaciji:', error);

        // Prikaži error dialog
        dialog.showErrorBox(
            'OMNI Initialization Error',
            `Napaka pri zagonu OMNI aplikacije:\n\n${error.message}\n\nPreverite da so vsi potrebni procesi nameščeni.`
        );

        app.quit();
    }
});

// Prepreči novo okno če so vsa okna zaprta (razen na macOS)
app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

// Aktiviraj okno če aplikacija aktivirana brez oken (macOS)
app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('🛑 Zaustavljanje OMNI Desktop aplikacije...');

    if (backendProcess) {
        backendProcess.kill();
    }

    app.quit();
});

// IPC handlers za komunikacijo z renderer procesom
ipcMain.handle('get-system-info', () => {
    return {
        platform: process.platform,
        version: app.getVersion(),
        electronVersion: process.versions.electron,
        nodeVersion: process.versions.node
    };
});

ipcMain.handle('check-backend-status', async () => {
    try {
        await checkServerHealth();
        return { status: 'connected', port: OMNI_CONFIG.backendPort };
    } catch (error) {
        return { status: 'disconnected', error: error.message };
    }
});

ipcMain.handle('restart-backend', async () => {
    try {
        if (backendProcess) {
            backendProcess.kill();
        }
        await startBackendServer();
        return { success: true };
    } catch (error) {
        return { success: false, error: error.message };
    }
});

console.log('🚀 OMNI Desktop aplikacija se inicializira...');