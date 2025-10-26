#!/usr/bin/env python3
"""
OMNI Edge Agent for Device Integration
Lightweight agent that runs on devices to connect them to OMNI backend
Supports MQTT, WebSocket, HTTP protocols for various device types
"""

import asyncio
import json
import time
import uuid
import ssl
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
import logging
import threading
import websockets
import paho.mqtt.client as mqtt
import requests
from pathlib import Path

@dataclass
class DeviceConfig:
    """Device configuration for edge agent"""
    device_id: str
    device_type: str
    device_name: str
    omni_gateway_url: str = "https://your-omni-platform.com"
    mqtt_broker: str = "localhost"
    mqtt_port: int = 1883
    websocket_url: str = "wss://your-omni-platform.com/ws"
    api_key: str = ""
    enable_mqtt: bool = True
    enable_websocket: bool = True
    enable_http: bool = True
    heartbeat_interval: int = 30
    reconnect_attempts: int = 5
    reconnect_delay: int = 5

@dataclass
class TelemetryData:
    """Telemetry data structure"""
    device_id: str
    timestamp: datetime
    data_type: str
    payload: Dict[str, Any]
    quality: float = 1.0

class OmniEdgeAgent:
    """Edge Agent for connecting devices to OMNI platform"""

    def __init__(self, config: DeviceConfig):
        self.config = config
        self.connected = False
        self.mqtt_client = None
        self.websocket = None
        self.telemetry_queue = asyncio.Queue()
        self.event_listeners = []

        # Device capabilities
        self.capabilities = self._detect_capabilities()

        # Background tasks
        self._running = False
        self._mqtt_task = None
        self._websocket_task = None
        self._heartbeat_task = None
        self._telemetry_task = None

        print(f"🔗 OMNI Edge Agent initialized for {config.device_name} ({config.device_type})")

    def _detect_capabilities(self) -> Dict[str, Any]:
        """Detect device capabilities"""
        capabilities = {
            "platform": os.sys.platform,
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
            "supports_websockets": True,
            "supports_mqtt": True,
            "supports_http": True,
            "device_type": self.config.device_type
        }

        # Add device-specific capabilities
        if self.config.device_type == "vr_glasses":
            capabilities.update({
                "webxr_support": True,
                "webrtc_support": True,
                "head_tracking": True,
                "hand_tracking": True
            })
        elif self.config.device_type == "iot_device":
            capabilities.update({
                "sensors": ["temperature", "humidity", "motion"],
                "actuators": ["relay", "motor"],
                "power_source": "battery"
            })
        elif self.config.device_type == "camera":
            capabilities.update({
                "streaming": True,
                "rtsp_support": True,
                "webrtc_support": True,
                "resolutions": ["1080p", "720p", "480p"]
            })

        return capabilities

    async def start(self) -> bool:
        """Start the edge agent"""
        try:
            self._running = True

            # Start MQTT client
            if self.config.enable_mqtt:
                await self._start_mqtt_client()

            # Start WebSocket connection
            if self.config.enable_websocket:
                await self._start_websocket_client()

            # Start telemetry processing
            self._telemetry_task = asyncio.create_task(self._process_telemetry())

            # Start heartbeat
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            print(f"✅ OMNI Edge Agent started for {self.config.device_name}")
            return True

        except Exception as e:
            print(f"❌ Failed to start edge agent: {e}")
            return False

    async def stop(self):
        """Stop the edge agent"""
        try:
            self._running = False

            # Stop MQTT
            if self.mqtt_client:
                self.mqtt_client.disconnect()
                self.mqtt_client = None

            # Stop WebSocket
            if self.websocket:
                await self.websocket.close()
                self.websocket = None

            # Cancel tasks
            if self._telemetry_task:
                self._telemetry_task.cancel()
            if self._heartbeat_task:
                self._heartbeat_task.cancel()

            print(f"🛑 OMNI Edge Agent stopped for {self.config.device_name}")

        except Exception as e:
            print(f"⚠️ Error stopping edge agent: {e}")

    async def _start_mqtt_client(self):
        """Start MQTT client connection"""
        try:
            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    print("✅ MQTT connected successfully")
                    self.connected = True
                    # Subscribe to device-specific topics
                    client.subscribe(f"omni/devices/{self.config.device_id}/commands")
                    client.subscribe(f"omni/devices/{self.config.device_id}/config")
                else:
                    print(f"❌ MQTT connection failed with code {rc}")

            def on_message(client, userdata, msg):
                asyncio.create_task(self._handle_mqtt_message(msg))

            def on_disconnect(client, userdata, rc):
                print("🔌 MQTT disconnected")
                self.connected = False

            # Create MQTT client
            self.mqtt_client = mqtt.Client(client_id=f"omni_edge_{self.config.device_id}")
            self.mqtt_client.on_connect = on_connect
            self.mqtt_client.on_message = on_message
            self.mqtt_client.on_disconnect = on_disconnect

            # Set up authentication if API key provided
            if self.config.api_key:
                self.mqtt_client.username_pw_set(self.config.device_id, self.config.api_key)

            # Connect to MQTT broker
            self.mqtt_client.connect_async(self.config.mqtt_broker, self.config.mqtt_port, 60)

            # Start MQTT loop in background thread
            self.mqtt_client.loop_start()

        except Exception as e:
            print(f"❌ Failed to start MQTT client: {e}")

    async def _start_websocket_client(self):
        """Start WebSocket client connection"""
        try:
            headers = {}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            uri = f"{self.config.websocket_url}/devices/{self.config.device_id}"

            self.websocket = await websockets.connect(
                uri,
                extra_headers=headers,
                ping_interval=30,
                ping_timeout=10
            )

            print("✅ WebSocket connected successfully")

            # Start WebSocket message handler
            asyncio.create_task(self._websocket_message_handler())

        except Exception as e:
            print(f"❌ Failed to start WebSocket client: {e}")

    async def _websocket_message_handler(self):
        """Handle WebSocket messages"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._handle_websocket_message(data)
                except json.JSONDecodeError:
                    print(f"⚠️ Invalid JSON received via WebSocket: {message}")
        except websockets.exceptions.ConnectionClosed:
            print("🔌 WebSocket connection closed")
            self.connected = False
        except Exception as e:
            print(f"⚠️ WebSocket message handler error: {e}")

    async def _handle_mqtt_message(self, msg):
        """Handle MQTT message"""
        try:
            payload = json.loads(msg.payload.decode())
            topic = msg.topic

            print(f"📨 MQTT message received on {topic}: {payload}")

            # Handle different message types
            if "commands" in topic:
                await self._execute_command(payload)
            elif "config" in topic:
                await self._update_config(payload)

        except Exception as e:
            print(f"⚠️ Error handling MQTT message: {e}")

    async def _handle_websocket_message(self, data: Dict[str, Any]):
        """Handle WebSocket message"""
        try:
            message_type = data.get("type", "unknown")

            if message_type == "command":
                await self._execute_command(data.get("command", {}))
            elif message_type == "config_update":
                await self._update_config(data.get("config", {}))
            elif message_type == "ping":
                # Respond to ping
                await self.send_websocket_message({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            elif message_type == "telemetry_request":
                # Send current telemetry
                await self._send_telemetry(data.get("request_id"))

        except Exception as e:
            print(f"⚠️ Error handling WebSocket message: {e}")

    async def _execute_command(self, command: Dict[str, Any]):
        """Execute command received from OMNI platform"""
        try:
            command_type = command.get("type", "unknown")
            parameters = command.get("parameters", {})

            print(f"⚡ Executing command: {command_type}")

            # Handle different command types
            if command_type == "get_telemetry":
                await self._send_telemetry()
            elif command_type == "update_config":
                await self._update_config(parameters)
            elif command_type == "restart":
                await self.restart()
            elif command_type == "calibrate":
                await self._calibrate_device(parameters)
            else:
                print(f"⚠️ Unknown command type: {command_type}")

            # Send command acknowledgment
            await self.send_mqtt_message("omni/commands/ack", {
                "command_id": command.get("id"),
                "status": "executed",
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            print(f"❌ Error executing command: {e}")

    async def _update_config(self, config: Dict[str, Any]):
        """Update device configuration"""
        try:
            print(f"🔧 Updating configuration: {config}")

            # Update local config
            for key, value in config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

            # Send confirmation
            await self.send_mqtt_message("omni/config/updated", {
                "device_id": self.config.device_id,
                "config": config,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            print(f"❌ Error updating config: {e}")

    async def _calibrate_device(self, parameters: Dict[str, Any]):
        """Calibrate device sensors/actuators"""
        try:
            calibration_type = parameters.get("type", "unknown")

            print(f"🔧 Calibrating {calibration_type}")

            # Simulate calibration process
            await asyncio.sleep(2)

            # Send calibration result
            await self.send_mqtt_message("omni/calibration/result", {
                "device_id": self.config.device_id,
                "calibration_type": calibration_type,
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            print(f"❌ Error calibrating device: {e}")

    async def _heartbeat_loop(self):
        """Send periodic heartbeat"""
        while self._running:
            try:
                if self.connected:
                    heartbeat_data = {
                        "device_id": self.config.device_id,
                        "timestamp": datetime.now().isoformat(),
                        "status": "online",
                        "uptime": time.time(),
                        "capabilities": self.capabilities
                    }

                    # Send via MQTT
                    if self.mqtt_client and self.mqtt_client.is_connected():
                        await self.send_mqtt_message("omni/heartbeat", heartbeat_data)

                    # Send via WebSocket
                    if self.websocket and not self.websocket.closed:
                        await self.send_websocket_message({
                            "type": "heartbeat",
                            "data": heartbeat_data
                        })

                await asyncio.sleep(self.config.heartbeat_interval)

            except Exception as e:
                print(f"⚠️ Heartbeat error: {e}")
                await asyncio.sleep(self.config.heartbeat_interval)

    async def _process_telemetry(self):
        """Process telemetry data queue"""
        while self._running:
            try:
                # Get telemetry from queue
                telemetry = await self.telemetry_queue.get()

                # Send to OMNI platform
                await self._send_telemetry_data(telemetry)

                self.telemetry_queue.task_done()

            except Exception as e:
                print(f"⚠️ Telemetry processing error: {e}")
                await asyncio.sleep(1)

    async def _send_telemetry_data(self, telemetry: TelemetryData):
        """Send telemetry data to OMNI platform"""
        try:
            # Send via MQTT (preferred for telemetry)
            if self.mqtt_client and self.mqtt_client.is_connected():
                topic = f"omni/telemetry/{self.config.device_id}"
                payload = {
                    "device_id": telemetry.device_id,
                    "timestamp": telemetry.timestamp.isoformat(),
                    "data_type": telemetry.data_type,
                    "payload": telemetry.payload,
                    "quality": telemetry.quality
                }

                await self.send_mqtt_message(topic, payload)

            # Also send via WebSocket for real-time updates
            if self.websocket and not self.websocket.closed:
                await self.send_websocket_message({
                    "type": "telemetry",
                    "data": payload
                })

        except Exception as e:
            print(f"❌ Error sending telemetry: {e}")

    async def send_mqtt_message(self, topic: str, payload: Dict[str, Any]):
        """Send MQTT message"""
        if self.mqtt_client and self.mqtt_client.is_connected():
            try:
                message = json.dumps(payload)
                self.mqtt_client.publish(topic, message, qos=1)
            except Exception as e:
                print(f"❌ Error sending MQTT message: {e}")

    async def send_websocket_message(self, data: Dict[str, Any]):
        """Send WebSocket message"""
        if self.websocket and not self.websocket.closed:
            try:
                message = json.dumps(data)
                await self.websocket.send(message)
            except Exception as e:
                print(f"❌ Error sending WebSocket message: {e}")

    def send_telemetry(self, data_type: str, payload: Dict[str, Any], quality: float = 1.0):
        """Send telemetry data (public method)"""
        try:
            telemetry = TelemetryData(
                device_id=self.config.device_id,
                timestamp=datetime.now(),
                data_type=data_type,
                payload=payload,
                quality=quality
            )

            # Add to queue for async processing
            asyncio.create_task(self.telemetry_queue.put(telemetry))

        except Exception as e:
            print(f"❌ Error queuing telemetry: {e}")

    def add_event_listener(self, listener: Callable[[str, Dict[str, Any]], None]):
        """Add event listener"""
        self.event_listeners.append(listener)

    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit event to listeners"""
        for listener in self.event_listeners:
            try:
                listener(event_type, data)
            except Exception as e:
                print(f"⚠️ Event listener error: {e}")

    async def restart(self):
        """Restart the edge agent"""
        print("🔄 Restarting OMNI Edge Agent...")
        await self.stop()
        await asyncio.sleep(2)
        await self.start()

    def get_status(self) -> Dict[str, Any]:
        """Get edge agent status"""
        return {
            "device_id": self.config.device_id,
            "device_name": self.config.device_name,
            "device_type": self.config.device_type,
            "connected": self.connected,
            "mqtt_connected": self.mqtt_client.is_connected() if self.mqtt_client else False,
            "websocket_connected": not self.websocket.closed if self.websocket else False,
            "capabilities": self.capabilities,
            "uptime": time.time(),
            "last_heartbeat": datetime.now().isoformat()
        }

# Factory functions for different device types
def create_vr_edge_agent(device_name: str, omni_gateway_url: str = "https://localhost:3090") -> OmniEdgeAgent:
    """Create edge agent for VR glasses"""
    config = DeviceConfig(
        device_id=str(uuid.uuid4()),
        device_type="vr_glasses",
        device_name=device_name,
        omni_gateway_url=omni_gateway_url,
        websocket_url=f"ws://{omni_gateway_url.replace('https://', '').replace('http://', '')}/vr/websocket"
    )
    return OmniEdgeAgent(config)

def create_iot_edge_agent(device_name: str, sensors: List[str] = None, omni_gateway_url: str = "https://localhost:3090") -> OmniEdgeAgent:
    """Create edge agent for IoT device"""
    config = DeviceConfig(
        device_id=str(uuid.uuid4()),
        device_type="iot_device",
        device_name=device_name,
        omni_gateway_url=omni_gateway_url,
        mqtt_broker="localhost",  # Local MQTT broker
        websocket_url=f"ws://{omni_gateway_url.replace('https://', '').replace('http://', '')}/ws"
    )
    return OmniEdgeAgent(config)

def create_camera_edge_agent(device_name: str, rtsp_url: str, omni_gateway_url: str = "https://localhost:3090") -> OmniEdgeAgent:
    """Create edge agent for camera"""
    config = DeviceConfig(
        device_id=str(uuid.uuid4()),
        device_type="camera",
        device_name=device_name,
        omni_gateway_url=omni_gateway_url,
        websocket_url=f"ws://{omni_gateway_url.replace('https://', '').replace('http://', '')}/camera/websocket"
    )

    agent = OmniEdgeAgent(config)
    agent.rtsp_url = rtsp_url  # Add RTSP URL for camera
    return agent

async def main():
    """Main function for testing edge agent"""
    print("🧪 Testing OMNI Edge Agent...")

    # Create VR edge agent
    vr_agent = create_vr_edge_agent("Test Oculus Quest")

    try:
        # Start agent
        await vr_agent.start()

        # Send some test telemetry
        for i in range(5):
            vr_agent.send_telemetry("head_position", {
                "x": i * 0.1,
                "y": 0.5,
                "z": -1.0,
                "rotation": {"x": 0, "y": i * 10, "z": 0}
            })
            await asyncio.sleep(1)

        # Get status
        status = vr_agent.get_status()
        print(f"📊 Agent Status: {status}")

        # Keep running for a bit
        await asyncio.sleep(10)

    finally:
        await vr_agent.stop()

    print("✅ Edge Agent test completed!")

if __name__ == "__main__":
    asyncio.run(main())