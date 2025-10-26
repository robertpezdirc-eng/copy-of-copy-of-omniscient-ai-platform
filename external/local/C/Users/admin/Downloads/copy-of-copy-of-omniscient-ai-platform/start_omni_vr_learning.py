#!/usr/bin/env python3
"""
START OMNI VR LEARNING - Complete VR Integration Startup Script
Follow these exact steps to begin OMNI's VR learning journey
"""

import os
import json
import time
import subprocess
from pathlib import Path
from omni_event_logger import EventLogger

def main():
    """Complete VR learning startup guide"""
    print("🚀 OMNI VR Learning Platform - Startup Guide")
    print("=" * 60)

    logger = EventLogger()

    # Step 1: Check current status
    print("\n📊 STEP 1: Current Platform Status")
    print("-" * 40)

    if os.path.exists("learn_summary.json"):
        with open("learn_summary.json", 'r') as f:
            summary = json.load(f)

        print(f"Learning Cycles Completed: {summary.get('runs', 0)}")
        print(f"Records Processed: {summary.get('total_records', 0)}")
        print(f"Last Activity: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(summary.get('last_run', 0)))}")

        if summary.get('total_records', 0) == 0:
            print("Status: WAITING FOR VR DATA")
        else:
            print("Status: LEARNING FROM VR DATA")
    else:
        print("No learning summary found - system ready for first run")

    # Step 2: Check VR integration
    print("\n🕶️ STEP 2: VR Integration Check")
    print("-" * 40)

    vr_files = [f for f in os.listdir('.') if 'vr' in f.lower()]
    print(f"VR Integration Files: {len(vr_files)} found")

    key_files = [
        "omni_vr_connector.py",
        "omni_vr_starter.py",
        "simulate_vr_headset.py"
    ]

    for file in key_files:
        if os.path.exists(file):
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} - MISSING")

    # Step 3: Start VR listener
    print("\n🎯 STEP 3: Start VR Data Collection")
    print("-" * 40)

    print("Choose how to provide VR data:")
    print("1. Connect real VR headset (Meta Quest 3)")
    print("2. Use VR simulation for testing")
    print("3. Skip VR for now")

    choice = input("Enter choice (1-3): ").strip()

    if choice in ["1", "2"]:
        print("\nStarting VR listener on port 9090...")

        try:
            from omni_vr_connector import OmniVRConnector
            vr_connector = OmniVRConnector({})

            print("✓ VR listener started")
            print("✓ Listening for UDP data on port 9090")
            print("✓ Ready for Meta Quest 3, Pico, or HTC Vive data")

            if choice == "2":
                print("\nTo test with simulation, run in another terminal:")
                print("python simulate_vr_headset.py")

        except Exception as e:
            print(f"✗ Failed to start VR listener: {e}")
            return

    # Step 4: Show next steps
    print("\n📋 STEP 4: Next Steps")
    print("-" * 40)

    print("Your OMNI platform is now ready!")
    print("\nImmediate actions:")
    print("1. Keep this terminal running (VR listener)")
    print("2. Connect VR headset to same network")
    print("3. Use SideQuest/Oculus Developer Hub to send VR data")
    print("4. Watch learn_summary.json for record increases")

    print("\nMonitoring commands:")
    print("- Check learning progress: cat learn_summary.json")
    print("- View VR logs: tail -f omni_vr_manager.log")
    print("- Check GCS uploads: gsutil ls gs://omni-meta-data/models/")

    print("\nVR Headset Setup:")
    print("- Meta Quest 3: Enable developer mode in Oculus app")
    print("- Network: Ensure headset and platform on same WiFi")
    print("- Data sending: Use UDP to platform IP on port 9090")

    print("\nExpected Results:")
    print("- Records count in learn_summary.json will increase")
    print("- VR movement data will be logged")
    print("- Learning summaries will upload to Google Cloud")
    print("- Dashboard will be generated automatically")

    # Step 5: Keep running and monitoring
    print("\n🔄 STEP 5: Monitoring")
    print("-" * 40)

    try:
        print("Monitoring for VR data... (Press Ctrl+C to stop)")
        last_records = 0

        while True:
            time.sleep(10)  # Check every 10 seconds

            if os.path.exists("learn_summary.json"):
                with open("learn_summary.json", 'r') as f:
                    summary = json.load(f)

                current_records = summary.get('total_records', 0)

                if current_records > last_records:
                    print(f"🎉 LEARNING PROGRESS: {current_records} records processed!")
                    print(f"   Cycles: {summary.get('runs', 0)}")
                    last_records = current_records

                elif last_records == 0:
                    print("⏳ Waiting for VR data... Send some VR movements!")

    except KeyboardInterrupt:
        print("\n🛑 VR Learning monitoring stopped")
        print("OMNI platform is still running in the background")

    print("\n✅ OMNI VR Learning session completed!")
    print("Check learn_summary.json for final results")

if __name__ == "__main__":
    main()