# 🔑 OMNI AI API Setup Guide

## 🚨 Current Issue Fixed

The "Invalid character in header content" error has been resolved by:
- ✅ **API key cleaning** - Removes invalid characters automatically
- ✅ **Better error handling** - Provides helpful error messages
- ✅ **Fallback options** - Works with OMNI AI when external APIs fail

## 🔧 API Key Configuration

### Option 1: Environment Variables (Recommended)

#### Windows PowerShell:
```powershell
$env:OPENAI_API_KEY = "sk-your-openai-api-key-here"
$env:GEMINI_API_KEY = "your-gemini-api-key-here"
```

#### Windows Command Prompt:
```cmd
set OPENAI_API_KEY=sk-your-openai-api-key-here
set GEMINI_API_KEY=your-gemini-api-key-here
```

#### Linux/Mac:
```bash
export OPENAI_API_KEY="sk-your-openai-api-key-here"
export GEMINI_API_KEY="your-gemini-api-key-here"
```

### Option 2: .env File
Create a `.env` file in the omni-search directory:
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
GEMINI_API_KEY=your-gemini-api-key-here
```

## 🔑 Getting API Keys

### OpenAI API Key
1. Go to https://platform.openai.com/
2. Sign up/Login to your account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-`)

### Gemini API Key
1. Go to https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Create a new API key
4. Copy the key

## ✅ Current Status

After fixes, the system now shows:
```
🔵 System Status: STANDALONE
Connected Agents: 8 | API Health: Standalone
```

This means:
- ✅ **Search works** - All 8 agents available
- ✅ **Chat works** - OMNI AI responses available
- ✅ **Learning Overlay ready** - Background learning system ready
- ⚠️ **External AIs optional** - ChatGPT/Gemini need API keys for full functionality

## 🚀 Quick Test

1. **Open:** `http://localhost:8080`
2. **Search:** Type "omni" to see all agents
3. **Chat:** Click 💬 button and try OMNI AI provider
4. **Status:** Should show STANDALONE mode (fully functional)

## 🔧 Troubleshooting

### If you see API key errors:
1. **Check key format** - Should start with `sk-` for OpenAI
2. **Verify key validity** - Test key in official API docs
3. **Use OMNI AI** - Switch to OMNI provider for testing
4. **Check console** - Browser dev tools show detailed errors

### API Key Formats:
- **OpenAI:** `sk-...` (51 characters, starts with sk-)
- **Gemini:** `AIza...` (39 characters, starts with AIza)
- **OMNI:** Built-in (no key needed)

## 🎯 Next Steps

1. **Set API keys** using one of the methods above
2. **Restart servers** to pick up new environment variables
3. **Test ChatGPT** by selecting it in the chat dropdown
4. **Test Gemini** for analytical questions
5. **Use OMNI Director** for automatic AI selection

---

**✅ Your OMNI platform is fully functional even without external API keys!**
**🚀 Add API keys when ready for full ChatGPT/Gemini integration!**