#!/usr/bin/env python3
"""
OMNI VR Learning Launcher - Complete VR Integration Startup
Starts VR data collection and learning from Meta Quest 3 movements
"""

import os
import json
import time
import subprocess
import threading
from pathlib import Path
from omni_event_logger import EventLogger

class OmniVRLearningLauncher:
    def __init__(self):
        self.logger = EventLogger()
        self.vr_connector = None
        self.gcs_uploader = None
        self.auto_learner = None
        self.running = False

    def check_prerequisites(self):
        """Check if all required components are available"""
        print("Checking prerequisites...")

        required_files = [
            "omni_vr_connector.py",
            "omni_gcs_uploader.py",
            "omni_autolearn_starter.py",
            "omni_autolearn_config.json"
        ]

        missing = []
        for file in required_files:
            if not os.path.exists(file):
                missing.append(file)

        if missing:
            print(f"ERROR: Missing files: {', '.join(missing)}")
            return False

        print("All prerequisite files found")
        return True

    def start_vr_listener(self):
        """Start VR data listener"""
        try:
            from omni_vr_connector import OmniVRConnector

            print("Starting VR listener on port 9090...")
            self.vr_connector = OmniVRConnector({})

            # Start listener in background thread
            def listen_for_vr():
                while self.running:
                    try:
                        vr_data = self.vr_connector.listen()
                        if vr_data:
                            self.logger.log(f"VR Data: {vr_data.get('event_type', 'unknown')}")
                            print(f"VR Data Received: {vr_data.get('event_type', 'unknown')}")
                    except Exception as e:
                        self.logger.log(f"VR listen error: {e}")
                        time.sleep(1)

            vr_thread = threading.Thread(target=listen_for_vr, daemon=True)
            vr_thread.start()

            print("VR listener started - waiting for headset data...")
            return True

        except Exception as e:
            print(f"Failed to start VR listener: {e}")
            return False

    def start_gcs_uploader(self):
        """Start Google Cloud Storage uploader"""
        try:
            from omni_gcs_uploader import OmniGCSUploader

            print("Starting GCS uploader...")
            self.gcs_uploader = OmniGCSUploader()

            # Start uploader in background thread
            def upload_to_cloud():
                while self.running:
                    try:
                        self.gcs_uploader.check_and_upload()
                    except Exception as e:
                        self.logger.log(f"GCS upload error: {e}")
                    time.sleep(60)  # Check every minute

            gcs_thread = threading.Thread(target=upload_to_cloud, daemon=True)
            gcs_thread.start()

            print("GCS uploader started")
            return True

        except Exception as e:
            print(f"Failed to start GCS uploader: {e}")
            return False

    def start_auto_learning(self):
        """Start the auto-learning system"""
        try:
            print("Starting auto-learning system...")

            # Import here to avoid circular dependencies
            import importlib.util
            spec = importlib.util.spec_from_file_location("omni_autolearn_starter", "omni_autolearn_starter.py")
            module = importlib.util.module_from_spec(spec)

            # Start learning in background thread
            def run_learning():
                try:
                    spec.loader.exec_module(module)
                    module.main()
                except Exception as e:
                    self.logger.log(f"Auto-learning error: {e}")

            learning_thread = threading.Thread(target=run_learning, daemon=True)
            learning_thread.start()

            print("Auto-learning system started")
            return True

        except Exception as e:
            print(f"Failed to start auto-learning: {e}")
            return False

    def create_vr_test_data(self):
        """Create test VR data to verify system works"""
        print("Creating test VR data...")

        test_data = {
            "event_type": "movement",
            "headset": "Meta Quest 3",
            "position": {
                "x": 1.5,
                "y": 1.2,
                "z": -2.0
            },
            "rotation": {
                "x": 15.0,
                "y": 45.0,
                "z": 0.0
            },
            "controllers": {
                "left": {
                    "position": {"x": -0.5, "y": 1.0, "z": -1.0},
                    "trigger": 0.8,
                    "grip": 0.6
                },
                "right": {
                    "position": {"x": 0.5, "y": 1.0, "z": -1.0},
                    "trigger": 0.3,
                    "grip": 0.9
                }
            },
            "timestamp": time.time()
        }

        # Save test data
        with open("test_vr_data.json", 'w') as f:
            json.dump(test_data, f, indent=2)

        print("Test VR data created: test_vr_data.json")
        return "test_vr_data.json"

    def show_status(self):
        """Show current system status"""
        print("\n" + "="*50)
        print("OMNI VR Learning Platform Status")
        print("="*50)

        # Check learning summary
        if os.path.exists("learn_summary.json"):
            with open("learn_summary.json", 'r') as f:
                summary = json.load(f)

            print(f"Learning Cycles: {summary.get('runs', 0)}")
            print(f"Records Processed: {summary.get('total_records', 0)}")
            print(f"Last Run: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(summary.get('last_run', 0)))}")

        # Show VR files
        vr_files = [f for f in os.listdir('.') if 'vr' in f.lower()]
        print(f"VR Integration Files: {len(vr_files)}")

        # Show recent logs
        log_files = [f for f in os.listdir('.') if f.endswith('.log')]
        print(f"Log Files: {len(log_files)}")

        print("="*50)

    def start_complete_system(self):
        """Start the complete VR learning system"""
        print("Starting OMNI VR Learning Platform...")
        print("="*50)

        if not self.check_prerequisites():
            return False

        self.running = True

        # Start all components
        vr_ok = self.start_vr_listener()
        gcs_ok = self.start_gcs_uploader()
        learning_ok = self.start_auto_learning()

        if not (vr_ok and gcs_ok and learning_ok):
            print("Some components failed to start")
            return False

        print("\nAll systems started successfully!")
        self.show_status()

        print("\nNext steps:")
        print("1. Connect Meta Quest 3 to same network")
        print("2. Use SideQuest/Oculus Developer Hub to send VR data")
        print("3. Or run: python simulate_vr_headset.py")
        print("4. Watch learning progress in learn_summary.json")
        print("5. Check GCS uploads: gsutil ls gs://omni-meta-data/models/")

        return True

    def stop_system(self):
        """Stop all systems"""
        print("Stopping OMNI VR Learning Platform...")
        self.running = False
        print("All systems stopped")

def main():
    """Main launcher function"""
    print("OMNI VR Learning Launcher")
    print("="*50)

    launcher = OmniVRLearningLauncher()

    print("Choose an option:")
    print("1. Start complete VR learning system")
    print("2. Start VR listener only")
    print("3. Start GCS uploader only")
    print("4. Create test VR data")
    print("5. Show current status")
    print("6. Exit")

    choice = input("Enter choice (1-6): ").strip()

    if choice == "1":
        if launcher.start_complete_system():
            print("\nSystem running! Press Ctrl+C to stop...")
            try:
                while True:
                    time.sleep(10)
                    launcher.show_status()
            except KeyboardInterrupt:
                print("Stopping system...")
                launcher.stop_system()

    elif choice == "2":
        if launcher.start_vr_listener():
            print("VR listener running. Press Ctrl+C to stop...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                launcher.stop_system()

    elif choice == "3":
        if launcher.start_gcs_uploader():
            print("GCS uploader running. Press Ctrl+C to stop...")
            try:
                while True:
                    time.sleep(10)
            except KeyboardInterrupt:
                launcher.stop_system()

    elif choice == "4":
        test_file = launcher.create_vr_test_data()
        print(f"Test file created: {test_file}")
        print("You can manually send this to the VR connector for testing")

    elif choice == "5":
        launcher.show_status()

    else:
        print("Exiting...")

if __name__ == "__main__":
    main()