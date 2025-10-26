const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const isDev = process.env.ELECTRON_IS_DEV;

let mainWindow;

function createWindow() {
    // Create the browser window
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            enableRemoteModule: true
        },
        icon: path.join(__dirname, 'assets/omni-icon.png'),
        title: 'OMNI Advanced Build System'
    });

    // Load the app
    const startUrl = isDev
        ? 'http://localhost:3000'
        : `file://${path.join(__dirname, '../build/index.html')}`;

    mainWindow.loadURL(startUrl);

    // Open DevTools in development
    if (isDev) {
        mainWindow.webContents.openDevTools();
    }

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

// App event listeners
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

// IPC handlers for OMNI platform integration
ipcMain.handle('omni-platform-status', async () => {
    return {
        status: 'active',
        version: '3.0.0',
        features: [
            'AI_Powered_Build_Prediction',
            'Quantum_Inspired_Optimization',
            'Distributed_Build_Coordinator',
            'Self_Healing_Build_Recovery',
            'Real_Time_Build_Analytics'
        ]
    };
});

ipcMain.handle('execute-build', async (event, modules) => {
    return {
        success: true,
        message: `Building modules: ${modules.join(', ')}`,
        estimated_time: '2-5 minutes'
    };
});