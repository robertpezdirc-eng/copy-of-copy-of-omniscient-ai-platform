#!/usr/bin/env python3
"""
OMNI Device Manager - Unified Device Registration and Management
Integrates VR devices with network-discovered devices from Omni Sync Core

Author: OMNI Platform
Version: 1.0.0
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
import logging
import threading
import websockets

from omni_sync_core import get_sync_core, DiscoveredDevice
from omni_vr_device_manager import get_vr_device_manager, VRDeviceConnection, VRDeviceCapabilities

@dataclass
class UnifiedDevice:
    """Unified device information combining all device types"""
    device_id: str
    device_name: str
    device_type: str
    category: str  # 'vr', 'network', 'iot', 'mobile', etc.
    connection_id: Optional[str] = None

    # Network information
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    port: Optional[int] = None

    # Status information
    connection_status: str = "discovered"  # discovered, connecting, connected, failed, disconnected
    last_seen: datetime = field(default_factory=datetime.now)

    # Capabilities and metadata
    capabilities: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # User association
    user_id: Optional[str] = None
    registered_at: Optional[datetime] = None

    # Connection quality metrics
    connection_quality: float = 1.0
    bandwidth_usage: float = 0.0
    latency: Optional[float] = None

@dataclass
class DeviceConnection:
    """Active device connection"""
    connection_id: str
    device_id: str
    connection_type: str  # 'websocket', 'http', 'tcp', 'udp'
    protocol: str  # 'ws', 'http', 'tcp', 'udp'
    endpoint: str
    connected_at: datetime
    last_activity: datetime
    status: str = "connected"

class OmniDeviceManager:
    """Unified Device Manager for OMNI Platform"""

    def __init__(self):
        # Device storage
        self.devices: Dict[str, UnifiedDevice] = {}
        self.connections: Dict[str, DeviceConnection] = {}
        self.device_event_listeners: List[Callable] = []

        # Integration with existing managers
        self.sync_core = None
        self.vr_manager = None
        self.quest3_manager = None

        # Background services
        self._running = False
        self._monitor_thread = None

        # Configuration
        self.config = {
            "connection_timeout": 300,  # seconds
            "cleanup_interval": 60,     # seconds
            "max_devices": 1000,
            "auto_register_discovered": True,
            "enable_vr_integration": True,
            "enable_sync_integration": True
        }

        print(" OMNI Device Manager initialized")

    def start(self):
        """Start the device manager"""
        if self._running:
            print(" Device manager already running")
            return

        self._running = True

        # Initialize integrations
        if self.config["enable_sync_integration"]:
            self.sync_core = get_sync_core()
            if self.sync_core:
                self.sync_core.add_device_event_listener(self._on_sync_device_event)

        if self.config["enable_vr_integration"]:
            self.vr_manager = get_vr_device_manager()

        # Quest 3 manager will be initialized separately to avoid circular imports

        # Start monitoring thread
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()


        print(" OMNI Device Manager started")

    def stop(self):
        """Stop the device manager"""
        if not self._running:
            return

        self._running = False
        print(" OMNI Device Manager stopped")

    def _monitor_loop(self):
        """Monitor device connections and cleanup"""
        while self._running:
            try:
                current_time = datetime.now()

                # Check for inactive connections
                inactive_connections = []
                for conn_id, connection in self.connections.items():
                    if (current_time - connection.last_activity).seconds > self.config["connection_timeout"]:
                        inactive_connections.append(conn_id)

                # Clean up inactive connections
                for conn_id in inactive_connections:
                    self._disconnect_device_connection(conn_id)

                # Update device last seen times
                for device in self.devices.values():
                    if device.connection_status == "connected":
                        # Check if device has active connections
                        active_conns = [c for c in self.connections.values() if c.device_id == device.device_id]
                        if not active_conns:
                            device.connection_status = "disconnected"

                time.sleep(self.config["cleanup_interval"])

            except Exception as e:
                print(f" Monitor loop error: {e}")
                time.sleep(self.config["cleanup_interval"])

    def _on_sync_device_event(self, event_type: str, device: DiscoveredDevice):
        """Handle device events from Omni Sync Core"""
        try:
            if event_type == "device_discovered":
                self._register_discovered_device(device)
            elif event_type == "device_lost":
                self._handle_device_lost(device)
            elif event_type == "device_connected":
                self._handle_device_connected(device)
            elif event_type == "device_disconnected":
                self._handle_device_disconnected(device)

        except Exception as e:
            print(f" Sync device event error: {e}")

    def _register_discovered_device(self, device: DiscoveredDevice):
        """Register a device discovered by Omni Sync Core"""
        try:
            # Check if device already exists
            existing_device = None
            for dev_id, dev in self.devices.items():
                # Match by MAC or IP address
                if ((device.mac_address and dev.mac_address == device.mac_address) or
                    (device.ip_address and dev.ip_address == device.ip_address)):
                    existing_device = dev
                    break

            if existing_device:
                # Update existing device
                existing_device.last_seen = datetime.now()
                existing_device.connection_status = "discovered"
                if device.device_name:
                    existing_device.device_name = device.device_name
                return

            # Create new unified device
            unified_device = UnifiedDevice(
                device_id=device.device_id,
                device_name=device.device_name,
                device_type=device.device_type,
                category=self._categorize_device(device.device_type),
                ip_address=device.ip_address,
                mac_address=device.mac_address,
                port=device.port,
                capabilities=device.capabilities,
                last_seen=device.last_seen,
                connection_status=device.connection_status,
                metadata={
                    "discovery_method": device.discovery_method,
                    "signal_strength": device.signal_strength,
                    "manufacturer": device.manufacturer,
                    "model": device.model,
                    "firmware_version": device.firmware_version
                }
            )

            # Add to devices if under limit
            if len(self.devices) < self.config["max_devices"]:
                self.devices[device.device_id] = unified_device

                # Notify listeners
                self._notify_device_event("device_registered", unified_device)

                print(f" Registered discovered device: {device.device_name} ({device.device_type})")

        except Exception as e:
            print(f" Error registering discovered device: {e}")

    def _categorize_device(self, device_type: str) -> str:
        """Categorize device type"""
        device_lower = device_type.lower()

        if any(vr_type in device_lower for vr_type in ["vr", "oculus", "vive", "quest", "headset"]):
            return "vr"
        elif any(network_type in device_lower for network_type in ["computer", "laptop", "desktop", "server"]):
            return "computer"
        elif any(mobile_type in device_lower for mobile_type in ["phone", "smartphone", "tablet", "mobile"]):
            return "mobile"
        elif any(iot_type in device_lower for iot_type in ["iot", "smart", "sensor", "camera", "speaker"]):
            return "iot"
        elif any(tv_type in device_lower for tv_type in ["tv", "display", "monitor", "screen"]):
            return "display"
        elif any(audio_type in device_lower for audio_type in ["speaker", "audio", "sound"]):
            return "audio"
        else:
            return "network"

    def register_device(self, device_info: Dict[str, Any], user_id: str = None) -> str:
        """Register a new device manually"""
        try:
            device_id = str(uuid.uuid4())

            unified_device = UnifiedDevice(
                device_id=device_id,
                device_name=device_info.get("device_name", f"Device_{device_id[:8]}"),
                device_type=device_info.get("device_type", "unknown"),
                category=self._categorize_device(device_info.get("device_type", "unknown")),
                ip_address=device_info.get("ip_address"),
                mac_address=device_info.get("mac_address"),
                port=device_info.get("port"),
                capabilities=device_info.get("capabilities", {}),
                user_id=user_id,
                registered_at=datetime.now(),
                connection_status="registered"
            )

            self.devices[device_id] = unified_device

            self._notify_device_event("device_registered", unified_device)

            print(f" Manually registered device: {unified_device.device_name}")
            return device_id

        except Exception as e:
            print(f" Error registering device: {e}")
            return None

    def connect_device(self, device_id: str, connection_info: Dict[str, Any] = None) -> bool:
        """Connect to a device"""
        device = self.devices.get(device_id)
        if not device:
            return False

        try:
            device.connection_status = "connecting"

            # Create connection based on device category
            if device.category == "vr" and self.vr_manager:
                # Handle VR device connection
                return self._connect_vr_device(device, connection_info)
            else:
                # Handle general network device connection
                return self._connect_network_device(device, connection_info)

        except Exception as e:
            device.connection_status = "failed"
            print(f" Error connecting to device {device_id}: {e}")
            return False

    def _connect_vr_device(self, device: UnifiedDevice, connection_info: Dict[str, Any]) -> bool:
        """Connect to VR device"""
        if not self.vr_manager:
            return False

        try:
            # Register with VR manager if not already registered
            if not any(vr_dev.device_id == device.device_id for vr_dev in self.vr_manager.get_device_list()):
                vr_device_info = {
                    "device_type": device.device_type,
                    "device_name": device.device_name,
                    "capabilities": device.capabilities
                }

                vr_device_id = self.vr_manager.register_device(vr_device_info, device.user_id or "system")

                if vr_device_id:
                    print(f" VR device registered with VR manager: {device.device_name}")
                    device.connection_status = "connected"
                    self._notify_device_event("device_connected", device)
                    return True

            return False

        except Exception as e:
            print(f" VR device connection error: {e}")
            return False

    def _connect_network_device(self, device: UnifiedDevice, connection_info: Dict[str, Any]) -> bool:
        """Connect to network device"""
        try:
            # Create connection record
            connection_id = str(uuid.uuid4())
            connection = DeviceConnection(
                connection_id=connection_id,
                device_id=device.device_id,
                connection_type=connection_info.get("type", "tcp"),
                protocol=connection_info.get("protocol", "tcp"),
                endpoint=f"{device.ip_address}:{device.port}" if device.ip_address and device.port else device.ip_address or "unknown",
                connected_at=datetime.now(),
                last_activity=datetime.now()
            )

            self.connections[connection_id] = connection
            device.connection_status = "connected"

            self._notify_device_event("device_connected", device)

            print(f" Network device connected: {device.device_name}")
            return True

        except Exception as e:
            print(f" Network device connection error: {e}")
            return False

    def disconnect_device(self, device_id: str) -> bool:
        """Disconnect a device"""
        device = self.devices.get(device_id)
        if not device:
            return False

        try:
            # Disconnect from VR manager if it's a VR device
            if device.category == "vr" and self.vr_manager:
                # Find and disconnect VR connections
                pass

            # Remove all connections for this device
            device_connections = [c for c in self.connections.values() if c.device_id == device_id]
            for connection in device_connections:
                self._disconnect_device_connection(connection.connection_id)

            device.connection_status = "disconnected"
            self._notify_device_event("device_disconnected", device)

            print(f" Device disconnected: {device.device_name}")
            return True

        except Exception as e:
            print(f" Error disconnecting device: {e}")
            return False

    def _disconnect_device_connection(self, connection_id: str):
        """Disconnect a specific connection"""
        if connection_id in self.connections:
            connection = self.connections.pop(connection_id)
            print(f" Connection closed: {connection.endpoint}")

    def _handle_device_lost(self, device: DiscoveredDevice):
        """Handle device lost event"""
        # Find and update device
        for unified_device in self.devices.values():
            if unified_device.device_id == device.device_id:
                unified_device.connection_status = "disconnected"
                unified_device.last_seen = datetime.now()
                self._notify_device_event("device_lost", unified_device)
                break

    def _handle_device_connected(self, device: DiscoveredDevice):
        """Handle device connected event"""
        for unified_device in self.devices.values():
            if unified_device.device_id == device.device_id:
                unified_device.connection_status = "connected"
                unified_device.last_seen = datetime.now()
                self._notify_device_event("device_connected", unified_device)
                break

    def _handle_device_disconnected(self, device: DiscoveredDevice):
        """Handle device disconnected event"""
        for unified_device in self.devices.values():
            if unified_device.device_id == device.device_id:
                unified_device.connection_status = "disconnected"
                unified_device.last_seen = datetime.now()
                self._notify_device_event("device_disconnected", unified_device)
                break

    def send_to_device(self, device_id: str, message: Dict[str, Any]) -> bool:
        """Send message to device"""
        device = self.devices.get(device_id)
        if not device:
            return False

        try:
            # Route to appropriate handler based on device category
            if device.category == "vr" and self.vr_manager:
                return self.vr_manager.send_to_device(device_id, message)
            else:
                # Handle general network device messaging
                # Find active connection for this device
                device_connections = [c for c in self.connections.values()
                                    if c.device_id == device_id and c.status == "connected"]

                if device_connections:
                    # Send via first available connection
                    print(f" Message sent to {device.device_name}: {message.get('type', 'unknown')}")
                    return True

            return False

        except Exception as e:
            print(f" Error sending message to device: {e}")
            return False

    def get_devices(self, category: str = None, status: str = None) -> List[Dict[str, Any]]:
        """Get list of devices with optional filtering"""
        devices = []

        for device in self.devices.values():
            # Apply filters
            if category and device.category != category:
                continue
            if status and device.connection_status != status:
                continue

            devices.append({
                "device_id": device.device_id,
                "device_name": device.device_name,
                "device_type": device.device_type,
                "category": device.category,
                "connection_status": device.connection_status,
                "ip_address": device.ip_address,
                "mac_address": device.mac_address,
                "port": device.port,
                "capabilities": device.capabilities,
                "metadata": device.metadata,
                "last_seen": device.last_seen.isoformat(),
                "user_id": device.user_id,
                "registered_at": device.registered_at.isoformat() if device.registered_at else None,
                "connection_quality": device.connection_quality,
                "latency": device.latency
            })

        return devices

    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get specific device by ID"""
        device = self.devices.get(device_id)
        if device:
            return {
                "device_id": device.device_id,
                "device_name": device.device_name,
                "device_type": device.device_type,
                "category": device.category,
                "connection_status": device.connection_status,
                "ip_address": device.ip_address,
                "mac_address": device.mac_address,
                "port": device.port,
                "capabilities": device.capabilities,
                "metadata": device.metadata,
                "last_seen": device.last_seen.isoformat(),
                "user_id": device.user_id,
                "registered_at": device.registered_at.isoformat() if device.registered_at else None,
                "connection_quality": device.connection_quality,
                "latency": device.latency
            }
        return None

    def update_device_info(self, device_id: str, updates: Dict[str, Any]) -> bool:
        """Update device information"""
        device = self.devices.get(device_id)
        if not device:
            return False

        try:
            # Update allowed fields
            for field in ["device_name", "capabilities", "metadata"]:
                if field in updates:
                    setattr(device, field, updates[field])

            device.last_seen = datetime.now()
            self._notify_device_event("device_updated", device)

            return True

        except Exception as e:
            print(f" Error updating device: {e}")
            return False

    def remove_device(self, device_id: str) -> bool:
        """Remove a device"""
        if device_id not in self.devices:
            return False

        try:
            device = self.devices.pop(device_id)

            # Remove all connections for this device
            device_connections = [c for c in self.connections.values() if c.device_id == device_id]
            for connection in device_connections:
                self.connections.pop(connection.connection_id, None)

            self._notify_device_event("device_removed", device)

            print(f" Device removed: {device.device_name}")
            return True

        except Exception as e:
            print(f" Error removing device: {e}")
            return False

    def _notify_device_event(self, event_type: str, device: UnifiedDevice):
        """Notify device event listeners"""
        for listener in self.device_event_listeners:
            try:
                listener(event_type, device)
            except Exception as e:
                print(f" Device event listener error: {e}")

    def add_device_event_listener(self, listener: Callable[[str, UnifiedDevice], None]):
        """Add device event listener"""
        self.device_event_listeners.append(listener)

    def remove_device_event_listener(self, listener: Callable[[str, UnifiedDevice], None]):
        """Remove device event listener"""
        if listener in self.device_event_listeners:
            self.device_event_listeners.remove(listener)

    def get_stats(self) -> Dict[str, Any]:
        """Get device manager statistics"""
        total_devices = len(self.devices)
        connected_devices = len([d for d in self.devices.values() if d.connection_status == "connected"])
        disconnected_devices = len([d for d in self.devices.values() if d.connection_status == "disconnected"])

        # Category breakdown
        categories = {}
        for device in self.devices.values():
            categories[device.category] = categories.get(device.category, 0) + 1

        return {
            "total_devices": total_devices,
            "connected_devices": connected_devices,
            "disconnected_devices": disconnected_devices,
            "active_connections": len(self.connections),
            "categories": categories,
            "running": self._running,
            "last_updated": datetime.now().isoformat()
        }

# Global device manager instance
omni_device_manager = None

def initialize_device_manager() -> OmniDeviceManager:
    """Initialize the device manager"""
    global omni_device_manager
    omni_device_manager = OmniDeviceManager()
    return omni_device_manager

def get_device_manager() -> OmniDeviceManager:
    """Get the global device manager instance"""
    return omni_device_manager

# API functions for easy access
def register_device(device_info: Dict[str, Any], user_id: str = None) -> str:
    """Register a device"""
    if not omni_device_manager:
        initialize_device_manager()
    return omni_device_manager.register_device(device_info, user_id)

def get_devices(category: str = None, status: str = None) -> List[Dict[str, Any]]:
    """Get devices with optional filtering"""
    if not omni_device_manager:
        initialize_device_manager()
    return omni_device_manager.get_devices(category, status)

def get_device(device_id: str) -> Optional[Dict[str, Any]]:
    """Get specific device"""
    if not omni_device_manager:
        initialize_device_manager()
    return omni_device_manager.get_device(device_id)

def connect_device(device_id: str, connection_info: Dict[str, Any] = None) -> bool:
    """Connect to device"""
    if not omni_device_manager:
        initialize_device_manager()
    return omni_device_manager.connect_device(device_id, connection_info)

def disconnect_device(device_id: str) -> bool:
    """Disconnect from device"""
    if not omni_device_manager:
        initialize_device_manager()
    return omni_device_manager.disconnect_device(device_id)

def send_to_device(device_id: str, message: Dict[str, Any]) -> bool:
    """Send message to device"""
    if not omni_device_manager:
        initialize_device_manager()
    return omni_device_manager.send_to_device(device_id, message)

def get_device_stats() -> Dict[str, Any]:
    """Get device statistics"""
    if not omni_device_manager:
        initialize_device_manager()
    return omni_device_manager.get_stats()

if __name__ == "__main__":
    # Test the device manager
    print(" Testing OMNI Device Manager...")

    # Initialize managers
    device_manager = initialize_device_manager()
    device_manager.start()

    # Test device registration
    device_info = {
        "device_name": "Test VR Headset",
        "device_type": "oculus_quest",
        "ip_address": "192.168.1.100",
        "capabilities": {
            "hand_tracking": True,
            "eye_tracking": False
        }
    }

    device_id = register_device(device_info, "test_user")
    print(f" Device registered: {device_id}")

    # Test getting devices
    devices = get_devices()
    print(f" Found {len(devices)} devices")

    for device in devices:
        print(f"  - {device['device_name']} ({device['device_type']}) - {device['connection_status']}")

    # Test stats
    stats = get_device_stats()
    print(f" Device stats: {stats}")

    print("\n OMNI Device Manager test completed!")