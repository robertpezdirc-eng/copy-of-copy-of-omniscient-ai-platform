#!/usr/bin/env python3
"""
OMNI Platform - Enhanced VR Integration Module
Supports Meta Quest, SteamVR, and advanced VR features
"""

import asyncio
import json
import time
import os
import logging
import aiohttp
import websockets
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import base64

@dataclass
class VRDevice:
    """VR Device information"""
    device_id: str
    device_type: str  # "quest", "steamvr", "other"
    device_name: str
    connection_status: str
    battery_level: Optional[float] = None
    firmware_version: Optional[str] = None
    last_seen: Optional[datetime] = None

@dataclass
class VRSession:
    """VR Session data"""
    session_id: str
    user_id: str
    device_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    session_data: Dict[str, Any] = None
    performance_metrics: Dict[str, Any] = None

class MetaQuestIntegration:
    """Meta Quest VR Integration"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://graph.meta.com"
        self.session = None
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for Meta Quest integration"""
        logger = logging.getLogger('MetaQuestIntegration')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.FileHandler('omni_vr_meta_quest.log', encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    async def get_device_info(self, device_id: str) -> Dict[str, Any]:
        """Get Meta Quest device information"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/vr/devices/{device_id}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        device_data = await response.json()
                        return {
                            "device_id": device_data.get("id"),
                            "device_name": device_data.get("name"),
                            "battery_level": device_data.get("battery_level"),
                            "firmware_version": device_data.get("firmware_version"),
                            "connection_status": "connected" if device_data.get("is_connected") else "disconnected"
                        }
                    else:
                        self.logger.error(f"Failed to get device info: {response.status}")
                        return {"error": f"HTTP {response.status}"}
        except Exception as e:
            self.logger.error(f"Meta Quest API error: {e}")
            return {"error": str(e)}

class SteamVRIntegration:
    """SteamVR Integration"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.steamvr.com"
        self.websocket_url = "wss://websocket.steamvr.com"
        self.session = None
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for SteamVR integration"""
        logger = logging.getLogger('SteamVRIntegration')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.FileHandler('omni_vr_steamvr.log', encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    async def get_device_status(self, device_id: str) -> Dict[str, Any]:
        """Get SteamVR device status"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/devices/{device_id}/status",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        status_data = await response.json()
                        return {
                            "device_id": status_data.get("device_id"),
                            "connection_status": status_data.get("status"),
                            "tracking_status": status_data.get("tracking"),
                            "performance_mode": status_data.get("performance_mode"),
                            "last_update": datetime.now().isoformat()
                        }
                    else:
                        return {"error": f"HTTP {response.status}"}
        except Exception as e:
            self.logger.error(f"SteamVR API error: {e}")
            return {"error": str(e)}

class OmniVRManager:
    """Enhanced VR Manager for OMNI Platform"""

    def __init__(self):
        self.meta_quest = None
        self.steamvr = None
        self.connected_devices: Dict[str, VRDevice] = {}
        self.active_sessions: Dict[str, VRSession] = {}
        self.websocket_connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for VR manager"""
        logger = logging.getLogger('OmniVRManager')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.FileHandler('omni_vr_manager.log', encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def configure_meta_quest(self, api_key: str):
        """Configure Meta Quest integration"""
        try:
            self.meta_quest = MetaQuestIntegration(api_key)
            self.logger.info("Meta Quest integration configured successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to configure Meta Quest: {e}")
            return False

    def configure_steamvr(self, api_key: str):
        """Configure SteamVR integration"""
        try:
            self.steamvr = SteamVRIntegration(api_key)
            self.logger.info("SteamVR integration configured successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to configure SteamVR: {e}")
            return False

    async def connect_vr_device(self, device_type: str, device_id: str, api_key: str = None) -> Dict[str, Any]:
        """Connect to VR device"""
        try:
            if device_type.lower() == "meta_quest" or device_type.lower() == "quest":
                if not self.meta_quest and api_key:
                    self.configure_meta_quest(api_key)

                if self.meta_quest:
                    device_info = await self.meta_quest.get_device_info(device_id)
                    if "error" not in device_info:
                        vr_device = VRDevice(
                            device_id=device_id,
                            device_type="quest",
                            device_name=device_info.get("device_name", "Meta Quest"),
                            connection_status=device_info.get("connection_status", "connected"),
                            battery_level=device_info.get("battery_level"),
                            firmware_version=device_info.get("firmware_version"),
                            last_seen=datetime.now()
                        )
                        self.connected_devices[device_id] = vr_device
                        self.logger.info(f"Connected to Meta Quest device: {device_id}")
                        return {"success": True, "device": asdict(vr_device)}

            elif device_type.lower() == "steamvr":
                if not self.steamvr and api_key:
                    self.configure_steamvr(api_key)

                if self.steamvr:
                    device_status = await self.steamvr.get_device_status(device_id)
                    if "error" not in device_status:
                        vr_device = VRDevice(
                            device_id=device_id,
                            device_type="steamvr",
                            device_name=f"SteamVR Device {device_id}",
                            connection_status=device_status.get("connection_status", "connected"),
                            last_seen=datetime.now()
                        )
                        self.connected_devices[device_id] = vr_device
                        self.logger.info(f"Connected to SteamVR device: {device_id}")
                        return {"success": True, "device": asdict(vr_device)}

            return {"success": False, "error": f"Unsupported device type: {device_type}"}

        except Exception as e:
            self.logger.error(f"Failed to connect VR device: {e}")
            return {"success": False, "error": str(e)}

    async def start_vr_session(self, user_id: str, device_id: str) -> Dict[str, Any]:
        """Start VR session"""
        try:
            if device_id not in self.connected_devices:
                return {"success": False, "error": "Device not connected"}

            session_id = f"session_{user_id}_{device_id}_{int(time.time())}"

            session = VRSession(
                session_id=session_id,
                user_id=user_id,
                device_id=device_id,
                start_time=datetime.now(),
                session_data={"status": "active"},
                performance_metrics={"fps": 0, "latency": 0, "quality": "high"}
            )

            self.active_sessions[session_id] = session

            self.logger.info(f"Started VR session: {session_id}")
            return {"success": True, "session_id": session_id, "session": asdict(session)}

        except Exception as e:
            self.logger.error(f"Failed to start VR session: {e}")
            return {"success": False, "error": str(e)}

    async def end_vr_session(self, session_id: str) -> Dict[str, Any]:
        """End VR session"""
        try:
            if session_id not in self.active_sessions:
                return {"success": False, "error": "Session not found"}

            session = self.active_sessions[session_id]
            session.end_time = datetime.now()
            session.session_data["status"] = "completed"

            # Calculate session duration
            duration = (session.end_time - session.start_time).total_seconds()
            session.session_data["duration_seconds"] = duration

            self.logger.info(f"Ended VR session: {session_id} (Duration: {duration}s)")
            return {"success": True, "session": asdict(session)}

        except Exception as e:
            self.logger.error(f"Failed to end VR session: {e}")
            return {"success": False, "error": str(e)}

    def get_vr_status(self) -> Dict[str, Any]:
        """Get comprehensive VR status"""
        return {
            "connected_devices": {device_id: asdict(device) for device_id, device in self.connected_devices.items()},
            "active_sessions": {session_id: asdict(session) for session_id, session in self.active_sessions.items()},
            "meta_quest_configured": self.meta_quest is not None,
            "steamvr_configured": self.steamvr is not None,
            "total_devices": len(self.connected_devices),
            "active_sessions_count": len(self.active_sessions)
        }

# Global VR manager instance
omni_vr_manager = OmniVRManager()

def main():
    """Main function for VR integration testing"""
    print("[OMNI] Enhanced VR Integration Module")
    print("=" * 50)
    print("[META_QUEST] Meta Quest VR support")
    print("[STEAMVR] SteamVR integration")
    print("[WEBSOCKET] Real-time VR data streaming")
    print("[ADVANCED] Multi-device VR management")
    print()

    # Example usage
    async def demo():
        # Configure VR integrations
        meta_quest_key = os.environ.get("META_QUEST_API_KEY")
        steamvr_key = os.environ.get("STEAMVR_API_KEY")

        if meta_quest_key:
            omni_vr_manager.configure_meta_quest(meta_quest_key)
            print("✅ Meta Quest integration configured")

        if steamvr_key:
            omni_vr_manager.configure_steamvr(steamvr_key)
            print("✅ SteamVR integration configured")

        # Get status
        status = omni_vr_manager.get_vr_status()
        print(f"📊 VR Status: {status}")

        return {"status": "success", "vr_status": status}

    try:
        result = asyncio.run(demo())
        print(f"\n[SUCCESS] VR Integration Demo: {result}")
        return result
    except Exception as e:
        print(f"\n[ERROR] VR Integration Demo failed: {e}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    main()