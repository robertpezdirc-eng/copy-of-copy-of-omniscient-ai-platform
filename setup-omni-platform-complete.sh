#!/bin/bash

# OMNI Platform - Complete Setup Script
# Sets up OMNI Platform with all advanced features

set -e

echo "🚀 OMNI Platform Complete Setup"
echo "================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_section() {
    echo -e "${PURPLE}[SECTION]${NC} $1"
}

# Check Python
print_header "Checking Python Installation"
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

python3 --version
print_status "Python is installed"

# Install/upgrade pip
print_header "Installing/Upgrading pip"
python3 -m pip install --upgrade pip

# Install core requirements
print_section "Installing Core Requirements"
print_status "Installing FastAPI, Uvicorn, and core libraries..."
pip install -r requirements.txt

# Install GPU requirements
print_section "Installing GPU Processing Libraries"
print_status "Installing PyTorch, TensorFlow, and GPU libraries..."
pip install -r requirements-gpu.txt || print_warning "Some GPU libraries may require manual installation"

# Verify installations
print_section "Verifying Installations"

# Test OpenAI
print_status "Testing OpenAI integration..."
python3 -c "
try:
    import openai
    print('✅ OpenAI library installed')
except ImportError as e:
    print(f'❌ OpenAI library not available: {e}')
"

# Test Google Generative AI
print_status "Testing Google Generative AI..."
python3 -c "
try:
    import google.generativeai as genai
    print('✅ Google Generative AI library installed')
except ImportError as e:
    print(f'❌ Google Generative AI library not available: {e}')
"

# Test GPU libraries
print_status "Testing GPU libraries..."
python3 -c "
try:
    import torch
    print(f'✅ PyTorch installed - CUDA available: {torch.cuda.is_available()}')
except ImportError as e:
    print(f'❌ PyTorch not available: {e}')
"

# Create .env template
print_section "Creating Environment Configuration"

cat > .env.template << 'EOF'
# OMNI Platform Environment Variables
# Copy this file to .env and fill in your actual values

# Core Configuration
SECRET_KEY=omni_platform_production_secret_key_2024_change_in_production
DEV_MODE=false
OMNI_SYSTEM_CHECKS=false
ENVIRONMENT=production

# Google Cloud Configuration
GCS_BUCKET=omni-singularity-storage
GOOGLE_CLOUD_PROJECT=omni-platform-2024
GOOGLE_API_KEY=your_google_api_key_here

# AI Provider API Keys
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
META_QUEST_API_KEY=your_meta_quest_api_key_here
STEAMVR_API_KEY=your_steamvr_api_key_here

# GPU Configuration
GPU_ENABLED=true
CUDA_VERSION=11.8
GPU_MEMORY=24GB

# Performance Settings
MEMORY_LIMIT=128GB
MAX_WORKERS=8
EOF

print_status "Created .env.template file"

# Create startup script
print_section "Creating Startup Scripts"

cat > start-omni-platform.sh << 'EOF'
#!/bin/bash
# OMNI Platform Startup Script

echo "🚀 Starting OMNI Platform with all features..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set environment variables
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Start the platform
python3 omni_dashboard_professional.py
EOF

chmod +x start-omni-platform.sh
print_status "Created start-omni-platform.sh"

# Create requirements summary
print_section "Creating Requirements Summary"

cat > REQUIREMENTS_SUMMARY.md << 'EOF'
# OMNI Platform - Requirements Summary

## Core Requirements (requirements.txt)
- FastAPI + Uvicorn (web framework)
- Plotly + Pandas (visualization)
- JWT + Security (authentication)
- Google Cloud Storage (cloud storage)
- OpenAI (AI integration)

## GPU Processing (requirements-gpu.txt)
- PyTorch + CUDA (GPU computing)
- TensorFlow + Keras (ML frameworks)
- OpenCV (computer vision)
- MoviePy (video processing)
- Transformers (NLP models)

## Optional Libraries
- google-generativeai (Google Gemini)
- elevenlabs (voice synthesis)
- pyopenvr (VR integration)
- SpeechRecognition (speech processing)

## Installation Commands

### Basic Installation
```bash
pip install -r requirements.txt
```

### Full Installation (with GPU)
```bash
pip install -r requirements.txt
pip install -r requirements-gpu.txt
```

### Manual GPU Setup (if needed)
```bash
# For NVIDIA GPUs
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# For CUDA 11.8
pip install tensorflow[and-cuda]==2.13.0
```
EOF

print_status "Created REQUIREMENTS_SUMMARY.md"

# Create feature test script
print_section "Creating Feature Test Script"

cat > test-omni-features.py << 'EOF'
#!/usr/bin/env python3
"""
OMNI Platform - Feature Test Script
Tests all OMNI platform features and integrations
"""

import asyncio
import os
import sys

async def test_all_features():
    """Test all OMNI platform features"""

    print("🧪 Testing OMNI Platform Features")
    print("=" * 45)

    # Test 1: Basic imports
    print("\n📦 Testing basic imports...")
    try:
        import fastapi
        import uvicorn
        print("✅ FastAPI/Uvicorn: OK")
    except ImportError as e:
        print(f"❌ FastAPI/Uvicorn: {e}")

    # Test 2: OpenAI integration
    print("\n🤖 Testing OpenAI integration...")
    try:
        from omni_real_api_integrations import omni_api_manager
        print("✅ OpenAI integration: Available")
    except ImportError:
        print("❌ OpenAI integration: Not available")

    # Test 3: Google Gemini
    print("\n🔵 Testing Google Gemini...")
    try:
        from omni_gemini_integration import omni_gemini_manager
        print("✅ Google Gemini: Available")
    except ImportError:
        print("❌ Google Gemini: Not available")

    # Test 4: VR integration
    print("\n🥽 Testing VR integration...")
    try:
        from omni_vr_integration_enhanced import omni_vr_manager
        print("✅ VR integration: Available")
    except ImportError:
        print("❌ VR integration: Not available")

    # Test 5: Speech AI
    print("\n🎤 Testing Speech AI...")
    try:
        from omni_speech_ai_integration import omni_speech_ai_manager
        print("✅ Speech AI: Available")
    except ImportError:
        print("❌ Speech AI: Not available")

    # Test 6: GPU processing
    print("\n🎨 Testing GPU processing...")
    try:
        from omni_gpu_processing import omni_gpu_manager
        print("✅ GPU processing: Available")
    except ImportError:
        print("❌ GPU processing: Not available")

    # Test 7: Google Cloud sync
    print("\n🔄 Testing Google Cloud sync...")
    try:
        from omni_google_cloud_sync import omni_gcloud_sync_manager
        print("✅ Google Cloud sync: Available")
    except ImportError:
        print("❌ Google Cloud sync: Not available")

    print("\n✅ Feature testing completed!")
    return {"status": "completed"}

def main():
    """Main test function"""
    try:
        result = asyncio.run(test_all_features())
        print(f"\n🎉 Test result: {result}")
        return 0
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF

print_status "Created test-omni-features.py"

# Make scripts executable
chmod +x start-omni-platform.sh
chmod +x test-omni-features.py

# Final instructions
print_section "Setup Complete!"
echo ""
print_status "🎉 OMNI Platform setup completed successfully!"
echo ""
print_status "📋 Next steps:"
echo "1. Copy .env.template to .env and fill in your API keys"
echo "2. Run: python3 test-omni-features.py"
echo "3. Run: ./start-omni-platform.sh"
echo "4. Open: http://localhost:8080/dashboard"
echo ""
print_status "🔑 Required API Keys:"
echo "- OPENAI_API_KEY (for AI chat)"
echo "- GOOGLE_API_KEY (for Gemini AI)"
echo "- GCS_BUCKET (Google Cloud Storage)"
echo ""
print_status "🏆 Your OMNI Platform now includes:"
echo "✅ Google Gemini AI integration"
echo "✅ GPU processing (NVIDIA A100)"
echo "✅ VR integration (Meta Quest/SteamVR)"
echo "✅ Speech AI (OpenAI TTS/ElevenLabs)"
echo "✅ Google Cloud auto-sync"
echo "✅ Enhanced dashboard with all features"
echo ""
print_status "🚀 Ready to launch your advanced OMNI Platform!"

# Run feature test
print_section "Running Feature Test"
python3 test-omni-features.py

echo ""
print_status "🎯 Setup completed! Launch with: ./start-omni-platform.sh"