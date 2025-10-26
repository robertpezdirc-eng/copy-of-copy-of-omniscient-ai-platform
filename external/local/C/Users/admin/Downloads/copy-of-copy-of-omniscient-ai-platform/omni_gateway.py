#!/usr/bin/env python3
"""
OMNI Gateway - Advanced Device Communication Gateway
Comprehensive gateway supporting MQTT, WebSocket, HTTP, and WebRTC protocols
Handles device connections, message routing, and protocol translation
"""

import asyncio
import json
import time
import ssl
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
import logging
import threading
import websockets
import paho.mqtt.client as mqtt
import requests
from pathlib import Path
from enum import Enum

class ProtocolType(Enum):
    """Supported communication protocols"""
    MQTT = "mqtt"
    WEBSOCKET = "websocket"
    HTTP = "http"
    WEBRTC = "webrtc"
    BLE = "ble"
    TCP = "tcp"

class DeviceState(Enum):
    """Device connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATING = "authenticating"
    AUTHORIZED = "authorized"
    ERROR = "error"

@dataclass
class DeviceConnection:
    """Device connection information"""
    device_id: str
    device_type: str
    protocol: ProtocolType
    connection_id: str
    connected_at: datetime
    last_seen: datetime
    state: DeviceState
    capabilities: Dict[str, Any]
    subscriptions: List[str] = field(default_factory=list)
    websocket = None
    mqtt_client = None

@dataclass
class Message:
    """Message structure for routing"""
    message_id: str
    from_device: str
    to_device: str
    protocol: ProtocolType
    message_type: str
    payload: Dict[str, Any]
    timestamp: datetime
    priority: int = 1
    requires_ack: bool = False

class OmniGateway:
    """Main OMNI Gateway for device communications"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = {
            "host": "0.0.0.0",
            "port": 3090,
            "mqtt_host": "localhost",
            "mqtt_port": 1883,
            "websocket_port": 3091,
            "webrtc_port": 3092,
            "enable_tls": False,
            "cert_file": "cert.pem",
            "key_file": "key.pem",
            "max_connections": 1000,
            "heartbeat_interval": 30,
            "message_timeout": 60,
            "enable_message_logging": True,
            "enable_protocol_translation": True,
            **(config or {})
        }

        # Connection management
        self.connections: Dict[str, DeviceConnection] = {}
        self.message_queue = asyncio.Queue()
        self.message_handlers = {}
        self.protocol_translators = {}

        # MQTT setup
        self.mqtt_client = None
        self.mqtt_topics = set()

        # WebSocket server
        self.websocket_server = None

        # HTTP server
        self.http_server = None

        # Background tasks
        self._running = False
        self._message_processor_task = None
        self._connection_monitor_task = None

        # Statistics
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_processed": 0,
            "messages_failed": 0,
            "bytes_transferred": 0,
            "uptime": 0
        }

        print("🌐 OMNI Gateway initialized")

    async def start(self) -> bool:
        """Start the OMNI Gateway"""
        try:
            self._running = True
            self.stats["start_time"] = time.time()

            # Start MQTT broker connection
            await self._start_mqtt_broker()

            # Start WebSocket server
            await self._start_websocket_server()

            # Start HTTP server
            await self._start_http_server()

            # Start message processor
            self._message_processor_task = asyncio.create_task(self._process_messages())

            # Start connection monitor
            self._connection_monitor_task = asyncio.create_task(self._monitor_connections())

            # Register default message handlers
            self._register_default_handlers()

            print(f"✅ OMNI Gateway started on {self.config['host']}:{self.config['port']}")
            return True

        except Exception as e:
            print(f"❌ Failed to start OMNI Gateway: {e}")
            return False

    async def stop(self):
        """Stop the OMNI Gateway"""
        try:
            self._running = False

            # Stop MQTT
            if self.mqtt_client:
                self.mqtt_client.disconnect()
                self.mqtt_client.loop_stop()

            # Stop WebSocket server
            if self.websocket_server:
                self.websocket_server.close()
                await self.websocket_server.wait_closed()

            # Stop HTTP server
            if self.http_server:
                self.http_server.close()

            # Cancel background tasks
            if self._message_processor_task:
                self._message_processor_task.cancel()
            if self._connection_monitor_task:
                self._connection_monitor_task.cancel()

            print("🛑 OMNI Gateway stopped")

        except Exception as e:
            print(f"⚠️ Error stopping gateway: {e}")

    async def _start_mqtt_broker(self):
        """Start MQTT broker connection"""
        try:
            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    print("✅ MQTT broker connected")
                    # Subscribe to all OMNI topics
                    client.subscribe("omni/#")
                    client.subscribe("devices/#")
                    client.subscribe("vr/#")
                    client.subscribe("iot/#")
                else:
                    print(f"❌ MQTT connection failed with code {rc}")

            def on_message(client, userdata, msg):
                asyncio.create_task(self._handle_mqtt_message(msg))

            def on_disconnect(client, userdata, rc):
                print("🔌 MQTT broker disconnected")

            # Create MQTT client
            self.mqtt_client = mqtt.Client(client_id="omni_gateway")
            self.mqtt_client.on_connect = on_connect
            self.mqtt_client.on_message = on_message
            self.mqtt_client.on_disconnect = on_disconnect

            # Connect to MQTT broker
            self.mqtt_client.connect_async(self.config["mqtt_host"], self.config["mqtt_port"], 60)
            self.mqtt_client.loop_start()

        except Exception as e:
            print(f"❌ Failed to start MQTT broker: {e}")

    async def _start_websocket_server(self):
        """Start WebSocket server"""
        try:
            async def websocket_handler(websocket, path):
                await self._handle_websocket_connection(websocket, path)

            # Start WebSocket server
            self.websocket_server = await websockets.serve(
                websocket_handler,
                self.config["host"],
                self.config["websocket_port"],
                ping_interval=30,
                ping_timeout=10
            )

            print(f"✅ WebSocket server started on port {self.config['websocket_port']}")

        except Exception as e:
            print(f"❌ Failed to start WebSocket server: {e}")

    async def _start_http_server(self):
        """Start HTTP server for REST API"""
        try:
            from aiohttp import web

            async def health_check(request):
                return web.json_response({
                    "status": "healthy",
                    "service": "omni_gateway",
                    "timestamp": datetime.now().isoformat(),
                    "stats": self.stats
                })

            async def device_register(request):
                try:
                    data = await request.json()
                    device_id = await self.register_device(data)
                    return web.json_response({"device_id": device_id, "status": "registered"})
                except Exception as e:
                    return web.json_response({"error": str(e)}, status=400)

            async def send_message(request):
                try:
                    data = await request.json()
                    message_id = await self.route_message(data)
                    return web.json_response({"message_id": message_id, "status": "sent"})
                except Exception as e:
                    return web.json_response({"error": str(e)}, status=400)

            # Create web application
            app = web.Application()
            app.router.add_get('/health', health_check)
            app.router.add_post('/devices/register', device_register)
            app.router.add_post('/messages/send', send_message)

            # Start HTTP server
            runner = web.AppRunner(app)
            await runner.setup()
            self.http_server = web.TCPSite(runner, self.config["host"], self.config["port"])
            await self.http_server.start()

            print(f"✅ HTTP server started on port {self.config['port']}")

        except Exception as e:
            print(f"❌ Failed to start HTTP server: {e}")

    async def _handle_websocket_connection(self, websocket, path):
        """Handle WebSocket connection"""
        connection_id = str(uuid.uuid4())
        device_id = None

        try:
            print(f"🔗 WebSocket connection established: {connection_id}")

            # Handle authentication
            try:
                auth_message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                auth_data = json.loads(auth_message)

                if auth_data.get("type") == "authenticate":
                    device_id = auth_data.get("device_id")
                    api_key = auth_data.get("api_key")

                    if await self.authenticate_device(device_id, api_key):
                        # Create device connection
                        connection = DeviceConnection(
                            device_id=device_id,
                            device_type=auth_data.get("device_type", "unknown"),
                            protocol=ProtocolType.WEBSOCKET,
                            connection_id=connection_id,
                            connected_at=datetime.now(),
                            last_seen=datetime.now(),
                            state=DeviceState.AUTHORIZED,
                            capabilities=auth_data.get("capabilities", {}),
                            websocket=websocket
                        )

                        self.connections[connection_id] = connection
                        self.stats["total_connections"] += 1
                        self.stats["active_connections"] += 1

                        # Send welcome message
                        await websocket.send(json.dumps({
                            "type": "authenticated",
                            "connection_id": connection_id,
                            "timestamp": datetime.now().isoformat()
                        }))

                        print(f"✅ Device authenticated: {device_id}")
                    else:
                        await websocket.send(json.dumps({
                            "type": "authentication_failed",
                            "error": "Invalid credentials"
                        }))
                        return

            except asyncio.TimeoutError:
                await websocket.send(json.dumps({
                    "type": "authentication_timeout"
                }))
                return
            except Exception as e:
                print(f"⚠️ WebSocket authentication error: {e}")
                return

            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_websocket_message(connection_id, data)
                except json.JSONDecodeError:
                    print(f"⚠️ Invalid JSON from WebSocket {connection_id}")
                except Exception as e:
                    print(f"⚠️ WebSocket message handling error: {e}")

        except websockets.exceptions.ConnectionClosed:
            print(f"🔌 WebSocket connection closed: {connection_id}")
        except Exception as e:
            print(f"⚠️ WebSocket connection error: {e}")
        finally:
            # Clean up connection
            if connection_id in self.connections:
                self.connections[connection_id].state = DeviceState.DISCONNECTED
                self.stats["active_connections"] -= 1
                del self.connections[connection_id]

    async def _handle_websocket_message(self, connection_id: str, data: Dict[str, Any]):
        """Handle WebSocket message"""
        try:
            connection = self.connections.get(connection_id)
            if not connection:
                return

            # Update last seen
            connection.last_seen = datetime.now()

            message_type = data.get("type", "unknown")

            if message_type == "subscribe":
                await self._handle_subscription(connection_id, data)
            elif message_type == "unsubscribe":
                await self._handle_unsubscription(connection_id, data)
            elif message_type == "message":
                await self._handle_device_message(connection_id, data)
            elif message_type == "heartbeat":
                await self._handle_heartbeat(connection_id)
            else:
                print(f"⚠️ Unknown WebSocket message type: {message_type}")

        except Exception as e:
            print(f"❌ Error handling WebSocket message: {e}")

    async def _handle_mqtt_message(self, msg):
        """Handle MQTT message"""
        try:
            payload = json.loads(msg.payload.decode())
            topic = msg.topic

            print(f"📨 MQTT message received on {topic}")

            # Route message to appropriate devices
            await self._route_mqtt_message(topic, payload)

        except Exception as e:
            print(f"❌ Error handling MQTT message: {e}")

    async def _handle_subscription(self, connection_id: str, data: Dict[str, Any]):
        """Handle topic subscription"""
        connection = self.connections.get(connection_id)
        if connection:
            topics = data.get("topics", [])
            connection.subscriptions.extend(topics)

            # Subscribe to MQTT topics if needed
            if self.mqtt_client and self.mqtt_client.is_connected():
                for topic in topics:
                    mqtt_topic = f"omni/{topic}"
                    self.mqtt_client.subscribe(mqtt_topic)
                    self.mqtt_topics.add(mqtt_topic)

    async def _handle_unsubscription(self, connection_id: str, data: Dict[str, Any]):
        """Handle topic unsubscription"""
        connection = self.connections.get(connection_id)
        if connection:
            topics = data.get("topics", [])
            connection.subscriptions = [t for t in connection.subscriptions if t not in topics]

    async def _handle_device_message(self, connection_id: str, data: Dict[str, Any]):
        """Handle message from device"""
        try:
            connection = self.connections.get(connection_id)
            if not connection:
                return

            # Create message object
            message = Message(
                message_id=str(uuid.uuid4()),
                from_device=connection.device_id,
                to_device=data.get("to", "broadcast"),
                protocol=ProtocolType.WEBSOCKET,
                message_type=data.get("message_type", "data"),
                payload=data.get("payload", {}),
                timestamp=datetime.now(),
                priority=data.get("priority", 1),
                requires_ack=data.get("requires_ack", False)
            )

            # Add to message queue for processing
            await self.message_queue.put(message)

        except Exception as e:
            print(f"❌ Error handling device message: {e}")

    async def _handle_heartbeat(self, connection_id: str):
        """Handle heartbeat from device"""
        connection = self.connections.get(connection_id)
        if connection:
            connection.last_seen = datetime.now()

    async def _process_messages(self):
        """Process messages from queue"""
        while self._running:
            try:
                # Get message from queue
                message = await self.message_queue.get()

                # Process message
                await self._route_message_to_destination(message)

                self.message_queue.task_done()
                self.stats["messages_processed"] += 1

            except Exception as e:
                print(f"❌ Message processing error: {e}")
                self.stats["messages_failed"] += 1
                await asyncio.sleep(1)

    async def _route_message_to_destination(self, message: Message):
        """Route message to destination device(s)"""
        try:
            if message.to_device == "broadcast":
                # Broadcast to all connected devices
                await self._broadcast_message(message)
            else:
                # Send to specific device
                await self._send_to_device(message.to_device, message)

        except Exception as e:
            print(f"❌ Error routing message: {e}")

    async def _broadcast_message(self, message: Message):
        """Broadcast message to all connected devices"""
        for connection in self.connections.values():
            if connection.state == DeviceState.AUTHORIZED:
                try:
                    if connection.protocol == ProtocolType.WEBSOCKET and connection.websocket:
                        await connection.websocket.send(json.dumps({
                            "type": "message",
                            "from": message.from_device,
                            "message_type": message.message_type,
                            "payload": message.payload,
                            "timestamp": message.timestamp.isoformat()
                        }))
                    elif connection.protocol == ProtocolType.MQTT and connection.mqtt_client:
                        topic = f"omni/devices/{connection.device_id}/messages"
                        await self._send_mqtt_message(topic, message.payload)

                except Exception as e:
                    print(f"⚠️ Error broadcasting to device {connection.device_id}: {e}")

    async def _send_to_device(self, device_id: str, message: Message):
        """Send message to specific device"""
        # Find device connection
        target_connection = None
        for connection in self.connections.values():
            if connection.device_id == device_id and connection.state == DeviceState.AUTHORIZED:
                target_connection = connection
                break

        if not target_connection:
            print(f"⚠️ Device not found or not authorized: {device_id}")
            return

        try:
            if target_connection.protocol == ProtocolType.WEBSOCKET and target_connection.websocket:
                await target_connection.websocket.send(json.dumps({
                    "type": "message",
                    "from": message.from_device,
                    "message_type": message.message_type,
                    "payload": message.payload,
                    "timestamp": message.timestamp.isoformat()
                }))
            elif target_connection.protocol == ProtocolType.MQTT and target_connection.mqtt_client:
                topic = f"omni/devices/{device_id}/messages"
                await self._send_mqtt_message(topic, message.payload)

        except Exception as e:
            print(f"❌ Error sending to device {device_id}: {e}")

    async def _send_mqtt_message(self, topic: str, payload: Dict[str, Any]):
        """Send MQTT message"""
        if self.mqtt_client and self.mqtt_client.is_connected():
            try:
                message = json.dumps(payload)
                self.mqtt_client.publish(topic, message, qos=1)
            except Exception as e:
                print(f"❌ Error sending MQTT message: {e}")

    async def _monitor_connections(self):
        """Monitor device connections"""
        while self._running:
            try:
                current_time = datetime.now()
                inactive_connections = []

                for connection_id, connection in self.connections.items():
                    # Check for inactive connections
                    if (current_time - connection.last_seen).seconds > self.config["heartbeat_interval"] * 3:
                        connection.state = DeviceState.DISCONNECTED
                        inactive_connections.append(connection_id)

                # Clean up inactive connections
                for connection_id in inactive_connections:
                    if connection_id in self.connections:
                        del self.connections[connection_id]
                        self.stats["active_connections"] -= 1
                        print(f"🗑️ Removed inactive connection: {connection_id}")

                # Update uptime
                if "start_time" in self.stats:
                    self.stats["uptime"] = time.time() - self.stats["start_time"]

                await asyncio.sleep(self.config["heartbeat_interval"])

            except Exception as e:
                print(f"⚠️ Connection monitoring error: {e}")
                await asyncio.sleep(self.config["heartbeat_interval"])

    async def register_device(self, device_info: Dict[str, Any]) -> str:
        """Register a new device"""
        try:
            device_id = device_info.get("device_id") or str(uuid.uuid4())

            # Create device connection (will be updated when device connects)
            connection = DeviceConnection(
                device_id=device_id,
                device_type=device_info.get("device_type", "unknown"),
                protocol=ProtocolType.HTTP,  # Initial registration via HTTP
                connection_id=str(uuid.uuid4()),
                connected_at=datetime.now(),
                last_seen=datetime.now(),
                state=DeviceState.REGISTERED,
                capabilities=device_info.get("capabilities", {})
            )

            self.connections[connection.connection_id] = connection

            print(f"📱 Device registered: {device_id}")
            return device_id

        except Exception as e:
            print(f"❌ Failed to register device: {e}")
            return None

    async def authenticate_device(self, device_id: str, api_key: str) -> bool:
        """Authenticate device"""
        try:
            # In a real implementation, this would verify against a database or JWT
            # For now, we'll do a simple check
            if api_key and len(api_key) > 10:  # Simple validation
                return True
            return False

        except Exception as e:
            print(f"❌ Device authentication error: {e}")
            return False

    async def route_message(self, message_data: Dict[str, Any]) -> str:
        """Route message through gateway"""
        try:
            message = Message(
                message_id=str(uuid.uuid4()),
                from_device=message_data.get("from_device", "gateway"),
                to_device=message_data.get("to_device", "broadcast"),
                protocol=ProtocolType.HTTP,
                message_type=message_data.get("message_type", "data"),
                payload=message_data.get("payload", {}),
                timestamp=datetime.now(),
                priority=message_data.get("priority", 1)
            )

            # Add to message queue
            await self.message_queue.put(message)

            return message.message_id

        except Exception as e:
            print(f"❌ Failed to route message: {e}")
            return None

    def _register_default_handlers(self):
        """Register default message handlers"""
        self.message_handlers["heartbeat"] = self._handle_heartbeat_message
        self.message_handlers["device_info"] = self._handle_device_info_message
        self.message_handlers["error"] = self._handle_error_message

    async def _handle_heartbeat_message(self, message: Message):
        """Handle heartbeat message"""
        print(f"💓 Heartbeat from {message.from_device}")

    async def _handle_device_info_message(self, message: Message):
        """Handle device info message"""
        print(f"📱 Device info from {message.from_device}: {message.payload}")

    async def _handle_error_message(self, message: Message):
        """Handle error message"""
        print(f"🚨 Error from {message.from_device}: {message.payload}")

    def get_gateway_status(self) -> Dict[str, Any]:
        """Get gateway status"""
        return {
            "running": self._running,
            "connections": {
                "total": len(self.connections),
                "active": len([c for c in self.connections.values() if c.state == DeviceState.AUTHORIZED]),
                "by_protocol": self._get_connections_by_protocol()
            },
            "stats": self.stats,
            "mqtt_topics": len(self.mqtt_topics),
            "uptime": self.stats.get("uptime", 0),
            "last_updated": datetime.now().isoformat()
        }

    def _get_connections_by_protocol(self) -> Dict[str, int]:
        """Get connection count by protocol"""
        protocol_count = {}
        for connection in self.connections.values():
            protocol = connection.protocol.value
            protocol_count[protocol] = protocol_count.get(protocol, 0) + 1
        return protocol_count

# Global gateway instance
omni_gateway = None

def initialize_omni_gateway(config: Dict[str, Any] = None) -> OmniGateway:
    """Initialize OMNI Gateway"""
    global omni_gateway
    omni_gateway = OmniGateway(config)
    return omni_gateway

def get_omni_gateway() -> OmniGateway:
    """Get global gateway instance"""
    return omni_gateway

async def main():
    """Main function for testing"""
    print("🧪 Testing OMNI Gateway...")

    # Initialize gateway
    gateway = initialize_omni_gateway({
        "host": "localhost",
        "port": 3090,
        "websocket_port": 3091,
        "mqtt_host": "localhost",
        "mqtt_port": 1883
    })

    try:
        # Start gateway
        await gateway.start()

        # Monitor for a while
        for i in range(10):
            await asyncio.sleep(1)
            status = gateway.get_gateway_status()
            print(f"📊 Gateway Status: {status['connections']['active']} active connections")

        # Test device registration
        device_id = await gateway.register_device({
            "device_id": "test_device_001",
            "device_type": "vr_glasses",
            "capabilities": {"webxr": True, "webrtc": True}
        })

        print(f"✅ Test device registered: {device_id}")

    finally:
        await gateway.stop()

    print("✅ OMNI Gateway test completed!")

if __name__ == "__main__":
    asyncio.run(main())