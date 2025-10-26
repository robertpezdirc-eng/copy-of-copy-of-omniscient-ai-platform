@echo off
setlocal enabledelayedexpansion

REM LocalTunnel VR Gateway Setup Script for Windows
REM Provides HTTPS tunneling for VR glasses compatibility during development

echo 🚀 Setting up LocalTunnel for VR Gateway...
echo =============================================

REM Default configuration
set "PORT=8080"
set "SUBDOMAIN=omni-vr-%random%"
set "VR_CONFIG_FILE=vr_gateway.json"

REM Check if arguments are provided
if not "%1"=="" set "PORT=%1"
if not "%2"=="" set "SUBDOMAIN=%2"

echo [INFO] Port: %PORT%
echo [INFO] Subdomain: %SUBDOMAIN%
echo [INFO] VR Config: %VR_CONFIG_FILE%

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed. Please install Node.js to use LocalTunnel.
    pause
    exit /b 1
)

REM Check if LocalTunnel is installed
npm list -g localtunnel >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing LocalTunnel...
    npm install -g localtunnel
    if errorlevel 1 (
        echo [ERROR] Failed to install LocalTunnel. Please check your npm permissions.
        pause
        exit /b 1
    )
)

REM Check if VR config exists
if not exist "%VR_CONFIG_FILE%" (
    echo [WARNING] VR config file not found. Creating default config...
    (
        echo {
        echo   "vr_config": {
        echo     "version": "1.0.0",
        echo     "name": "Omni VR Gateway - LocalTunnel",
        echo     "description": "Local development VR gateway with HTTPS tunneling",
        echo     "enabled": true,
        echo     "localtunnel": true,
        echo     "https_enforced": true
        echo   },
        echo   "tunnel": {
        echo     "provider": "localtunnel",
        echo     "auto_start": true,
        echo     "restart_on_failure": true
        echo   }
        echo }
    ) > "%VR_CONFIG_FILE%"
    echo [SUCCESS] Created default VR config file
)

REM Start LocalTunnel
echo [INFO] Starting HTTPS tunnel for VR glasses...
echo [INFO] This will provide a secure HTTPS URL for VR devices
echo.
echo [WARNING] Make sure your local server is running on port %PORT%
echo.

REM Start LocalTunnel in background
start "LocalTunnel VR Gateway" cmd /k "lt --port %PORT% --subdomain %SUBDOMAIN%"

echo [SUCCESS] LocalTunnel started
echo [SUCCESS] Your HTTPS URL for VR glasses: https://%SUBDOMAIN%.loca.lt
echo.
echo 🌐 VR Gateway Information:
echo ==========================
echo HTTPS URL: https://%SUBDOMAIN%.loca.lt
echo Local Port: %PORT%
echo.
echo 📱 For VR Glasses:
echo    - Open Oculus Browser on Quest
echo    - Navigate to: https://%SUBDOMAIN%.loca.lt/vr/trampoline
echo    - Click 'Enter VR' button
echo.
echo 💡 Tips:
echo    - Keep this command window open
echo    - Close the new LocalTunnel window to stop the tunnel
echo    - Restart if connection drops
echo.

pause