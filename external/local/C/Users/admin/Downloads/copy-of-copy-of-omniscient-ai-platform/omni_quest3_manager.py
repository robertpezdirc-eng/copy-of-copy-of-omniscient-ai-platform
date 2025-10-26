#!/usr/bin/env python3
"""
OMNI Meta Quest 3 Manager
Advanced Meta Quest 3 VR/AR integration with mixed reality capabilities

Author: OMNI Platform
Version: 1.0.0
"""

import asyncio
import json
import time
import uuid
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
import logging
import socket
import subprocess

from omni_device_manager import get_device_manager, UnifiedDevice
from omni_sync_core import get_sync_core

@dataclass
class Quest3Capabilities:
    """Meta Quest 3 specific capabilities"""
    # Hardware specs
    processor: str = "Qualcomm Snapdragon XR2 Gen 2"
    ram: str = "8GB"
    storage: str = "128GB/512GB"

    # VR/AR features
    mixed_reality: bool = True
    passthrough_cameras: int = 4
    refresh_rate_max: int = 120
    resolution_per_eye: Tuple[int, int] = (2064, 2208)

    # Tracking capabilities
    hand_tracking: bool = True
    eye_tracking: bool = True
    face_tracking: bool = True
    body_tracking: bool = True

    # Controllers
    touch_controllers: bool = True
    controller_tracking: bool = True

    # Connectivity
    wifi_6e: bool = True
    bluetooth_5_2: bool = True
    usb_c: bool = True

    # Software features
    standalone_mode: bool = True
    pc_connection: bool = True
    oculus_link: bool = True
    air_link: bool = True

@dataclass
class Quest3TrackingData:
    """Real-time tracking data from Quest 3"""
    timestamp: datetime
    device_id: str

    # Hand tracking
    left_hand_position: Optional[Tuple[float, float, float]] = None
    right_hand_position: Optional[Tuple[float, float, float]] = None
    hand_gestures: Dict[str, str] = field(default_factory=dict)

    # Eye tracking
    left_eye_gaze: Optional[Tuple[float, float, float]] = None
    right_eye_gaze: Optional[Tuple[float, float, float]] = None
    eye_convergence: Optional[float] = None

    # Body tracking
    head_position: Optional[Tuple[float, float, float]] = None
    head_rotation: Optional[Tuple[float, float, float]] = None
    body_position: Optional[Tuple[float, float, float]] = None

    # Controller tracking
    left_controller: Dict[str, Any] = field(default_factory=dict)
    right_controller: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Quest3AROverlay:
    """AR overlay data for Quest 3"""
    overlay_id: str
    device_id: str
    overlay_type: str  # 'device_data', 'system_status', 'notification', 'custom'

    # Position and appearance
    position: Tuple[float, float, float] = (0, 0, 0)
    rotation: Tuple[float, float, float] = (0, 0, 0)
    scale: Tuple[float, float, float] = (1, 1, 1)

    # Content
    title: str = ""
    content: str = ""
    data_source: str = ""  # Which OMNI device/data source

    # Styling
    background_color: str = "#000000"
    text_color: str = "#FFFFFF"
    opacity: float = 0.8

    # Behavior
    persistent: bool = True
    timeout: Optional[int] = None  # seconds
    follow_user: bool = False

class OmniQuest3Manager:
    """Meta Quest 3 VR/AR Device Manager for OMNI Platform"""

    def __init__(self):
        # Quest 3 devices and connections
        self.devices: Dict[str, Dict[str, Any]] = {}
        self.tracking_data: Dict[str, Quest3TrackingData] = {}
        self.ar_overlays: Dict[str, Quest3AROverlay] = {}
        self.active_connections: Dict[str, Dict[str, Any]] = {}

        # Integration with OMNI platform
        self.device_manager = None
        self.sync_core = None

        # Background services
        self._running = False
        self._monitor_thread = None
        self._ar_update_thread = None

        # Event listeners
        self.tracking_listeners: List[Callable] = []
        self.ar_overlay_listeners: List[Callable] = []

        # Configuration
        self.config = {
            "ar_overlay_update_interval": 0.1,  # 10 FPS for smooth AR
            "tracking_data_buffer_size": 100,
            "max_ar_overlays": 50,
            "default_connection_mode": "standalone",  # standalone, oculus_link, air_link
            "passthrough_enabled": True,
            "mixed_reality_enabled": True
        }

        print("Meta Quest 3 Manager initialized")

    def start(self):
        """Start the Quest 3 manager"""
        if self._running:
            print("Quest 3 manager already running")
            return

        self._running = True

        # Initialize OMNI platform integrations
        self.device_manager = get_device_manager()
        self.sync_core = get_sync_core()

        # Start background threads
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

        self._ar_update_thread = threading.Thread(target=self._ar_update_loop, daemon=True)
        self._ar_update_thread.start()

        print("Meta Quest 3 Manager started")

    def stop(self):
        """Stop the Quest 3 manager"""
        if not self._running:
            return

        self._running = False

        # Close all connections
        for device_id in list(self.active_connections.keys()):
            self.disconnect_quest3(device_id)

        print("Meta Quest 3 Manager stopped")

    def register_quest3(self, device_info: Dict[str, Any], user_id: str = None) -> str:
        """Register a new Meta Quest 3 device"""
        try:
            device_id = str(uuid.uuid4())

            # Create Quest 3 device profile
            quest3_device = {
                "device_id": device_id,
                "device_name": device_info.get("device_name", "Meta Quest 3"),
                "device_type": "meta_quest_3",
                "category": "vr_ar",
                "user_id": user_id,

                # Hardware info
                "serial_number": device_info.get("serial_number"),
                "firmware_version": device_info.get("firmware_version"),
                "capabilities": Quest3Capabilities().__dict__,

                # Connection info
                "connection_mode": device_info.get("connection_mode", self.config["default_connection_mode"]),
                "ip_address": device_info.get("ip_address"),
                "connection_status": "registered",

                # Registration
                "registered_at": datetime.now(),
                "last_seen": datetime.now(),

                # Quest 3 specific features
                "mixed_reality_enabled": self.config["mixed_reality_enabled"],
                "passthrough_enabled": self.config["passthrough_enabled"],
                "tracking_features": {
                    "hand_tracking": True,
                    "eye_tracking": True,
                    "face_tracking": True,
                    "body_tracking": True
                }
            }

            self.devices[device_id] = quest3_device

            # Register with unified device manager
            if self.device_manager:
                unified_device_info = {
                    "device_name": quest3_device["device_name"],
                    "device_type": "meta_quest_3",
                    "ip_address": quest3_device["ip_address"],
                    "capabilities": quest3_device["capabilities"]
                }
                self.device_manager.register_device(unified_device_info, user_id)

            print(f"Meta Quest 3 registered: {quest3_device['device_name']}")
            return device_id

        except Exception as e:
            print(f"Error registering Quest 3: {e}")
            return None

    def connect_quest3(self, device_id: str, connection_mode: str = None) -> bool:
        """Connect to Meta Quest 3"""
        if device_id not in self.devices:
            print(f"Quest 3 device {device_id} not found")
            return False

        device = self.devices[device_id]
        device["connection_status"] = "connecting"

        try:
            if connection_mode:
                device["connection_mode"] = connection_mode

            # Simulate connection process
            if device["connection_mode"] == "standalone":
                success = self._connect_standalone(device_id)
            elif device["connection_mode"] == "oculus_link":
                success = self._connect_oculus_link(device_id)
            elif device["connection_mode"] == "air_link":
                success = self._connect_air_link(device_id)
            else:
                success = self._connect_standalone(device_id)

            if success:
                device["connection_status"] = "connected"
                device["last_seen"] = datetime.now()

                # Initialize tracking data buffer
                self.tracking_data[device_id] = Quest3TrackingData(
                    timestamp=datetime.now(),
                    device_id=device_id
                )

                print(f"Meta Quest 3 connected: {device['device_name']} ({device['connection_mode']})")
                return True
            else:
                device["connection_status"] = "failed"
                return False

        except Exception as e:
            device["connection_status"] = "failed"
            print(f"Error connecting Quest 3 {device_id}: {e}")
            return False

    def _connect_standalone(self, device_id: str) -> bool:
        """Connect to Quest 3 in standalone mode"""
        device = self.devices[device_id]

        # In real implementation, this would:
        # 1. Establish Wi-Fi connection to Quest 3
        # 2. Initialize ADB connection
        # 3. Start Quest 3 services
        # 4. Enable passthrough/mixed reality

        # For demo, simulate successful connection
        connection_info = {
            "connection_id": str(uuid.uuid4()),
            "device_id": device_id,
            "connection_type": "wifi_standalone",
            "connected_at": datetime.now(),
            "status": "connected"
        }

        self.active_connections[device_id] = connection_info
        return True

    def _connect_oculus_link(self, device_id: str) -> bool:
        """Connect to Quest 3 via Oculus Link (USB-C)"""
        device = self.devices[device_id]

        # In real implementation, this would:
        # 1. Check USB-C connection
        # 2. Initialize Oculus Link software
        # 3. Enable PC VR mode

        connection_info = {
            "connection_id": str(uuid.uuid4()),
            "device_id": device_id,
            "connection_type": "usb_link",
            "connected_at": datetime.now(),
            "status": "connected"
        }

        self.active_connections[device_id] = connection_info
        return True

    def _connect_air_link(self, device_id: str) -> bool:
        """Connect to Quest 3 via Air Link (Wi-Fi)"""
        device = self.devices[device_id]

        # In real implementation, this would:
        # 1. Establish Wi-Fi Direct connection
        # 2. Initialize Air Link streaming
        # 3. Enable PC VR mode over Wi-Fi

        connection_info = {
            "connection_id": str(uuid.uuid4()),
            "device_id": device_id,
            "connection_type": "wifi_air_link",
            "connected_at": datetime.now(),
            "status": "connected"
        }

        self.active_connections[device_id] = connection_info
        return True

    def disconnect_quest3(self, device_id: str) -> bool:
        """Disconnect from Meta Quest 3"""
        if device_id not in self.devices:
            return False

        try:
            device = self.devices[device_id]
            device["connection_status"] = "disconnected"

            # Close connection
            if device_id in self.active_connections:
                del self.active_connections[device_id]

            # Clear tracking data
            if device_id in self.tracking_data:
                del self.tracking_data[device_id]

            print(f"Meta Quest 3 disconnected: {device['device_name']}")
            return True

        except Exception as e:
            print(f"Error disconnecting Quest 3: {e}")
            return False

    def update_tracking_data(self, device_id: str, tracking_data: Dict[str, Any]) -> bool:
        """Update real-time tracking data from Quest 3"""
        if device_id not in self.devices or device_id not in self.active_connections:
            return False

        try:
            # Create new tracking data entry
            quest_tracking = Quest3TrackingData(
                timestamp=datetime.now(),
                device_id=device_id
            )

            # Update hand tracking
            if "hands" in tracking_data:
                hands = tracking_data["hands"]
                if "left" in hands:
                    quest_tracking.left_hand_position = tuple(hands["left"].get("position", [0, 0, 0]))
                if "right" in hands:
                    quest_tracking.right_hand_position = tuple(hands["right"].get("position", [0, 0, 0]))
                quest_tracking.hand_gestures = hands.get("gestures", {})

            # Update eye tracking
            if "eyes" in tracking_data:
                eyes = tracking_data["eyes"]
                if "left_gaze" in eyes:
                    quest_tracking.left_eye_gaze = tuple(eyes["left_gaze"])
                if "right_gaze" in eyes:
                    quest_tracking.right_eye_gaze = tuple(eyes["right_gaze"])
                quest_tracking.eye_convergence = eyes.get("convergence")

            # Update body tracking
            if "body" in tracking_data:
                body = tracking_data["body"]
                if "head" in body:
                    quest_tracking.head_position = tuple(body["head"].get("position", [0, 0, 0]))
                    quest_tracking.head_rotation = tuple(body["head"].get("rotation", [0, 0, 0]))
                if "body_position" in body:
                    quest_tracking.body_position = tuple(body["body_position"])

            # Update controller tracking
            if "controllers" in tracking_data:
                controllers = tracking_data["controllers"]
                quest_tracking.left_controller = controllers.get("left", {})
                quest_tracking.right_controller = controllers.get("right", {})

            # Store tracking data (keep buffer size)
            self.tracking_data[device_id] = quest_tracking

            # Notify tracking listeners
            self._notify_tracking_update(device_id, quest_tracking)

            return True

        except Exception as e:
            print(f"Error updating tracking data: {e}")
            return False

    def create_ar_overlay(self, device_id: str, overlay_info: Dict[str, Any]) -> str:
        """Create AR overlay for Quest 3 mixed reality"""
        if device_id not in self.devices or device_id not in self.active_connections:
            return None

        try:
            overlay_id = str(uuid.uuid4())

            # Get data source from OMNI platform
            data_content = ""
            if overlay_info.get("data_source"):
                data_content = self._get_omni_data(overlay_info["data_source"])

            ar_overlay = Quest3AROverlay(
                overlay_id=overlay_id,
                device_id=device_id,
                overlay_type=overlay_info.get("overlay_type", "custom"),
                position=tuple(overlay_info.get("position", [0, 0, 0])),
                rotation=tuple(overlay_info.get("rotation", [0, 0, 0])),
                scale=tuple(overlay_info.get("scale", [1, 1, 1])),
                title=overlay_info.get("title", "OMNI Data"),
                content=data_content,
                data_source=overlay_info.get("data_source", ""),
                background_color=overlay_info.get("background_color", "#000000"),
                text_color=overlay_info.get("text_color", "#FFFFFF"),
                opacity=overlay_info.get("opacity", 0.8),
                persistent=overlay_info.get("persistent", True),
                timeout=overlay_info.get("timeout"),
                follow_user=overlay_info.get("follow_user", False)
            )

            self.ar_overlays[overlay_id] = ar_overlay

            # Notify AR overlay listeners
            self._notify_ar_overlay_created(device_id, ar_overlay)

            print(f"AR overlay created: {overlay_id} for device {device_id}")
            return overlay_id

        except Exception as e:
            print(f"Error creating AR overlay: {e}")
            return None

    def _get_omni_data(self, data_source: str) -> str:
        """Get data from OMNI platform for AR display"""
        try:
            if data_source == "device_count":
                devices = self.device_manager.get_devices() if self.device_manager else []
                return f"Connected Devices: {len(devices)}"

            elif data_source == "system_status":
                if self.sync_core:
                    stats = self.sync_core.get_stats()
                    return f"Scan Cycles: {stats.get('scan_cycles', 0)}\nActive: {stats.get('active_devices', 0)}"
                return "System Status: Active"

            elif data_source == "device_list":
                devices = self.device_manager.get_devices() if self.device_manager else []
                if devices:
                    device_names = [d["device_name"] for d in devices[:3]]  # First 3 devices
                    return "Devices:\n" + "\n".join(device_names)
                return "No devices found"

            elif data_source == "network_status":
                if self.sync_core:
                    stats = self.sync_core.get_stats()
                    return f"Network Interfaces: {stats.get('network_interfaces', 0)}\nDiscovery: Active"
                return "Network: Active"

            else:
                return f"OMNI Data: {data_source}"

        except Exception as e:
            return f"Error getting data: {e}"

    def remove_ar_overlay(self, overlay_id: str) -> bool:
        """Remove AR overlay"""
        if overlay_id in self.ar_overlays:
            overlay = self.ar_overlays.pop(overlay_id)
            self._notify_ar_overlay_removed(overlay.device_id, overlay)
            print(f"AR overlay removed: {overlay_id}")
            return True
        return False

    def _monitor_loop(self):
        """Monitor Quest 3 connections and status"""
        while self._running:
            try:
                current_time = datetime.now()

                # Check for inactive connections
                for device_id, device in self.devices.items():
                    if device["connection_status"] == "connected":
                        # Check if connection is still active
                        if device_id in self.active_connections:
                            connection_age = (current_time - self.active_connections[device_id]["connected_at"]).seconds
                            if connection_age > 300:  # 5 minutes timeout
                                print(f"Quest 3 connection timeout: {device['device_name']}")
                                self.disconnect_quest3(device_id)

                time.sleep(10)  # Check every 10 seconds

            except Exception as e:
                print(f"Quest 3 monitor error: {e}")
                time.sleep(10)

    def _ar_update_loop(self):
        """Update AR overlays in real-time"""
        while self._running:
            try:
                current_time = datetime.now()

                # Update AR overlays
                for overlay_id, overlay in list(self.ar_overlays.items()):
                    # Check for timeout
                    if overlay.timeout and (current_time - datetime.now()).seconds > overlay.timeout:
                        self.remove_ar_overlay(overlay_id)
                        continue

                    # Update content if data source is specified
                    if overlay.data_source:
                        new_content = self._get_omni_data(overlay.data_source)
                        if new_content != overlay.content:
                            overlay.content = new_content
                            self._notify_ar_overlay_updated(overlay.device_id, overlay)

                time.sleep(self.config["ar_overlay_update_interval"])

            except Exception as e:
                print(f"AR update error: {e}")
                time.sleep(self.config["ar_overlay_update_interval"])

    def _notify_tracking_update(self, device_id: str, tracking_data: Quest3TrackingData):
        """Notify tracking data listeners"""
        for listener in self.tracking_listeners:
            try:
                listener(device_id, tracking_data)
            except Exception as e:
                print(f"Tracking listener error: {e}")

    def _notify_ar_overlay_created(self, device_id: str, overlay: Quest3AROverlay):
        """Notify AR overlay creation"""
        for listener in self.ar_overlay_listeners:
            try:
                listener("overlay_created", device_id, overlay)
            except Exception as e:
                print(f"AR overlay listener error: {e}")

    def _notify_ar_overlay_updated(self, device_id: str, overlay: Quest3AROverlay):
        """Notify AR overlay update"""
        for listener in self.ar_overlay_listeners:
            try:
                listener("overlay_updated", device_id, overlay)
            except Exception as e:
                print(f"AR overlay listener error: {e}")

    def _notify_ar_overlay_removed(self, device_id: str, overlay: Quest3AROverlay):
        """Notify AR overlay removal"""
        for listener in self.ar_overlay_listeners:
            try:
                listener("overlay_removed", device_id, overlay)
            except Exception as e:
                print(f"AR overlay listener error: {e}")

    def add_tracking_listener(self, listener: Callable[[str, Quest3TrackingData], None]):
        """Add tracking data listener"""
        self.tracking_listeners.append(listener)

    def add_ar_overlay_listener(self, listener: Callable[[str, str, Quest3AROverlay], None]):
        """Add AR overlay listener"""
        self.ar_overlay_listeners.append(listener)

    def get_quest3_devices(self) -> List[Dict[str, Any]]:
        """Get all registered Quest 3 devices"""
        return list(self.devices.values())

    def get_quest3_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get specific Quest 3 device"""
        return self.devices.get(device_id)

    def get_tracking_data(self, device_id: str) -> Optional[Quest3TrackingData]:
        """Get latest tracking data for device"""
        return self.tracking_data.get(device_id)

    def get_ar_overlays(self, device_id: str = None) -> List[Quest3AROverlay]:
        """Get AR overlays, optionally filtered by device"""
        overlays = list(self.ar_overlays.values())
        if device_id:
            overlays = [o for o in overlays if o.device_id == device_id]
        return overlays

    def send_to_quest3(self, device_id: str, command: str, data: Dict[str, Any] = None) -> bool:
        """Send command to Quest 3"""
        if device_id not in self.devices or device_id not in self.active_connections:
            return False

        try:
            # In real implementation, this would send commands via:
            # - ADB for standalone mode
            # - Oculus API for PC-connected modes

            print(f"Command sent to Quest 3 {device_id}: {command}")

            # Handle specific commands
            if command == "enable_passthrough":
                self.devices[device_id]["passthrough_enabled"] = True
            elif command == "disable_passthrough":
                self.devices[device_id]["passthrough_enabled"] = False
            elif command == "enable_mixed_reality":
                self.devices[device_id]["mixed_reality_enabled"] = True
            elif command == "disable_mixed_reality":
                self.devices[device_id]["mixed_reality_enabled"] = False

            return True

        except Exception as e:
            print(f"Error sending command to Quest 3: {e}")
            return False

    def get_quest3_status(self) -> Dict[str, Any]:
        """Get comprehensive Quest 3 status"""
        connected_devices = len([d for d in self.devices.values() if d["connection_status"] == "connected"])
        total_devices = len(self.devices)
        active_overlays = len(self.ar_overlays)

        return {
            "total_devices": total_devices,
            "connected_devices": connected_devices,
            "active_connections": len(self.active_connections),
            "ar_overlays": active_overlays,
            "tracking_active": len(self.tracking_data) > 0,
            "running": self._running,
            "last_updated": datetime.now().isoformat()
        }

# Global Quest 3 manager instance
omni_quest3_manager = None

def initialize_quest3_manager() -> OmniQuest3Manager:
    """Initialize the Quest 3 manager"""
    global omni_quest3_manager
    omni_quest3_manager = OmniQuest3Manager()
    return omni_quest3_manager

def get_quest3_manager() -> OmniQuest3Manager:
    """Get the global Quest 3 manager instance"""
    return omni_quest3_manager

# API functions for easy access
def register_quest3(device_info: Dict[str, Any], user_id: str = None) -> str:
    """Register a Quest 3 device"""
    if not omni_quest3_manager:
        initialize_quest3_manager()
    return omni_quest3_manager.register_quest3(device_info, user_id)

def connect_quest3(device_id: str, connection_mode: str = None) -> bool:
    """Connect to Quest 3"""
    if not omni_quest3_manager:
        initialize_quest3_manager()
    return omni_quest3_manager.connect_quest3(device_id, connection_mode)

def disconnect_quest3(device_id: str) -> bool:
    """Disconnect from Quest 3"""
    if not omni_quest3_manager:
        initialize_quest3_manager()
    return omni_quest3_manager.disconnect_quest3(device_id)

def create_ar_overlay(device_id: str, overlay_info: Dict[str, Any]) -> str:
    """Create AR overlay for Quest 3"""
    if not omni_quest3_manager:
        initialize_quest3_manager()
    return omni_quest3_manager.create_ar_overlay(device_id, overlay_info)

def get_quest3_devices() -> List[Dict[str, Any]]:
    """Get all Quest 3 devices"""
    if not omni_quest3_manager:
        initialize_quest3_manager()
    return omni_quest3_manager.get_quest3_devices()

def get_quest3_status() -> Dict[str, Any]:
    """Get Quest 3 status"""
    if not omni_quest3_manager:
        initialize_quest3_manager()
    return omni_quest3_manager.get_quest3_status()

if __name__ == "__main__":
    # Test Quest 3 manager
    print("Testing OMNI Meta Quest 3 Manager...")

    # Initialize manager
    quest3_manager = initialize_quest3_manager()
    quest3_manager.start()

    # Test device registration
    quest3_info = {
        "device_name": "My Meta Quest 3",
        "serial_number": "QUEST3-123456",
        "firmware_version": "1.0.0",
        "connection_mode": "standalone"
    }

    device_id = register_quest3(quest3_info, "test_user")
    print(f"Quest 3 registered: {device_id}")

    # Test connection
    if device_id:
        connected = connect_quest3(device_id, "standalone")
        print(f"Quest 3 connected: {connected}")

        # Test AR overlay creation
        overlay_info = {
            "overlay_type": "device_data",
            "data_source": "device_count",
            "position": [0, 0, -2],  # 2 meters in front
            "title": "OMNI Device Count"
        }

        overlay_id = create_ar_overlay(device_id, overlay_info)
        print(f"AR overlay created: {overlay_id}")

    # Show status
    status = get_quest3_status()
    print(f"Quest 3 status: {status}")

    print("\nQuest 3 Manager test completed!")