@echo off
REM 🚀 OMNI Desktop Launcher - Windows
REM Zažene backend in frontend skrito, odpre Electron okno

echo 🌐 OMNI AI Desktop - Silent Launch
echo ==================================

REM Preveri če so potrebne datoteke
if not exist "electron_main.js" (
    echo ❌ Error: electron_main.js not found!
    pause
    exit /b 1
)

if not exist "package.json" (
    echo ❌ Error: package.json not found!
    pause
    exit /b 1
)

REM Preveri če so Node dependencies nameščene
if not exist "node_modules" (
    echo 📦 Installing Node dependencies...
    call npm install
    if errorlevel 1 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
)

echo ✅ Starting OMNI Desktop Application...

REM Zaženi Electron aplikacijo
start /B npm start

REM Počakaj 3 sekunde
timeout /t 3 /nobreak > nul

echo ✅ OMNI Desktop Application started!
echo 🖥️ Look for the OMNI window on your desktop
echo 🛑 Close the window to exit the application
echo.
echo 💡 Troubleshooting:
echo    - If window doesn't open, check if ports 3001 and 8080 are free
echo    - Check firewall settings if you have connectivity issues
echo    - Make sure all dependencies are installed
echo.

pause