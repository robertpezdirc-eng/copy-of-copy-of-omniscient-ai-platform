#!/usr/bin/env python3
"""
OMNI VR + GCS Complete Setup Script
Sets up VR headset integration and Google Cloud Storage auto-upload
"""

import os
import json
import time
import subprocess
from pathlib import Path
from omni_event_logger import EventLogger

class OmniVRGCSSetup:
    def __init__(self):
        self.logger = EventLogger()
        self.project_root = Path(__file__).parent

    def check_requirements(self):
        """Check if all required files exist"""
        required_files = [
            "omni_vr_connector.py",
            "omni_gcs_uploader.py",
            "omni_autolearn_starter.py",
            "omni_autolearn_config.json"
        ]

        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)

        if missing_files:
            print(f"ERROR: Missing required files: {', '.join(missing_files)}")
            return False

        print("All required files present")
        return True

    def setup_google_cloud_credentials(self):
        """Set up Google Cloud credentials"""
        print("\n=== Google Cloud Setup ===")

        # Check for existing credentials
        credential_paths = [
            "service-account.json",
            "credentials/service-account.json",
            os.path.expanduser("~/service-account.json")
        ]

        existing_cred = None
        for path in credential_paths:
            if os.path.exists(path):
                existing_cred = path
                break

        if existing_cred:
            print(f"Found existing credentials: {existing_cred}")
            use_existing = input("Use existing credentials? (y/n): ").lower().strip()
            if use_existing == 'y':
                return True

        print("Setting up Google Cloud credentials...")
        print("You have several options:")
        print("1. Use service account JSON key file")
        print("2. Use gcloud CLI authentication")
        print("3. Use default credentials (if running on GCE/GKE)")

        choice = input("Choose option (1-3): ").strip()

        if choice == "1":
            print("Please place your service-account.json file in the project root")
            print("Or specify the path to your service account JSON file:")
            json_path = input("Path to service account JSON: ").strip().strip('"')

            if os.path.exists(json_path):
                # Copy to project root for consistency
                dest_path = "service-account.json"
                import shutil
                shutil.copy2(json_path, dest_path)
                print(f"Copied credentials to: {dest_path}")
                return True
            else:
                print(f"File not found: {json_path}")
                return False

        elif choice == "2":
            print("Authenticating with gcloud CLI...")
            try:
                # Try to authenticate
                result = subprocess.run(["gcloud", "auth", "application-default", "login"],
                                      capture_output=True, text=True)

                if result.returncode == 0:
                    print("gcloud authentication successful")
                    return True
                else:
                    print("gcloud authentication failed")
                    print("Please run: gcloud auth application-default login")
                    return False

            except FileNotFoundError:
                print("gcloud CLI not found. Please install Google Cloud SDK")
                print("https://cloud.google.com/sdk/docs/install")
                return False

        elif choice == "3":
            print("Using default credentials...")
            try:
                import google.auth
                creds, project = google.auth.default()
                print("Default credentials available")
                return True
            except Exception as e:
                print(f"Default credentials not available: {e}")
                return False

        return False

    def test_gcs_connection(self):
        """Test Google Cloud Storage connection"""
        print("\n=== Testing GCS Connection ===")

        try:
            from omni_gcs_uploader import OmniGCSUploader
            uploader = OmniGCSUploader()

            if uploader.setup_gcp_credentials():
                print("Credentials: OK")

                if uploader.ensure_bucket_exists():
                    print("Bucket: OK")

                    # Try a test upload
                    test_data = {"test": True, "timestamp": time.time()}
                    test_file = "test_gcs_connection.json"

                    with open(test_file, 'w') as f:
                        json.dump(test_data, f)

                    if uploader.upload_to_gcs(test_file, "test/test_connection.json"):
                        print("Upload test: SUCCESS")
                        os.remove(test_file)
                        return True
                    else:
                        print("Upload test: FAILED")
                        os.remove(test_file)
                        return False
                else:
                    print("Bucket creation/access: FAILED")
                    return False
            else:
                print("Credentials setup: FAILED")
                return False

        except Exception as e:
            print(f"GCS test failed: {e}")
            return False

    def test_vr_integration(self):
        """Test VR integration"""
        print("\n=== Testing VR Integration ===")

        try:
            from omni_vr_starter import OmniVRStarter
            vr_starter = OmniVRStarter()

            print("Creating VR test files...")
            unity_file = vr_starter.create_unity_example()
            test_file = vr_starter.create_vr_test_client()

            print(f"Created Unity script: {unity_file}")
            print(f"Created test client: {test_file}")

            print("Testing VR connector...")
            if vr_starter.test_vr_connector():
                print("VR connector: OK")
                return True
            else:
                print("VR connector: FAILED")
                return False

        except Exception as e:
            print(f"VR test failed: {e}")
            return False

    def create_startup_scripts(self):
        """Create startup scripts for easy operation"""
        print("\n=== Creating Startup Scripts ===")

        # Windows batch script
        windows_script = '''
@echo off
echo Starting OMNI VR Learning Platform...
echo ====================================

echo Starting auto-learning system...
start "OMNI Auto-Learning" cmd /k "python omni_autolearn_starter.py"

echo Starting GCS uploader...
start "OMNI GCS Uploader" cmd /k "python omni_gcs_uploader.py"

echo Starting VR listener...
start "OMNI VR Listener" cmd /k "python omni_vr_starter.py"

echo All services started!
echo - Auto-learning: Collects and processes VR data
echo - GCS uploader: Uploads summaries to Google Cloud
echo - VR listener: Receives data from VR headsets
echo.
echo Press any key to stop all services...
pause >nul

echo Stopping all services...
taskkill /FI "WINDOWTITLE eq OMNI Auto-Learning*" /T /F
taskkill /FI "WINDOWTITLE eq OMNI GCS Uploader*" /T /F
taskkill /FI "WINDOWTITLE eq OMNI VR Listener*" /T /F
'''

        # Unix shell script
        unix_script = '''#!/bin/bash
echo "Starting OMNI VR Learning Platform..."
echo "===================================="

echo "Starting auto-learning system..."
python omni_autolearn_starter.py &
AUTO_LEARN_PID=$!

echo "Starting GCS uploader..."
python omni_gcs_uploader.py &
GCS_PID=$!

echo "Starting VR listener..."
python omni_vr_starter.py &
VR_PID=$!

echo "All services started!"
echo "- Auto-learning: Collects and processes VR data (PID: $AUTO_LEARN_PID)"
echo "- GCS uploader: Uploads summaries to Google Cloud (PID: $GCS_PID)"
echo "- VR listener: Receives data from VR headsets (PID: $VR_PID)"
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait for interrupt
trap "echo 'Stopping all services...'; kill $AUTO_LEARN_PID $GCS_PID $VR_PID; exit" INT
wait
'''

        # Write Windows script
        with open("start_omni_vr_platform.bat", "w") as f:
            f.write(windows_script)

        # Write Unix script
        with open("start_omni_vr_platform.sh", "w") as f:
            f.write(unix_script)

        # Make Unix script executable
        try:
            os.chmod("start_omni_vr_platform.sh", 0o755)
        except:
            pass

        print("Created startup scripts:")
        print("- start_omni_vr_platform.bat (Windows)")
        print("- start_omni_vr_platform.sh (Unix/Mac)")

    def show_final_instructions(self):
        """Show final setup instructions"""
        print("\n" + "="*60)
        print("🎉 OMNI VR + GCS Setup Complete!")
        print("="*60)

        print("\n📋 Next Steps:")
        print("1. 🔑 Set up Google Cloud credentials (if not done)")
        print("2. 🕶️  Connect your VR headset:")
        print("   - Use Meta Quest 3, Pico, or HTC Vive")
        print("   - Run: python omni_vr_starter.py")
        print("   - Or use the provided Unity script")
        print("3. 🤖 Start learning: python omni_autolearn_starter.py")
        print("4. ☁️  Monitor cloud uploads: python omni_gcs_uploader.py")

        print("\n📁 Files Created:")
        print("- omni_vr_starter.py (VR headset management)")
        print("- omni_gcs_uploader.py (Cloud storage)")
        print("- omni_vr_unity_example.cs (Unity integration)")
        print("- simulate_vr_headset.py (VR testing)")
        print("- start_omni_vr_platform.bat/sh (Startup scripts)")

        print("\n🔧 VR Headset Setup:")
        print("- Meta Quest 3: Use SideQuest + Unity or Oculus Developer Hub")
        print("- Unity: Import omni_vr_unity_example.cs")
        print("- Network: Ensure VR device can reach this machine on port 9090")

        print("\n☁️  Google Cloud Setup:")
        print("- Bucket: omni-meta-data (auto-created)")
        print("- Storage: gs://omni-meta-data/models/")
        print("- Auto-upload: Runs every learning cycle")

        print("\n🚀 Quick Start:")
        print("1. Run: python start_omni_vr_platform.sh")
        print("2. Connect VR headset to send data")
        print("3. Watch learning summaries upload to Google Cloud")

        print("\n📊 Monitoring:")
        print("- Local logs: Check .log files")
        print("- Cloud data: gs://omni-meta-data/models/")
        print("- Real-time: Check learn_summary.json")

def main():
    """Main setup function"""
    print("OMNI VR + GCS Complete Setup")
    print("=" * 50)

    setup = OmniVRGCSSetup()

    # Check requirements
    if not setup.check_requirements():
        return False

    # Setup Google Cloud
    if not setup.setup_google_cloud_credentials():
        print("Google Cloud setup failed. You can still use VR features locally.")
        print("Run 'python omni_gcs_uploader.py' later to set up cloud storage.")

    # Test GCS connection
    if setup.test_gcs_connection():
        print("GCS connection: SUCCESS")
    else:
        print("GCS connection: FAILED (but VR features still work)")

    # Test VR integration
    if setup.test_vr_integration():
        print("VR integration: SUCCESS")
    else:
        print("VR integration: FAILED")

    # Create startup scripts
    setup.create_startup_scripts()

    # Show final instructions
    setup.show_final_instructions()

    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Setup completed successfully!")
    else:
        print("\n❌ Setup completed with errors. Check the messages above.")