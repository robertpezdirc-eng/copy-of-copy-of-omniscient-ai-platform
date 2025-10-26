#!/usr/bin/env python3
"""
OMNI VR Device Connection Manager
Advanced VR device connection and communication management
Handles Oculus, HTC Vive, and other VR device connections with Omni platform
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
import requests

@dataclass
class VRDeviceConnection:
    """VR device connection information"""
    connection_id: str
    device_id: str
    device_type: str
    websocket: Optional[websockets.WebSocketServerProtocol]
    connected_at: datetime
    last_ping: datetime
    status: str = "connected"
    connection_quality: float = 1.0
    bandwidth_usage: float = 0.0

@dataclass
class VRDeviceCapabilities:
    """VR device capabilities"""
    webxr_support: bool = True
    hand_tracking: bool = False
    eye_tracking: bool = False
    face_tracking: bool = False
    body_tracking: bool = False
    haptic_feedback: bool = False
    spatial_audio: bool = True
    refresh_rate: int = 90
    resolution_width: int = 1920
    resolution_height: int = 1080

class OmniVRDeviceManager:
    """VR Device Connection Manager for OMNI platform"""

    def __init__(self, server_url: str = "ws://localhost:3090/vr/websocket"):
        self.server_url = server_url
        self.connections: Dict[str, VRDeviceConnection] = {}
        self.device_capabilities: Dict[str, VRDeviceCapabilities] = {}
        self.websocket_server = None
        self.connection_handlers = {}
        self.device_event_listeners = []

        # Connection settings
        self.config = {
            "max_connections": 100,
            "ping_interval": 30,  # seconds
            "connection_timeout": 300,  # seconds
            "reconnect_attempts": 3,
            "reconnect_delay": 5,  # seconds
            "enable_auto_reconnect": True,
            "enable_connection_monitoring": True
        }

        # Start background services
        self._start_background_services()

        print("🔗 OMNI VR Device Manager initialized")

    def _start_background_services(self):
        """Start background services for device management"""
        # Connection monitoring thread
        monitor_thread = threading.Thread(target=self._connection_monitor, daemon=True)
        monitor_thread.start()

        # WebSocket server thread
        ws_thread = threading.Thread(target=self._start_websocket_server, daemon=True)
        ws_thread.start()

    def _start_websocket_server(self):
        """Start WebSocket server for VR device connections"""
        try:
            # This would start a WebSocket server for VR devices
            # For now, we'll simulate the functionality
            print("🔗 VR Device WebSocket server started")
        except Exception as e:
            print(f"⚠️ Failed to start VR WebSocket server: {e}")

    def _connection_monitor(self):
        """Monitor VR device connections"""
        while True:
            try:
                current_time = datetime.now()
                inactive_connections = []

                for conn_id, connection in self.connections.items():
                    # Check for inactive connections
                    if (current_time - connection.last_ping).seconds > self.config["connection_timeout"]:
                        connection.status = "inactive"
                        inactive_connections.append(conn_id)

                    # Check connection quality
                    if connection.status == "connected":
                        # Simulate connection quality monitoring
                        connection.connection_quality = min(1.0, connection.connection_quality + 0.1)

                # Clean up inactive connections
                for conn_id in inactive_connections:
                    if (current_time - self.connections[conn_id].last_ping).seconds > self.config["connection_timeout"] * 2:
                        self._disconnect_device(conn_id)
                        print(f"🗑️ Removed inactive VR connection: {conn_id}")

                time.sleep(self.config["ping_interval"])

            except Exception as e:
                print(f"⚠️ Connection monitor error: {e}")
                time.sleep(self.config["ping_interval"])

    def register_device(self, device_info: Dict[str, Any], user_id: str) -> str:
        """Register a new VR device"""
        try:
            device_id = str(uuid.uuid4())
            connection_id = str(uuid.uuid4())

            # Determine device type and capabilities
            device_type = device_info.get('device_type', 'unknown')
            capabilities = self._detect_device_capabilities(device_type, device_info)

            # Create connection
            connection = VRDeviceConnection(
                connection_id=connection_id,
                device_id=device_id,
                device_type=device_type,
                websocket=None,  # Will be set when WebSocket connects
                connected_at=datetime.now(),
                last_ping=datetime.now()
            )

            self.connections[connection_id] = connection
            self.device_capabilities[device_id] = capabilities

            print(f"📱 VR Device registered: {device_info.get('device_name', 'Unknown')} ({device_type})")
            return device_id

        except Exception as e:
            print(f"❌ Failed to register VR device: {e}")
            return None

    def _detect_device_capabilities(self, device_type: str, device_info: Dict[str, Any]) -> VRDeviceCapabilities:
        """Detect VR device capabilities based on type"""
        capabilities = VRDeviceCapabilities()

        device_type_lower = device_type.lower()

        if "oculus" in device_type_lower or "quest" in device_type_lower:
            capabilities.hand_tracking = device_info.get('hand_tracking', True)
            capabilities.eye_tracking = device_info.get('eye_tracking', False)
            capabilities.face_tracking = device_info.get('face_tracking', False)
            capabilities.haptic_feedback = True
            capabilities.refresh_rate = 90
            capabilities.resolution_width = 1920
            capabilities.resolution_height = 1080

        elif "vive" in device_type_lower:
            capabilities.hand_tracking = True
            capabilities.body_tracking = device_info.get('body_tracking', False)
            capabilities.haptic_feedback = True
            capabilities.refresh_rate = 90
            capabilities.resolution_width = 2160
            capabilities.resolution_height = 1200

        elif "mobile" in device_type_lower:
            capabilities.hand_tracking = device_info.get('hand_tracking', False)
            capabilities.refresh_rate = 60
            capabilities.resolution_width = device_info.get('screen_width', 1920)
            capabilities.resolution_height = device_info.get('screen_height', 1080)

        return capabilities

    def connect_device_websocket(self, device_id: str, websocket) -> bool:
        """Connect VR device via WebSocket"""
        try:
            # Find connection by device_id
            connection = None
            for conn in self.connections.values():
                if conn.device_id == device_id and conn.websocket is None:
                    connection = conn
                    break

            if not connection:
                return False

            connection.websocket = websocket
            connection.status = "connected"
            connection.last_ping = datetime.now()

            # Send welcome message
            welcome_message = {
                "type": "welcome",
                "device_id": device_id,
                "connection_id": connection.connection_id,
                "timestamp": datetime.now().isoformat(),
                "capabilities": self.device_capabilities[device_id].__dict__
            }

            websocket.send(json.dumps(welcome_message))

            print(f"🔗 VR Device WebSocket connected: {device_id}")
            return True

        except Exception as e:
            print(f"❌ Failed to connect VR device WebSocket: {e}")
            return False

    def handle_device_message(self, connection_id: str, message: str) -> bool:
        """Handle message from VR device"""
        try:
            data = json.loads(message)
            connection = self.connections.get(connection_id)

            if not connection:
                return False

            # Update last ping
            connection.last_ping = datetime.now()

            # Handle different message types
            message_type = data.get('type', 'unknown')

            if message_type == 'heartbeat':
                self._handle_heartbeat(connection_id, data)
            elif message_type == 'device_info':
                self._handle_device_info(connection_id, data)
            elif message_type == 'session_event':
                self._handle_session_event(connection_id, data)
            elif message_type == 'error':
                self._handle_device_error(connection_id, data)
            else:
                print(f"🎮 Unknown VR device message type: {message_type}")

            return True

        except Exception as e:
            print(f"❌ Failed to handle VR device message: {e}")
            return False

    def _handle_heartbeat(self, connection_id: str, data: Dict[str, Any]):
        """Handle heartbeat from VR device"""
        connection = self.connections.get(connection_id)
        if connection:
            connection.last_ping = datetime.now()
            connection.connection_quality = data.get('connection_quality', 1.0)
            connection.bandwidth_usage = data.get('bandwidth_usage', 0.0)

    def _handle_device_info(self, connection_id: str, data: Dict[str, Any]):
        """Handle device info update"""
        connection = self.connections.get(connection_id)
        if connection:
            # Update device capabilities if provided
            device_info = data.get('device_info', {})
            if device_info:
                device_id = connection.device_id
                if device_id in self.device_capabilities:
                    # Update capabilities
                    for key, value in device_info.items():
                        if hasattr(self.device_capabilities[device_id], key):
                            setattr(self.device_capabilities[device_id], key, value)

    def _handle_session_event(self, connection_id: str, data: Dict[str, Any]):
        """Handle VR session events"""
        connection = self.connections.get(connection_id)
        if connection:
            event_type = data.get('event_type', 'unknown')
            session_data = data.get('session_data', {})

            # Notify event listeners
            for listener in self.device_event_listeners:
                try:
                    listener(connection.device_id, event_type, session_data)
                except Exception as e:
                    print(f"⚠️ Device event listener error: {e}")

    def _handle_device_error(self, connection_id: str, data: Dict[str, Any]):
        """Handle device errors"""
        connection = self.connections.get(connection_id)
        if connection:
            error_message = data.get('error', 'Unknown error')
            print(f"🚨 VR Device Error [{connection.device_id}]: {error_message}")

            # Notify error handlers
            if connection_id in self.connection_handlers:
                try:
                    self.connection_handlers[connection_id](connection.device_id, error_message)
                except Exception as e:
                    print(f"⚠️ Connection handler error: {e}")

    def _disconnect_device(self, connection_id: str):
        """Disconnect VR device"""
        try:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                connection.status = "disconnected"

                # Close WebSocket if exists
                if connection.websocket:
                    asyncio.create_task(connection.websocket.close())

                # Remove from active connections
                del self.connections[connection_id]

                print(f"🔌 VR Device disconnected: {connection.device_id}")

        except Exception as e:
            print(f"⚠️ Error disconnecting VR device: {e}")

    def send_to_device(self, device_id: str, message: Dict[str, Any]) -> bool:
        """Send message to VR device"""
        try:
            # Find connection by device_id
            connection = None
            for conn in self.connections.values():
                if conn.device_id == device_id and conn.status == "connected":
                    connection = conn
                    break

            if not connection or not connection.websocket:
                return False

            # Send message
            message_json = json.dumps(message)
            asyncio.create_task(connection.websocket.send(message_json))

            return True

        except Exception as e:
            print(f"❌ Failed to send message to VR device: {e}")
            return False

    def broadcast_to_devices(self, message: Dict[str, Any], device_type_filter: str = None) -> int:
        """Broadcast message to all connected VR devices"""
        sent_count = 0

        try:
            for connection in self.connections.values():
                if connection.status == "connected":
                    # Apply device type filter if specified
                    if device_type_filter and connection.device_type != device_type_filter:
                        continue

                    if self.send_to_device(connection.device_id, message):
                        sent_count += 1

            return sent_count

        except Exception as e:
            print(f"❌ Failed to broadcast to VR devices: {e}")
            return sent_count

    def get_device_list(self) -> List[Dict[str, Any]]:
        """Get list of connected VR devices"""
        devices = []

        for connection in self.connections.values():
            device_info = {
                "connection_id": connection.connection_id,
                "device_id": connection.device_id,
                "device_type": connection.device_type,
                "status": connection.status,
                "connected_at": connection.connected_at.isoformat(),
                "last_ping": connection.last_ping.isoformat(),
                "connection_quality": connection.connection_quality,
                "bandwidth_usage": connection.bandwidth_usage
            }

            # Add capabilities if available
            if connection.device_id in self.device_capabilities:
                device_info["capabilities"] = self.device_capabilities[connection.device_id].__dict__

            devices.append(device_info)

        return devices

    def get_device_capabilities(self, device_id: str) -> Dict[str, Any]:
        """Get VR device capabilities"""
        if device_id in self.device_capabilities:
            return self.device_capabilities[device_id].__dict__
        return {"error": "Device not found"}

    def add_device_event_listener(self, listener: Callable[[str, str, Dict[str, Any]], None]):
        """Add device event listener"""
        self.device_event_listeners.append(listener)

    def remove_device_event_listener(self, listener: Callable[[str, str, Dict[str, Any]], None]):
        """Remove device event listener"""
        if listener in self.device_event_listeners:
            self.device_event_listeners.remove(listener)

    def add_connection_handler(self, connection_id: str, handler: Callable[[str, str], None]):
        """Add connection error handler"""
        self.connection_handlers[connection_id] = handler

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        total_connections = len(self.connections)
        active_connections = len([c for c in self.connections.values() if c.status == "connected"])
        inactive_connections = len([c for c in self.connections.values() if c.status == "inactive"])

        # Calculate average connection quality
        avg_quality = 0.0
        if active_connections > 0:
            quality_sum = sum(c.connection_quality for c in self.connections.values() if c.status == "connected")
            avg_quality = quality_sum / active_connections

        return {
            "total_connections": total_connections,
            "active_connections": active_connections,
            "inactive_connections": inactive_connections,
            "average_connection_quality": round(avg_quality, 2),
            "websocket_server_running": self.websocket_server is not None,
            "last_updated": datetime.now().isoformat()
        }

# Global VR device manager instance
omni_vr_device_manager = None

def initialize_vr_device_manager(server_url: str = "ws://localhost:3090/vr/websocket") -> OmniVRDeviceManager:
    """Initialize VR device manager"""
    global omni_vr_device_manager
    omni_vr_device_manager = OmniVRDeviceManager(server_url)
    return omni_vr_device_manager

def get_vr_device_manager() -> OmniVRDeviceManager:
    """Get global VR device manager instance"""
    return omni_vr_device_manager

# Device manager API functions
def register_vr_device(device_info: Dict[str, Any], user_id: str) -> str:
    """Register VR device"""
    if omni_vr_device_manager:
        return omni_vr_device_manager.register_device(device_info, user_id)
    return None

def get_vr_devices() -> List[Dict[str, Any]]:
    """Get list of VR devices"""
    if omni_vr_device_manager:
        return omni_vr_device_manager.get_device_list()
    return []

def get_vr_device_capabilities(device_id: str) -> Dict[str, Any]:
    """Get VR device capabilities"""
    if omni_vr_device_manager:
        return omni_vr_device_manager.get_device_capabilities(device_id)
    return {}

def send_to_vr_device(device_id: str, message: Dict[str, Any]) -> bool:
    """Send message to VR device"""
    if omni_vr_device_manager:
        return omni_vr_device_manager.send_to_device(device_id, message)
    return False

def get_vr_connection_stats() -> Dict[str, Any]:
    """Get VR connection statistics"""
    if omni_vr_device_manager:
        return omni_vr_device_manager.get_connection_stats()
    return {}

if __name__ == "__main__":
    # Test VR device manager
    print("🧪 Testing OMNI VR Device Manager...")

    # Initialize device manager
    device_manager = initialize_vr_device_manager()

    # Test device registration
    device_info = {
        "device_type": "oculus_quest",
        "device_name": "Test Oculus Quest 2",
        "capabilities": {
            "hand_tracking": True,
            "eye_tracking": False,
            "screen_width": 1920,
            "screen_height": 1080
        }
    }

    device_id = register_vr_device(device_info, "test_user")
    print(f"✅ VR Device registered: {device_id}")

    # Test capabilities detection
    capabilities = get_vr_device_capabilities(device_id)
    print(f"✅ Device capabilities: {capabilities}")

    # Test connection stats
    stats = get_vr_connection_stats()
    print(f"✅ Connection stats: {stats}")

    print("\n✅ OMNI VR Device Manager test completed!")