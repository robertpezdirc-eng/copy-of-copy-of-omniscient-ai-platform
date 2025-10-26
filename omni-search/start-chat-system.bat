@echo off
echo 🚀 Starting OMNI Real-Time Chat System...
echo ======================================

echo.
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

echo.
echo 📦 Installing Node.js dependencies...
npm install

echo.
echo 🌐 Starting Flask API server...
start "OMNI Chat API" cmd /k "python chat_api.py"

echo.
echo ⚛️  Starting React frontend...
timeout /t 3 /nobreak > nul
start "OMNI Chat Frontend" cmd /k "npm start"

echo.
echo ✅ OMNI Chat System Started!
echo ============================
echo 🌐 API Server: http://localhost:8080
echo ⚛️  Frontend:   http://localhost:3000
echo.
echo Press any key to exit...
pause > nul