@echo off
REM 🚀 OMNI Desktop Launcher - Complete System
REM Zažene celoten OMNI sistem (backend, frontend, desktop app)

echo 🌐 OMNI AI Desktop - Complete Launch
echo ====================================

REM Preveri če so potrebne datoteke
if not exist "electron_main.js" (
    echo ❌ Error: electron_main.js not found!
    echo Make sure you're running from the omni_desktop directory
    pause
    exit /b 1
)

echo 📋 Checking system requirements...

REM Preveri Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed!
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Preveri npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ npm is not installed!
    echo Please install npm (comes with Node.js)
    pause
    exit /b 1
)

echo ✅ System requirements OK

REM Namesti dependencies če potrebno
if not exist "node_modules" (
    echo 📦 Installing Electron dependencies...
    call npm install
    if errorlevel 1 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
)

echo ✅ Dependencies installed

REM Preveri če omni-search direktorij obstaja
if not exist "../omni-search" (
    echo ❌ Error: omni-search directory not found!
    echo Make sure omni-search is in the parent directory
    pause
    exit /b 1
)

echo ✅ OMNI Search interface found

REM Zaženi backend server v ozadju
echo 🚀 Starting OMNI Backend Server...
start "OMNI Backend" cmd /k "cd ../omni-search && node server.js"

REM Počakaj 3 sekunde da se backend zažene
timeout /t 3 /nobreak > nul

REM Zaženi frontend server v ozadju
echo 🎨 Starting OMNI Frontend Server...
start "OMNI Frontend" cmd /k "cd ../omni-search && npm run dev -- --port 8080"

REM Počakaj 5 sekund da se frontend zažene
timeout /t 5 /nobreak > nul

REM Zaženi Electron desktop aplikacijo
echo 🖥️ Starting OMNI Desktop Application...
call npm start

echo ✅ OMNI Desktop Application started!
echo.
echo 💡 What you should see:
echo    🖥️ Desktop window with OMNI interface
echo    🌐 Backend running on port 3001
echo    🎨 Frontend running on port 8080
echo    🤖 All AI services connected
echo.
echo 🛑 To exit:
echo    Close the desktop window
echo    Or press Ctrl+C in this terminal
echo.
echo 🚀 Your OMNI Desktop is ready!
echo.

pause