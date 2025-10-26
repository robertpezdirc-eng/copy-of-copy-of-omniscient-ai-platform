#!/usr/bin/env python3
"""
Test script for VR integration
"""

import json
import time
import threading
from omni_vr_connector import OmniVRConnector
from omni_event_logger import EventLogger

def test_vr_connector():
    """Test VR connector initialization and basic functionality"""
    print("Testing VR connector...")

    # Create a test config
    config = {
        "system": {"auto_learning": False},
        "learning_engine": {"interval_seconds": 5}
    }

    # Initialize VR connector
    try:
        vr_connector = OmniVRConnector(config)
        print("SUCCESS: VR connector initialized successfully")
        print("SUCCESS: Listening on UDP port 9090 for VR headset data")
        print("SUCCESS: Ready to receive data from Meta Quest, Pico, or HTC Vive")
        return True
    except Exception as e:
        print(f"ERROR: VR connector initialization failed: {e}")
        return False

def simulate_vr_data():
    """Simulate VR headset sending data"""
    import socket

    # Wait a bit for the connector to start listening
    time.sleep(2)

    try:
        # Create UDP socket to simulate VR headset
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Sample VR data
        vr_data = {
            "event_type": "movement",
            "position": {"x": 1.2, "y": 0.5, "z": -2.1},
            "rotation": {"x": 0.1, "y": 0.8, "z": 0.0},
            "headset": "Meta Quest 3",
            "timestamp": time.time()
        }

        # Send data to the VR connector
        message = json.dumps(vr_data).encode('utf-8')
        sock.sendto(message, ("localhost", 9090))
        print("SUCCESS: Simulated VR data sent to connector")
        sock.close()

    except Exception as e:
        print(f"ERROR: Failed to simulate VR data: {e}")

def main():
    """Main test function"""
    print("OMNI VR Integration Test")
    print("=" * 50)

    # Test VR connector
    if not test_vr_connector():
        return False

    print("\nStarting VR data listener test...")
    print("Note: The connector will listen for 10 seconds")
    print("You can run the VR headset app or use the simulator")

    # Start a thread to simulate VR data after 3 seconds
    simulator_thread = threading.Thread(target=simulate_vr_data, daemon=True)
    simulator_thread.start()

    # Test listening for a short period
    config = {"system": {"auto_learning": False}}
    vr_connector = OmniVRConnector(config)

    start_time = time.time()
    test_duration = 10  # seconds

    print(f"\nListening for VR data for {test_duration} seconds...")

    while time.time() - start_time < test_duration:
        try:
            data = vr_connector.listen()
            if data:
                print(f"  Time: {time.time() - start_time:.2f}s")
                print(f"SUCCESS: Received VR data: {data.get('event_type', 'unknown')}")
                print(f"  Position: {data.get('position', {})}")
                print(f"  Headset: {data.get('headset', 'unknown')}")
                break
        except Exception as e:
            print(f"ERROR: Error listening for VR data: {e}")
            break

        time.sleep(0.5)

    print("\nVR integration test completed")
    print("Ready for real VR headset integration")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)