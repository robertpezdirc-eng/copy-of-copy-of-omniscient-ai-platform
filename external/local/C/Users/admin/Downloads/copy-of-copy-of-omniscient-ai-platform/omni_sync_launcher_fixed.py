#!/usr/bin/env python3
"""
OMNI Sync Core Launcher
Integrated launcher for the complete device discovery system

Author: OMNI Platform
Version: 1.0.0
"""

import time
import threading
import json
from datetime import datetime

# Import our modules
from omni_sync_core import initialize_sync_core, get_sync_core, get_discovered_devices, start_device_discovery, stop_device_discovery, get_discovery_stats
from omni_device_manager import initialize_device_manager, get_device_manager, get_devices, get_device_stats
from omni_sync_dashboard_server import initialize_dashboard_server, start_dashboard_server, stop_dashboard_server

class OmniSyncLauncher:
    """Integrated launcher for OMNI Sync Core system"""

    def __init__(self):
        self.components = {
            'sync_core': {'initialized': False, 'started': False},
            'device_manager': {'initialized': False, 'started': False},
            'dashboard_server': {'initialized': False, 'started': False}
        }

        self.running = False
        self.monitor_thread = None

        print("OMNI Sync Core Launcher initialized")

    def initialize_all(self):
        """Initialize all components"""
        print("Initializing OMNI Sync Core components...")

        try:
            # Initialize Sync Core
            print("  Initializing Omni Sync Core...")
            sync_core = initialize_sync_core({
                'scan_interval': 15,  # Faster scanning for demo
                'device_timeout': 60,
                'enable_mdns': True,
                'enable_ble': True,
                'enable_wifi_scan': True
            })
            self.components['sync_core']['initialized'] = True
            print("    Sync Core initialized")

            # Initialize Device Manager
            print("  Initializing Device Manager...")
            device_manager = initialize_device_manager()
            self.components['device_manager']['initialized'] = True
            print("    Device Manager initialized")

            # Initialize Dashboard Server
            print("  Initializing Dashboard Server...")
            dashboard_server = initialize_dashboard_server('0.0.0.0', 3080)
            self.components['dashboard_server']['initialized'] = True
            print("    Dashboard Server initialized")

            print("All components initialized successfully!")

        except Exception as e:
            print(f"Error initializing components: {e}")
            raise

    def start_all(self):
        """Start all components"""
        if not all(comp['initialized'] for comp in self.components.values()):
            print("Not all components initialized. Initializing first...")
            self.initialize_all()

        print("Starting OMNI Sync Core system...")

        try:
            # Start Device Manager first (handles device events)
            print("  Starting Device Manager...")
            device_manager = get_device_manager()
            device_manager.start()
            self.components['device_manager']['started'] = True
            print("    Device Manager started")

            # Start Sync Core (discovers devices)
            print("  Starting Sync Core...")
            sync_core = get_sync_core()
            sync_core.start()
            self.components['sync_core']['started'] = True
            print("    Sync Core started")

            # Start Dashboard Server last (serves the UI)
            print("  Starting Dashboard Server...")
            start_dashboard_server()
            self.components['dashboard_server']['started'] = True
            print("    Dashboard Server started")

            self.running = True

            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self._monitor_system, daemon=True)
            self.monitor_thread.start()

            print("OMNI Sync Core system started successfully!")
            print("Access the dashboard at: http://localhost:3080")
            print("Device discovery is now active")

        except Exception as e:
            print(f"Error starting system: {e}")
            raise

    def stop_all(self):
        """Stop all components"""
        if not self.running:
            return

        print("Stopping OMNI Sync Core system...")

        self.running = False

        try:
            # Stop in reverse order
            if self.components['dashboard_server']['started']:
                print("  Stopping Dashboard Server...")
                stop_dashboard_server()
                self.components['dashboard_server']['started'] = False
                print("    Dashboard Server stopped")

            if self.components['sync_core']['started']:
                print("  Stopping Sync Core...")
                sync_core = get_sync_core()
                if sync_core:
                    sync_core.stop()
                self.components['sync_core']['started'] = False
                print("    Sync Core stopped")

            if self.components['device_manager']['started']:
                print("  Stopping Device Manager...")
                device_manager = get_device_manager()
                if device_manager:
                    device_manager.stop()
                self.components['device_manager']['started'] = False
                print("    Device Manager stopped")

            print("All components stopped successfully!")

        except Exception as e:
            print(f"Error stopping system: {e}")

    def _monitor_system(self):
        """Monitor system status and print periodic updates"""
        last_device_count = 0
        last_scan_cycle = 0

        while self.running:
            try:
                # Get current stats
                sync_stats = get_discovery_stats()
                device_stats = get_device_stats()

                current_devices = len(get_devices())
                current_scan_cycles = sync_stats.get('scan_cycles', 0)

                # Print updates if there are changes
                if (current_devices != last_device_count or
                    current_scan_cycles != last_scan_cycle or
                    int(time.time()) % 30 == 0):  # Every 30 seconds

                    print("\nSystem Status:")
                    print(f"  Scan Cycles: {current_scan_cycles}")
                    print(f"  Total Devices: {current_devices}")
                    print(f"  Connected Devices: {device_stats.get('connected_devices', 0)}")
                    print(f"  Active Connections: {device_stats.get('active_connections', 0)}")

                    if current_devices > 0:
                        print("  Recent Devices:")
                        devices = get_devices()
                        for device in devices[-3:]:  # Show last 3 devices
                            print(f"    {device['device_name']} ({device['device_type']}) - {device['connection_status']}")

                    last_device_count = current_devices
                    last_scan_cycle = current_scan_cycles

                time.sleep(5)  # Check every 5 seconds

            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(10)

    def get_system_status(self):
        """Get comprehensive system status"""
        try:
            sync_stats = get_discovery_stats()
            device_stats = get_device_stats()
            devices = get_devices()

            return {
                'system': {
                    'running': self.running,
                    'components': self.components,
                    'timestamp': datetime.now().isoformat()
                },
                'sync_core': sync_stats,
                'device_manager': device_stats,
                'devices': {
                    'total': len(devices),
                    'connected': len([d for d in devices if d['connection_status'] == 'connected']),
                    'recent': devices[-5:] if devices else []  # Last 5 devices
                }
            }
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Global launcher instance
omni_sync_launcher = None

def initialize_launcher():
    """Initialize the launcher"""
    global omni_sync_launcher
    omni_sync_launcher = OmniSyncLauncher()
    return omni_sync_launcher

def get_launcher():
    """Get the global launcher instance"""
    return omni_sync_launcher

def start_omni_sync():
    """Start the complete OMNI Sync system"""
    launcher = initialize_launcher()
    launcher.initialize_all()
    launcher.start_all()
    return launcher

def stop_omni_sync():
    """Stop the complete OMNI Sync system"""
    if omni_sync_launcher:
        omni_sync_launcher.stop_all()

def get_system_status():
    """Get system status"""
    if omni_sync_launcher:
        return omni_sync_launcher.get_system_status()
    return {'error': 'Launcher not initialized'}

# Demo functions
def demo_device_discovery(duration=60):
    """Demo the device discovery system"""
    print(f"Starting OMNI Sync Core demo for {duration} seconds...")

    # Start the system
    launcher = start_omni_sync()

    print("Demo running... Press Ctrl+C to stop early")

    try:
        # Run for specified duration
        start_time = time.time()
        while time.time() - start_time < duration:
            time.sleep(1)

        print(f"\nDemo completed after {duration} seconds")

    except KeyboardInterrupt:
        print("\nDemo interrupted by user")

    # Show final results
    status = get_system_status()
    if 'error' not in status:
        print("\nFinal Results:")
        print(f"  Total Scan Cycles: {status['sync_core'].get('scan_cycles', 0)}")
        print(f"  Devices Discovered: {status['devices']['total']}")
        print(f"  Devices Connected: {status['devices']['connected']}")

        if status['devices']['recent']:
            print("  Recently Discovered Devices:")
            for device in status['devices']['recent']:
                print(f"    {device['device_name']} ({device['device_type']}) via {device['discovery_method']}")

    # Stop the system
    stop_omni_sync()
    print("Demo completed!")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "demo":
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            demo_device_discovery(duration)
        elif sys.argv[1] == "start":
            launcher = start_omni_sync()

            print("System running... Press Ctrl+C to stop")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping system...")
                stop_omni_sync()
                print("System stopped!")
        else:
            print("Usage: python omni_sync_launcher.py [demo|start] [duration]")
            print("  demo [duration] - Run demo for specified seconds (default 60)")
            print("  start - Start system and keep running until Ctrl+C")
    else:
        # Just show status if no arguments
        print("OMNI Sync Core Launcher")
        print("Usage: python omni_sync_launcher.py [demo|start] [duration]")
        print()
        print("Commands:")
        print("  demo [duration] - Run demo for specified seconds (default 60)")
        print("  start - Start system and keep running until Ctrl+C")
        print()
        print("The system will automatically discover devices using:")
        print("  mDNS (Multicast DNS)")
        print("  BLE (Bluetooth Low Energy)")
        print("  Wi-Fi Network Scanning")
        print()
        print("Access the dashboard at: http://localhost:3080")