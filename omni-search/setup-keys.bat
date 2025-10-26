@echo off
echo 🌐 OMNI AI - API Key Setup
echo ================================

echo.
echo Setting up API keys for OMNI platform...
echo.

REM Set your actual API keys here
set OPENAI_API_KEY=sk-proj-your-actual-openai-key-here
set GEMINI_API_KEY=your-actual-gemini-key-here

echo ✅ Environment variables set!
echo.
echo 🔑 API Keys Status:
echo    OpenAI: %OPENAI_API_KEY:~0,20%...
echo    Gemini: %GEMINI_API_KEY:~0,20%...
echo.
echo 🚀 Starting OMNI servers...
echo.
echo Terminal 1 - Backend API Server:
echo    node server.js
echo.
echo Terminal 2 - Frontend React App:
echo    npm run dev -- --port 8080
echo.
echo 🌐 Access your OMNI platform at:
echo    http://localhost:8080
echo.
echo 💡 To test ChatGPT integration:
echo    1. Open http://localhost:8080
echo    2. Click the chat button (💬)
echo    3. Select "ChatGPT" from dropdown
echo    4. Ask any question in Slovenian or English
echo.
echo 📚 To activate Learning Overlay:
echo    cd omni_learning_overlay
echo    python launch_overlay.py
echo.
pause