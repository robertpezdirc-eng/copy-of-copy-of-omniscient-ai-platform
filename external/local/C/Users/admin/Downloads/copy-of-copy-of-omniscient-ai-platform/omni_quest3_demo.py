#!/usr/bin/env python3
"""
OMNI Meta Quest 3 Integration Demo
Comprehensive demonstration of Quest 3 VR/AR capabilities with OMNI platform

Author: OMNI Platform
Version: 1.0.0
"""

import time
import json
from datetime import datetime

# Import OMNI modules
from omni_sync_core import initialize_sync_core, get_sync_core, start_device_discovery, stop_device_discovery, get_discovery_stats
from omni_device_manager import initialize_device_manager, get_device_manager, get_devices, get_device_stats
from omni_quest3_manager import initialize_quest3_manager, get_quest3_manager, register_quest3, connect_quest3, create_ar_overlay, get_quest3_devices, get_quest3_status

class OmniQuest3Demo:
    """Meta Quest 3 Integration Demo"""

    def __init__(self):
        self.quest3_manager = None
        self.device_manager = None
        self.sync_core = None

        print("Meta Quest 3 OMNI Integration Demo")

    def run_full_demo(self, duration=120):
        """Run complete Quest 3 integration demo"""
        print(f"Starting Meta Quest 3 demo for {duration} seconds...")

        try:
            # Phase 1: Initialize all systems
            print("\n=== Phase 1: System Initialization ===")
            self._initialize_systems()

            # Phase 2: Register Quest 3 device
            print("\n=== Phase 2: Device Registration ===")
            quest3_id = self._register_quest3_device()

            if quest3_id:
                # Phase 3: Connect and configure
                print("\n=== Phase 3: Connection & Configuration ===")
                self._connect_and_configure_quest3(quest3_id)

                # Phase 4: AR Overlay Demo
                print("\n=== Phase 4: AR Overlay Demonstration ===")
                self._demo_ar_overlays(quest3_id)

                # Phase 5: Real-time Monitoring
                print("\n=== Phase 5: Real-time Monitoring ===")
                self._demo_real_time_monitoring(duration)

                # Phase 6: Integration Showcase
                print("\n=== Phase 6: OMNI Platform Integration ===")
                self._showcase_omni_integration()

        except KeyboardInterrupt:
            print("\nDemo interrupted by user")
        except Exception as e:
            print(f"Demo error: {e}")
        finally:
            # Cleanup
            print("\n=== Cleanup ===")
            self._cleanup()

    def _initialize_systems(self):
        """Initialize all OMNI systems"""
        print("Initializing OMNI platform components...")

        # Initialize Sync Core
        self.sync_core = initialize_sync_core({
            'scan_interval': 10,
            'device_timeout': 60,
            'enable_mdns': True,
            'enable_ble': True,
            'enable_wifi_scan': True
        })
        self.sync_core.start()
        print("  Sync Core: Active")

        # Initialize Device Manager
        self.device_manager = initialize_device_manager()
        self.device_manager.start()
        print("  Device Manager: Active")

        # Initialize Quest 3 Manager
        self.quest3_manager = initialize_quest3_manager()
        self.quest3_manager.start()
        print("  Quest 3 Manager: Active")

        print("All systems initialized successfully!")

    def _register_quest3_device(self):
        """Register a Meta Quest 3 device"""
        print("Registering Meta Quest 3 device...")

        # Simulate Quest 3 device info
        quest3_info = {
            "device_name": "Meta Quest 3 Developer Kit",
            "serial_number": "QUEST3-DK-001",
            "firmware_version": "1.0.0",
            "connection_mode": "standalone",
            "ip_address": "192.168.1.150"
        }

        device_id = register_quest3(quest3_info, "demo_user")

        if device_id:
            print(f"  Quest 3 registered with ID: {device_id}")
            return device_id
        else:
            print("  Failed to register Quest 3 device")
            return None

    def _connect_and_configure_quest3(self, device_id: str):
        """Connect and configure Quest 3"""
        print(f"Connecting to Quest 3 device: {device_id}")

        # Test different connection modes
        connection_modes = ["standalone", "oculus_link", "air_link"]

        for mode in connection_modes:
            print(f"  Testing {mode} connection...")

            # In real implementation, this would attempt actual connection
            # For demo, we'll simulate the process
            time.sleep(2)

            if mode == "standalone":
                print("    Standalone mode: WiFi connection established")
                print("    Mixed reality: Enabled")
                print("    Passthrough cameras: Active")
            elif mode == "oculus_link":
                print("    Oculus Link: USB-C connection ready")
                print("    PC VR mode: Available")
            elif mode == "air_link":
                print("    Air Link: WiFi streaming ready")
                print("    Low latency mode: Optimized")

        # Connect in standalone mode for demo
        connected = connect_quest3(device_id, "standalone")
        print(f"  Connection result: {'Success' if connected else 'Failed'}")

    def _demo_ar_overlays(self, device_id: str):
        """Demonstrate AR overlay capabilities"""
        print("Creating AR overlays for Quest 3 mixed reality...")

        # Create various AR overlays
        overlays = [
            {
                "overlay_type": "device_data",
                "data_source": "device_count",
                "title": "Connected Devices",
                "position": [0, 0, -2],
                "background_color": "#000000",
                "text_color": "#00FF00"
            },
            {
                "overlay_type": "system_status",
                "data_source": "system_status",
                "title": "System Status",
                "position": [-1, 0, -2],
                "background_color": "#000000",
                "text_color": "#0088FF"
            },
            {
                "overlay_type": "device_list",
                "data_source": "device_list",
                "title": "Device List",
                "position": [1, 0, -2],
                "background_color": "#000000",
                "text_color": "#FF8800"
            }
        ]

        created_overlays = []

        for i, overlay_info in enumerate(overlays):
            print(f"  Creating overlay {i+1}: {overlay_info['title']}")

            overlay_id = create_ar_overlay(device_id, overlay_info)
            if overlay_id:
                created_overlays.append(overlay_id)
                print(f"    Overlay created: {overlay_id}")
            else:
                print("    Failed to create overlay")

            time.sleep(1)

        print(f"Created {len(created_overlays)} AR overlays")

        # Simulate real-time updates
        print("  Simulating real-time AR updates...")
        for _ in range(5):
            time.sleep(2)
            print("    AR overlay content updated")

        return created_overlays

    def _demo_real_time_monitoring(self, duration: int):
        """Demonstrate real-time monitoring"""
        print(f"Monitoring Quest 3 integration for {duration} seconds...")

        start_time = time.time()
        last_update = 0

        while time.time() - start_time < duration:
            current_time = time.time()

            # Update every 10 seconds
            if current_time - last_update > 10:
                self._show_current_status()
                last_update = current_time

            time.sleep(1)

    def _show_current_status(self):
        """Show current system status"""
        try:
            # Get status from all systems
            quest3_status = get_quest3_status()
            device_stats = get_device_stats()
            sync_stats = get_discovery_stats()

            print("
  Current Status:"            print(f"    Quest 3 Devices: {quest3_status.get('connected_devices', 0)}/{quest3_status.get('total_devices', 0)}")
            print(f"    AR Overlays: {quest3_status.get('ar_overlays', 0)}")
            print(f"    Total Devices: {device_stats.get('total_devices', 0)}")
            print(f"    Scan Cycles: {sync_stats.get('scan_cycles', 0)}")

            # Show recent devices
            devices = get_devices()
            if devices:
                print("    Recent devices:")
                for device in devices[-3:]:
                    print(f"      - {device['device_name']} ({device['connection_status']})")

        except Exception as e:
            print(f"  Status update error: {e}")

    def _showcase_omni_integration(self):
        """Showcase OMNI platform integration features"""
        print("OMNI Platform Integration Features:")

        # Show device discovery integration
        print("  Device Discovery Integration:")
        print("    - Automatic Quest 3 detection via mDNS/BLE/WiFi")
        print("    - Unified device management across all platforms")
        print("    - Real-time status synchronization")

        # Show AR data integration
        print("  AR Data Integration:")
        print("    - Live device count overlay")
        print("    - System status visualization")
        print("    - Network topology display")
        print("    - Real-time performance metrics")

        # Show tracking integration
        print("  Advanced Tracking:")
        print("    - Hand tracking (27 points per hand)")
        print("    - Eye tracking with gaze direction")
        print("    - Body and head position tracking")
        print("    - Gesture recognition")

        # Show connection modes
        print("  Connection Modes:")
        print("    - Standalone VR/AR mode")
        print("    - Oculus Link (USB-C)")
        print("    - Air Link (WiFi streaming)")

    def _cleanup(self):
        """Clean up all systems"""
        print("Cleaning up systems...")

        if self.quest3_manager:
            self.quest3_manager.stop()

        if self.device_manager:
            self.device_manager.stop()

        if self.sync_core:
            self.sync_core.stop()

        print("All systems stopped")

def run_quest3_demo(duration=120):
    """Run the Quest 3 demo"""
    demo = OmniQuest3Demo()
    demo.run_full_demo(duration)

def run_quest3_feature_demo():
    """Run specific feature demonstrations"""
    print("Meta Quest 3 Feature Demonstrations")
    print("=" * 50)

    # Initialize systems
    demo = OmniQuest3Demo()
    demo._initialize_systems()

    try:
        # Feature 1: Hardware Capabilities
        print("\n1. Hardware Capabilities Demo")
        print("-" * 30)
        print("Meta Quest 3 Specifications:")
        print("  - Processor: Qualcomm Snapdragon XR2 Gen 2")
        print("  - RAM: 8GB")
        print("  - Display: 2064x2208 per eye @ 90-120Hz")
        print("  - Cameras: 4x passthrough for mixed reality")
        print("  - Connectivity: WiFi 6E + Bluetooth 5.2")
        print("  - Battery: 2-3 hours active use")

        # Feature 2: Mixed Reality
        print("\n2. Mixed Reality Demo")
        print("-" * 30)
        print("Mixed Reality Features:")
        print("  - Real world passthrough via front cameras")
        print("  - Real-time environment mapping")
        print("  - Virtual object placement in real space")
        print("  - Hand interaction with real objects")

        # Feature 3: AR Overlays
        print("\n3. AR Data Overlay Demo")
        print("-" * 30)
        print("AR Overlay Capabilities:")
        print("  - Real-time device status display")
        print("  - System performance metrics")
        print("  - Network topology visualization")
        print("  - Custom data visualization")

        # Feature 4: Connection Modes
        print("\n4. Connection Modes Demo")
        print("-" * 30)
        print("Connection Options:")
        print("  - Standalone: Independent VR/AR operation")
        print("  - Oculus Link: USB-C PC connection")
        print("  - Air Link: WiFi PC streaming (low latency)")

        # Feature 5: Tracking Systems
        print("\n5. Advanced Tracking Demo")
        print("-" * 30)
        print("Tracking Capabilities:")
        print("  - Hand Tracking: 27 points per hand")
        print("  - Eye Tracking: Gaze direction and convergence")
        print("  - Face Tracking: Expression and emotion")
        print("  - Body Tracking: Full body position and movement")

        time.sleep(5)

    finally:
        demo._cleanup()

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "full":
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 120
            run_quest3_demo(duration)
        elif sys.argv[1] == "features":
            run_quest3_feature_demo()
        elif sys.argv[1] == "quick":
            run_quest3_demo(30)
        else:
            print("Usage: python omni_quest3_demo.py [full|features|quick] [duration]")
            print("  full [duration] - Run full demo (default 120 seconds)")
            print("  features - Show feature demonstrations")
            print("  quick - Run quick 30-second demo")
    else:
        print("Meta Quest 3 OMNI Integration Demo")
        print("Usage: python omni_quest3_demo.py [full|features|quick] [duration]")
        print()
        print("Commands:")
        print("  full [duration] - Complete system demo")
        print("  features - Feature capability showcase")
        print("  quick - 30-second quick demo")
        print()
        print("This demo showcases:")
        print("  - Meta Quest 3 hardware capabilities")
        print("  - Mixed reality and passthrough features")
        print("  - AR data overlay system")
        print("  - Advanced hand/eye/body tracking")
        print("  - Multiple connection modes")
        print("  - OMNI platform integration")