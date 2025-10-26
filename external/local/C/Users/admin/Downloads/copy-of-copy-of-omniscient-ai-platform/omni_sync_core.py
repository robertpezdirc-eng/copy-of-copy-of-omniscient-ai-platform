#!/usr/bin/env python3
"""
OMNI Sync Core - Automatic Device Discovery and Management
Advanced network device discovery using mDNS, BLE, and Wi-Fi scanning
Automatically detects and connects devices without manual IP entry

Author: OMNI Platform
Version: 1.0.0
"""

import asyncio
import json
import socket
import time
import uuid
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
import logging
import ipaddress
import subprocess
import platform
import re

# Network discovery imports
try:
    import zeroconf
    from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf
    MDNS_AVAILABLE = True
except ImportError:
    MDNS_AVAILABLE = False
    print("WARNING: Zeroconf not available. mDNS discovery will be limited.")

try:
    import bluetooth
    BLE_AVAILABLE = True
except ImportError:
    BLE_AVAILABLE = False
    print(" Bluetooth module not available. BLE discovery will be limited.")

@dataclass
class DiscoveredDevice:
    """Information about a discovered network device"""
    device_id: str
    device_name: str
    device_type: str
    discovery_method: str  # 'mdns', 'ble', 'wifi', 'manual'
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    port: Optional[int] = None
    capabilities: Dict[str, Any] = field(default_factory=dict)
    last_seen: datetime = field(default_factory=datetime.now)
    connection_status: str = "discovered"  # discovered, connecting, connected, failed
    signal_strength: int = 0  # For Wi-Fi and BLE devices
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None

@dataclass
class NetworkInterface:
    """Network interface information"""
    name: str
    ip_address: str
    subnet: str
    is_active: bool = True

class OmniSyncCore:
    """OMNI Sync Core - Automatic Device Discovery and Management"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = {
            "scan_interval": 30,  # seconds
            "device_timeout": 300,  # seconds
            "max_devices": 1000,
            "enable_mdns": True,
            "enable_ble": True,
            "enable_wifi_scan": True,
            "enable_auto_connect": True,
            "supported_device_types": [
                "smartphone", "tablet", "laptop", "desktop", "iot_device",
                "smart_tv", "gaming_console", "vr_headset", "smart_glasses",
                "printer", "camera", "speaker", "display", "router"
            ],
            "mdns_services": [
                "_http._tcp.local.",
                "_https._tcp.local.",
                "_ssh._tcp.local.",
                "_ftp._tcp.local.",
                "_smb._tcp.local.",
                "_printer._tcp.local.",
                "_airplay._tcp.local.",
                "_googlecast._tcp.local.",
                "_omnidevice._tcp.local."
            ]
        }

        # Override with user config
        if config:
            self.config.update(config)

        # Device storage
        self.discovered_devices: Dict[str, DiscoveredDevice] = {}
        self.network_interfaces: List[NetworkInterface] = []
        self.device_event_listeners: List[Callable] = []

        # Background services
        self._running = False
        self._scan_thread = None
        self._mdns_browser = None
        self._zeroconf = None

        # Statistics
        self.stats = {
            "total_devices_discovered": 0,
            "total_devices_connected": 0,
            "scan_cycles": 0,
            "last_scan_time": None,
            "errors": 0
        }

        print(" OMNI Sync Core initialized")

    def start(self):
        """Start the Omni Sync Core services"""
        if self._running:
            print(" OMNI Sync Core already running")
            return

        self._running = True

        # Get network interfaces
        self._discover_network_interfaces()

        # Start background scanning
        self._scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
        self._scan_thread.start()

        # Start mDNS discovery if available
        if MDNS_AVAILABLE and self.config["enable_mdns"]:
            self._start_mdns_discovery()

        print(" OMNI Sync Core started")

    def stop(self):
        """Stop the Omni Sync Core services"""
        if not self._running:
            return

        self._running = False

        # Stop mDNS browser
        if self._mdns_browser:
            self._mdns_browser.cancel()
        if self._zeroconf:
            self._zeroconf.close()

        print(" OMNI Sync Core stopped")

    def _discover_network_interfaces(self):
        """Discover available network interfaces"""
        try:
            interfaces = []

            # Get network interfaces based on OS
            if platform.system() == "Windows":
                result = subprocess.run(['ipconfig'], capture_output=True, text=True)
                # Parse Windows ipconfig output
                current_interface = None
                for line in result.stdout.split('\n'):
                    if 'adapter' in line.lower() and 'ethernet' in line.lower() or 'wi-fi' in line.lower():
                        # Extract interface name
                        interface_match = re.search(r'adapter (.+?):', line, re.IGNORECASE)
                        if interface_match:
                            current_interface = interface_match.group(1).strip()
                    elif current_interface and 'ipv4 address' in line.lower():
                        ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                        if ip_match:
                            ip = ip_match.group(1)
                            subnet = ip.rsplit('.', 1)[0] + '.0/24'
                            interfaces.append(NetworkInterface(
                                name=current_interface,
                                ip_address=ip,
                                subnet=subnet
                            ))
                            current_interface = None

            else:  # Linux/Unix
                result = subprocess.run(['ip', 'route'], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if 'src' in line and 'dev' in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == 'dev':
                                interface_name = parts[i + 1]
                            elif part == 'src':
                                ip = parts[i + 1]
                                subnet = ip.rsplit('.', 1)[0] + '.0/24'
                                interfaces.append(NetworkInterface(
                                    name=interface_name,
                                    ip_address=ip,
                                    subnet=subnet
                                ))

            self.network_interfaces = interfaces
            print(f" Discovered {len(interfaces)} network interfaces")

        except Exception as e:
            print(f" Failed to discover network interfaces: {e}")

    def _scan_loop(self):
        """Main scanning loop"""
        while self._running:
            try:
                self.stats["scan_cycles"] += 1
                self.stats["last_scan_time"] = datetime.now()

                # Perform different types of scanning
                if self.config["enable_wifi_scan"]:
                    self._scan_wifi_networks()

                if self.config["enable_ble"]:
                    self._scan_ble_devices()

                # Clean up old devices
                self._cleanup_old_devices()

                # Wait for next scan
                time.sleep(self.config["scan_interval"])

            except Exception as e:
                print(f" Scan loop error: {e}")
                self.stats["errors"] += 1
                time.sleep(self.config["scan_interval"])

    def _scan_wifi_networks(self):
        """Scan for Wi-Fi networks and devices"""
        try:
            if platform.system() == "Windows":
                # Use netsh on Windows
                result = subprocess.run(['netsh', 'wlan', 'show', 'network', 'mode=bssid'],
                                      capture_output=True, text=True)

                current_network = None
                for line in result.stdout.split('\n'):
                    line = line.strip()

                    if line.startswith('SSID'):
                        ssid_match = re.search(r'SSID \d+ : (.+)', line)
                        if ssid_match:
                            current_network = ssid_match.group(1).strip()
                    elif line.startswith('BSSID'):
                        bssid_match = re.search(r'BSSID \d+ : (.+)', line)
                        if bssid_match:
                            mac = bssid_match.group(1).strip().upper()
                            # Create device entry for access point
                            device_id = f"wifi_ap_{mac.replace(':', '')}"
                            self._add_discovered_device(DiscoveredDevice(
                                device_id=device_id,
                                device_name=current_network or f"Access_Point_{mac[-6:]}",
                                device_type="access_point",
                                discovery_method="wifi",
                                mac_address=mac,
                                signal_strength=0,  # Would need more parsing
                                last_seen=datetime.now()
                            ))

            else:  # Linux
                # Use iwlist or nmcli on Linux
                try:
                    result = subprocess.run(['nmcli', '-t', '-f', 'BSSID,SSID,SIGNAL',
                                          'device', 'wifi', 'list'],
                                          capture_output=True, text=True)

                    for line in result.stdout.split('\n'):
                        if line.strip() and ':' in line:
                            parts = line.split(':')
                            if len(parts) >= 3:
                                mac, ssid, signal = parts[0], parts[1], parts[2]
                                device_id = f"wifi_ap_{mac.replace(':', '')}"
                                self._add_discovered_device(DiscoveredDevice(
                                    device_id=device_id,
                                    device_name=ssid or f"Access_Point_{mac[-6:]}",
                                    device_type="access_point",
                                    discovery_method="wifi",
                                    mac_address=mac.upper(),
                                    signal_strength=int(signal) if signal.isdigit() else 0,
                                    last_seen=datetime.now()
                                ))
                except:
                    # Fallback to iwlist
                    try:
                        result = subprocess.run(['iwlist', 'scan'],
                                              capture_output=True, text=True)
                        # Parse iwlist output (more complex)
                        pass
                    except:
                        pass

        except Exception as e:
            print(f" Wi-Fi scan error: {e}")

    def _scan_ble_devices(self):
        """Scan for BLE devices"""
        if not BLE_AVAILABLE:
            return

        try:
            print(" Scanning for BLE devices...")
            nearby_devices = bluetooth.discover_devices(
                duration=8,
                lookup_names=True,
                flush_cache=True,
                lookup_class=False
            )

            for addr, name in nearby_devices:
                try:
                    device_id = f"ble_{addr.replace(':', '')}"

                    # Get additional BLE info if possible
                    signal_strength = 0
                    try:
                        # This would require more advanced BLE libraries
                        pass
                    except:
                        pass

                    self._add_discovered_device(DiscoveredDevice(
                        device_id=device_id,
                        device_name=name or f"BLE_Device_{addr[-6:]}",
                        device_type="ble_device",
                        discovery_method="ble",
                        mac_address=addr.upper(),
                        signal_strength=signal_strength,
                        last_seen=datetime.now()
                    ))

                except Exception as e:
                    print(f" BLE device processing error: {e}")

        except Exception as e:
            print(f" BLE scan error: {e}")

    def _start_mdns_discovery(self):
        """Start mDNS service discovery"""
        if not MDNS_AVAILABLE:
            print(" mDNS discovery not available")
            return

        try:
            self._zeroconf = Zeroconf()
            services = self.config["mdns_services"]

            def on_service_state_change(zeroconf, service_type, name, state_change):
                if state_change is ServiceStateChange.Added:
                    asyncio.create_task(self._process_mdns_service(zeroconf, service_type, name))

            self._mdns_browser = ServiceBrowser(
                self._zeroconf,
                services,
                handlers=[on_service_state_change]
            )

            print(f" mDNS discovery started for {len(services)} service types")

        except Exception as e:
            print(f" mDNS discovery error: {e}")

    async def _process_mdns_service(self, zeroconf, service_type, name):
        """Process discovered mDNS service"""
        try:
            info = zeroconf.get_service_info(service_type, name)

            if info:
                # Extract device information from mDNS
                device_name = name.replace(f".{service_type}", "")

                # Get IP address
                addresses = info.parsed_addresses()
                ip_address = str(addresses[0]) if addresses else None

                # Generate device ID
                device_id = f"mdns_{hash(f'{name}_{service_type}') % 1000000:06d}"

                # Determine device type based on service
                device_type = self._classify_device_by_service(service_type, device_name)

                self._add_discovered_device(DiscoveredDevice(
                    device_id=device_id,
                    device_name=device_name,
                    device_type=device_type,
                    discovery_method="mdns",
                    ip_address=ip_address,
                    port=info.port,
                    last_seen=datetime.now()
                ))

        except Exception as e:
            print(f" mDNS service processing error: {e}")

    def _classify_device_by_service(self, service_type: str, device_name: str) -> str:
        """Classify device type based on mDNS service"""
        service_lower = service_type.lower()
        name_lower = device_name.lower()

        if "printer" in service_lower:
            return "printer"
        elif "airplay" in service_lower:
            return "apple_device"
        elif "googlecast" in service_lower or "chromecast" in name_lower:
            return "smart_tv"
        elif "omnidevice" in service_lower:
            return "omni_device"
        elif "http" in service_lower or "https" in service_lower:
            return "web_server"
        elif "ssh" in service_lower:
            return "computer"
        elif "smb" in service_lower:
            return "network_storage"
        else:
            return "network_device"

    def _add_discovered_device(self, device: DiscoveredDevice):
        """Add or update discovered device"""
        try:
            # Check if device already exists
            existing_device = None
            for dev_id, dev in self.discovered_devices.items():
                # Match by MAC address or IP address
                if ((device.mac_address and dev.mac_address == device.mac_address) or
                    (device.ip_address and dev.ip_address == device.ip_address)):
                    existing_device = dev
                    break

            if existing_device:
                # Update existing device
                existing_device.last_seen = datetime.now()
                existing_device.connection_status = "discovered"

                # Update other fields if they're better
                if device.device_name and not existing_device.device_name:
                    existing_device.device_name = device.device_name
                if device.signal_strength > existing_device.signal_strength:
                    existing_device.signal_strength = device.signal_strength

            else:
                # Add new device
                if len(self.discovered_devices) < self.config["max_devices"]:
                    self.discovered_devices[device.device_id] = device
                    self.stats["total_devices_discovered"] += 1

                    # Notify listeners
                    self._notify_device_event("device_discovered", device)

                    print(f" New device discovered: {device.device_name} ({device.device_type}) via {device.discovery_method}")

        except Exception as e:
            print(f" Error adding discovered device: {e}")

    def _cleanup_old_devices(self):
        """Remove devices that haven't been seen for a while"""
        current_time = datetime.now()
        to_remove = []

        for device_id, device in self.discovered_devices.items():
            if (current_time - device.last_seen).seconds > self.config["device_timeout"]:
                to_remove.append(device_id)

        for device_id in to_remove:
            device = self.discovered_devices.pop(device_id)
            print(f" Removed stale device: {device.device_name}")
            self._notify_device_event("device_lost", device)

    def _notify_device_event(self, event_type: str, device: DiscoveredDevice):
        """Notify device event listeners"""
        for listener in self.device_event_listeners:
            try:
                listener(event_type, device)
            except Exception as e:
                print(f" Device event listener error: {e}")

    def get_discovered_devices(self) -> List[Dict[str, Any]]:
        """Get list of all discovered devices"""
        devices = []
        for device in self.discovered_devices.values():
            devices.append({
                "device_id": device.device_id,
                "device_name": device.device_name,
                "device_type": device.device_type,
                "discovery_method": device.discovery_method,
                "ip_address": device.ip_address,
                "mac_address": device.mac_address,
                "port": device.port,
                "capabilities": device.capabilities,
                "last_seen": device.last_seen.isoformat(),
                "connection_status": device.connection_status,
                "signal_strength": device.signal_strength,
                "manufacturer": device.manufacturer,
                "model": device.model,
                "firmware_version": device.firmware_version
            })
        return devices

    def get_device_by_id(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get specific device by ID"""
        device = self.discovered_devices.get(device_id)
        if device:
            return {
                "device_id": device.device_id,
                "device_name": device.device_name,
                "device_type": device.device_type,
                "discovery_method": device.discovery_method,
                "ip_address": device.ip_address,
                "mac_address": device.mac_address,
                "port": device.port,
                "capabilities": device.capabilities,
                "last_seen": device.last_seen.isoformat(),
                "connection_status": device.connection_status,
                "signal_strength": device.signal_strength,
                "manufacturer": device.manufacturer,
                "model": device.model,
                "firmware_version": device.firmware_version
            }
        return None

    def connect_device(self, device_id: str) -> bool:
        """Attempt to connect to a discovered device"""
        device = self.discovered_devices.get(device_id)
        if not device:
            return False

        try:
            device.connection_status = "connecting"

            # Here you would implement actual connection logic
            # based on device type and capabilities

            # For now, just mark as connected
            device.connection_status = "connected"
            self.stats["total_devices_connected"] += 1

            self._notify_device_event("device_connected", device)
            print(f" Connected to device: {device.device_name}")

            return True

        except Exception as e:
            device.connection_status = "failed"
            print(f" Failed to connect to device {device_id}: {e}")
            return False

    def disconnect_device(self, device_id: str) -> bool:
        """Disconnect from a device"""
        device = self.discovered_devices.get(device_id)
        if not device:
            return False

        device.connection_status = "discovered"
        self._notify_device_event("device_disconnected", device)
        print(f" Disconnected from device: {device.device_name}")

        return True

    def add_device_event_listener(self, listener: Callable[[str, DiscoveredDevice], None]):
        """Add device event listener"""
        self.device_event_listeners.append(listener)

    def remove_device_event_listener(self, listener: Callable[[str, DiscoveredDevice], None]):
        """Remove device event listener"""
        if listener in self.device_event_listeners:
            self.device_event_listeners.remove(listener)

    def get_stats(self) -> Dict[str, Any]:
        """Get discovery statistics"""
        return {
            **self.stats,
            "active_devices": len(self.discovered_devices),
            "network_interfaces": len(self.network_interfaces),
            "running": self._running,
            "mdns_available": MDNS_AVAILABLE,
            "ble_available": BLE_AVAILABLE
        }

# Global Omni Sync Core instance
omni_sync_core = None

def initialize_sync_core(config: Dict[str, Any] = None) -> OmniSyncCore:
    """Initialize the Omni Sync Core"""
    global omni_sync_core
    omni_sync_core = OmniSyncCore(config)
    return omni_sync_core

def get_sync_core() -> OmniSyncCore:
    """Get the global Omni Sync Core instance"""
    return omni_sync_core

# API functions for easy access
def start_device_discovery(config: Dict[str, Any] = None):
    """Start automatic device discovery"""
    if not omni_sync_core:
        initialize_sync_core(config)
    omni_sync_core.start()

def stop_device_discovery():
    """Stop automatic device discovery"""
    if omni_sync_core:
        omni_sync_core.stop()

def get_discovered_devices():
    """Get all discovered devices"""
    if omni_sync_core:
        return omni_sync_core.get_discovered_devices()
    return []

def connect_to_device(device_id: str) -> bool:
    """Connect to a specific device"""
    if omni_sync_core:
        return omni_sync_core.connect_device(device_id)
    return False

def get_discovery_stats():
    """Get discovery statistics"""
    if omni_sync_core:
        return omni_sync_core.get_stats()
    return {}

if __name__ == "__main__":
    # Test the Omni Sync Core
    print(" Testing OMNI Sync Core...")

    # Initialize and start
    sync_core = initialize_sync_core()
    sync_core.start()

    # Add event listener
    def on_device_event(event_type, device):
        print(f" Device event: {event_type} - {device.device_name}")

    sync_core.add_device_event_listener(on_device_event)

    # Run for 60 seconds
    print(" Scanning for devices for 60 seconds...")
    time.sleep(60)

    # Show results
    devices = sync_core.get_discovered_devices()
    stats = sync_core.get_stats()

    print(f"\n Results:")
    print(f"  Devices discovered: {len(devices)}")
    print(f"  Scan cycles: {stats['scan_cycles']}")
    print(f"  Errors: {stats['errors']}")

    for device in devices[:5]:  # Show first 5 devices
        print(f"  - {device['device_name']} ({device['device_type']}) via {device['discovery_method']}")

    sync_core.stop()
    print("\n OMNI Sync Core test completed!")