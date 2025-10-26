#!/usr/bin/env python3
"""
Omni Platform Vertex AI Runner
Simple script to run omni platform with Vertex AI integration
"""

import os
import sys
import subprocess
import json
import time

def setup_vertex_ai():
    """Set up Vertex AI environment variables"""
    os.environ['VERTEX_AI_API_KEY'] = 'AQ.Ab8RN6LjDXj9_BHBcp-XvbSm0WCE2ftjfwyobHz-Zc3oNMVfhQ'
    os.environ['GOOGLE_CLOUD_PROJECT'] = 'refined-graph-471712-n9'
    os.environ['GOOGLE_CLOUD_REGION'] = 'europe-west1'
    os.environ['VERTEX_AI_MODEL'] = 'gemini-2.0-pro'
    os.environ['AI_PROVIDER'] = 'vertex_ai'
    os.environ['OMNI_HOME'] = '/tmp/omni-platform'
    os.environ['PYTHONPATH'] = '/tmp/omni-platform'

    print("✅ Vertex AI environment configured")

def test_vertex_ai():
    """Test Vertex AI connectivity"""
    try:
        import requests

        url = "https://europe-west1-aiplatform.googleapis.com/v1/projects/refined-graph-471712-n9/locations/europe-west1/publishers/google/models/gemini-2.0-pro:generateContent"
        headers = {
            'Authorization': f'Bearer {os.environ["VERTEX_AI_API_KEY"]}',
            'Content-Type': 'application/json'
        }
        data = {
            'contents': [{
                'parts': [{
                    'text': 'Hello from omni platform! This is a connectivity test.'
                }]
            }]
        }

        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            print("✅ Vertex AI connectivity test successful!")
            return True
        else:
            print(f"⚠️ Vertex AI test returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️ Vertex AI connectivity test failed: {e}")
        return False

def run_omni_platform():
    """Run the omni platform"""
    try:
        # Change to the omni platform directory
        os.chdir('/tmp/omni-platform')

        # Check if main omni platform file exists
        main_file = 'omni_platform_final.py'
        if not os.path.exists(main_file):
            print(f"❌ Main omni platform file not found: {main_file}")
            return False

        print(f"🚀 Starting omni platform with Vertex AI...")
        print(f"   Project: {os.environ.get('GOOGLE_CLOUD_PROJECT')}")
        print(f"   Region: {os.environ.get('GOOGLE_CLOUD_REGION')}")
        print(f"   Model: {os.environ.get('VERTEX_AI_MODEL')}")
        print(f"   AI Provider: {os.environ.get('AI_PROVIDER')}")

        # Start the omni platform
        cmd = [sys.executable, main_file]
        process = subprocess.Popen(cmd, cwd='/tmp/omni-platform')

        print(f"✅ Omni platform started with PID: {process.pid}")
        print(f"🌐 Access at: http://34.140.18.254:8080")
        print(f"📊 Monitor logs with: docker logs -f omni-platform")

        return True

    except Exception as e:
        print(f"❌ Failed to start omni platform: {e}")
        return False

def main():
    """Main function"""
    print("🤖 Omni Platform Vertex AI Runner")
    print("=" * 50)

    # Set up Vertex AI
    setup_vertex_ai()

    # Test connectivity
    print("\n🧪 Testing Vertex AI connectivity...")
    test_vertex_ai()

    # Run omni platform
    print("\n🚀 Starting omni platform...")
    if run_omni_platform():
        print("\n✅ Omni platform deployment successful!")
        print("\n📋 Platform Information:")
        print(f"   External IP: 34.140.18.254")
        print(f"   Port: 8080")
        print(f"   AI Provider: Vertex AI (Gemini 1.5 Pro)")
        print(f"   RAM: 64 GB")
        print(f"   Disk: 200 GB")
        print(f"   Region: europe-west1")
    else:
        print("\n❌ Failed to deploy omni platform")
        sys.exit(1)

if __name__ == "__main__":
    main()