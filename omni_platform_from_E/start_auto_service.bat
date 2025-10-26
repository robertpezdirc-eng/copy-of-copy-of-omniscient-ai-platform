@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PYTHON_PATH={sys.executable}"
set "LAUNCHER_SCRIPT=%SCRIPT_DIR%omni_auto_launcher.py"

echo Starting OMNI Platform Auto Launcher Service...
echo Script Directory: %SCRIPT_DIR%
echo Python Path: %PYTHON_PATH%
echo Launcher Script: %LAUNCHER_SCRIPT%

cd /d "%SCRIPT_DIR%"
"%PYTHON_PATH%" "%LAUNCHER_SCRIPT%"

if errorlevel 1 (
    echo Service failed with exit code %errorlevel%
    timeout /t 30
    exit /b 1
) else (
    echo Service completed successfully
    exit /b 0
)
