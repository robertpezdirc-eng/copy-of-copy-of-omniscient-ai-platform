#!/usr/bin/env python3
"""
OMNI VR Core Integration Module
Advanced VR integration with OMNI Singularity platform core
Connects VR experiences with quantum cores, neural networks, and AI agents
"""

import asyncio
import json
import time
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
import logging
import threading
import websockets
from enum import Enum

class VRDeviceType(Enum):
    """VR device types supported"""
    OCULUS_QUEST = "oculus_quest"
    HTC_VIVE = "htc_vive"
    MOBILE_VR = "mobile_vr"
    DESKTOP_VR = "desktop_vr"
    OTHER = "other"

class VRFramework(Enum):
    """VR frameworks supported"""
    AFRAME = "aframe"
    THREE_JS = "three.js"
    BABYLON_JS = "babylon.js"

@dataclass
class VRDevice:
    """VR device information"""
    device_id: str
    device_type: VRDeviceType
    device_name: str
    user_id: str
    connected_at: datetime
    last_seen: datetime
    capabilities: Dict[str, Any]
    status: str = "connected"

@dataclass
class VRSession:
    """VR session information"""
    session_id: str
    device_id: str
    user_id: str
    project_id: str
    framework: VRFramework
    started_at: datetime
    status: str = "active"
    metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class VRProject:
    """VR project information"""
    project_id: str
    name: str
    description: str
    framework: VRFramework
    project_type: str
    created_at: datetime
    created_by: str
    file_path: str
    status: str = "ready"
    access_count: int = 0

class OmniVRCore:
    """Main VR core integration class"""

    def __init__(self, omni_core=None):
        self.omni_core = omni_core
        self.devices: Dict[str, VRDevice] = {}
        self.sessions: Dict[str, VRSession] = {}
        self.projects: Dict[str, VRProject] = {}
        self.websocket_clients: Dict[str, websockets.WebSocketServerProtocol] = {}

        # VR Configuration
        self.config = {
            "max_devices": 100,
            "max_sessions_per_device": 5,
            "session_timeout": 3600,  # seconds
            "heartbeat_interval": 30,  # seconds
            "supported_frameworks": ["aframe", "three.js", "babylon.js"],
            "auto_cleanup": True,
            "enable_quantum_integration": True,
            "enable_ai_assistance": True
        }

        # Load existing projects
        self._load_vr_projects()

        # Start background services
        self._start_background_services()

        print("🎮 OMNI VR Core initialized and connected to platform")

    def _load_vr_projects(self):
        """Load existing VR projects from vr_projects directory"""
        try:
            vr_projects_dir = Path("vr_projects")
            if vr_projects_dir.exists():
                # Load project metadata from vr_gateway.json
                gateway_config_path = Path("vr_gateway.json")
                if gateway_config_path.exists():
                    with open(gateway_config_path, 'r') as f:
                        config = json.load(f)

                    # Load example projects
                    examples = config.get('examples', {})
                    for project_key, project_data in examples.items():
                        project = VRProject(
                            project_id=f"example_{project_key}",
                            name=project_data['name'],
                            description=project_data['description'],
                            framework=VRFramework(project_data['framework']),
                            project_type="example",
                            created_at=datetime.now(),
                            created_by="system",
                            file_path=f"vr_projects/templates/{project_data['framework']}_basic.html"
                        )
                        self.projects[project.project_id] = project

                print(f"✅ Loaded {len(self.projects)} VR projects")
        except Exception as e:
            print(f"⚠️ Failed to load VR projects: {e}")

    def _start_background_services(self):
        """Start background services for VR core"""
        # Device heartbeat monitor
        heartbeat_thread = threading.Thread(target=self._device_heartbeat_monitor, daemon=True)
        heartbeat_thread.start()

        # Session cleanup
        cleanup_thread = threading.Thread(target=self._session_cleanup, daemon=True)
        cleanup_thread.start()

        # Quantum integration (if enabled)
        if self.config["enable_quantum_integration"]:
            quantum_thread = threading.Thread(target=self._quantum_vr_integration, daemon=True)
            quantum_thread.start()

    def register_vr_device(self, device_info: Dict[str, Any], user_id: str) -> str:
        """Register a new VR device"""
        try:
            device_id = str(uuid.uuid4())

            # Determine device type
            device_type_str = device_info.get('device_type', 'other').lower()
            device_type = VRDeviceType.OTHER
            for dt in VRDeviceType:
                if dt.value in device_type_str:
                    device_type = dt
                    break

            device = VRDevice(
                device_id=device_id,
                device_type=device_type,
                device_name=device_info.get('device_name', f"VR Device {device_id[:8]}"),
                user_id=user_id,
                connected_at=datetime.now(),
                last_seen=datetime.now(),
                capabilities=device_info.get('capabilities', {})
            )

            self.devices[device_id] = device

            # Notify Omni core about new device
            if self.omni_core:
                self.omni_core.register_component("vr_device", device_id, device.__dict__)

            print(f"🎮 VR Device registered: {device.device_name} ({device_type.value})")
            return device_id

        except Exception as e:
            print(f"❌ Failed to register VR device: {e}")
            return None

    def create_vr_session(self, device_id: str, project_id: str, user_id: str) -> str:
        """Create a new VR session"""
        try:
            if device_id not in self.devices:
                return None

            session_id = str(uuid.uuid4())

            # Get project info
            project = self.projects.get(project_id)
            if not project:
                return None

            session = VRSession(
                session_id=session_id,
                device_id=device_id,
                user_id=user_id,
                project_id=project_id,
                framework=project.framework,
                started_at=datetime.now()
            )

            self.sessions[session_id] = session

            # Update device last seen
            self.devices[device_id].last_seen = datetime.now()

            # Update project access count
            project.access_count += 1

            # Notify Omni core about new session
            if self.omni_core:
                self.omni_core.register_component("vr_session", session_id, session.__dict__)

            print(f"🎮 VR Session created: {session_id} for project {project.name}")
            return session_id

        except Exception as e:
            print(f"❌ Failed to create VR session: {e}")
            return None

    def end_vr_session(self, session_id: str):
        """End a VR session"""
        try:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session.status = "ended"

                # Update device last seen
                if session.device_id in self.devices:
                    self.devices[session.device_id].last_seen = datetime.now()

                # Archive session data
                if self.omni_core:
                    self.omni_core.archive_component("vr_session", session_id, session.__dict__)

                print(f"🎮 VR Session ended: {session_id}")
                return True

        except Exception as e:
            print(f"❌ Failed to end VR session: {e}")
            return False

    def get_vr_device_status(self, device_id: str) -> Dict[str, Any]:
        """Get VR device status"""
        device = self.devices.get(device_id)
        if not device:
            return {"error": "Device not found"}

        return {
            "device_id": device.device_id,
            "device_name": device.device_name,
            "device_type": device.device_type.value,
            "status": device.status,
            "connected_at": device.connected_at.isoformat(),
            "last_seen": device.last_seen.isoformat(),
            "capabilities": device.capabilities,
            "active_sessions": [
                session.session_id for session in self.sessions.values()
                if session.device_id == device_id and session.status == "active"
            ]
        }

    def get_vr_projects_list(self) -> List[Dict[str, Any]]:
        """Get list of available VR projects"""
        projects = []
        for project in self.projects.values():
            projects.append({
                "project_id": project.project_id,
                "name": project.name,
                "description": project.description,
                "framework": project.framework.value,
                "project_type": project.project_type,
                "created_at": project.created_at.isoformat(),
                "access_count": project.access_count,
                "status": project.status
            })
        return projects

    def get_vr_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get VR session information"""
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        device = self.devices.get(session.device_id)
        project = self.projects.get(session.project_id)

        return {
            "session_id": session.session_id,
            "device_name": device.device_name if device else "Unknown",
            "project_name": project.name if project else "Unknown",
            "framework": session.framework.value,
            "started_at": session.started_at.isoformat(),
            "status": session.status,
            "metrics": session.metrics
        }

    def _device_heartbeat_monitor(self):
        """Monitor device heartbeats and cleanup inactive devices"""
        while True:
            try:
                current_time = datetime.now()
                inactive_devices = []

                for device_id, device in self.devices.items():
                    # Check if device hasn't been seen for too long
                    if (current_time - device.last_seen).seconds > 300:  # 5 minutes
                        device.status = "inactive"
                        inactive_devices.append(device_id)

                # Remove very old inactive devices
                for device_id in inactive_devices:
                    if (current_time - self.devices[device_id].last_seen).seconds > 1800:  # 30 minutes
                        del self.devices[device_id]
                        print(f"🗑️ Removed inactive VR device: {device_id}")

                time.sleep(self.config["heartbeat_interval"])

            except Exception as e:
                print(f"⚠️ Device heartbeat monitor error: {e}")
                time.sleep(self.config["heartbeat_interval"])

    def _session_cleanup(self):
        """Clean up expired sessions"""
        while True:
            try:
                current_time = datetime.now()
                expired_sessions = []

                for session_id, session in self.sessions.items():
                    if session.status == "active":
                        # Check if session has expired
                        if (current_time - session.started_at).seconds > self.config["session_timeout"]:
                            session.status = "expired"
                            expired_sessions.append(session_id)

                # End expired sessions
                for session_id in expired_sessions:
                    self.end_vr_session(session_id)
                    print(f"⏰ Ended expired VR session: {session_id}")

                time.sleep(60)  # Check every minute

            except Exception as e:
                print(f"⚠️ Session cleanup error: {e}")
                time.sleep(60)

    def _quantum_vr_integration(self):
        """Integrate VR with quantum computing (if available)"""
        while True:
            try:
                if not self.omni_core or not hasattr(self.omni_core, 'quantum_cores'):
                    time.sleep(60)
                    continue

                # Get active VR sessions
                active_sessions = [
                    session for session in self.sessions.values()
                    if session.status == "active"
                ]

                if active_sessions:
                    # Use quantum computing for VR optimization
                    for session in active_sessions:
                        try:
                            # Quantum-enhanced VR processing
                            quantum_data = {
                                "session_id": session.session_id,
                                "framework": session.framework.value,
                                "metrics": session.metrics,
                                "timestamp": datetime.now().isoformat()
                            }

                            # Process through quantum core if available
                            if hasattr(self.omni_core, 'process_quantum_data'):
                                result = self.omni_core.process_quantum_data("vr_session", quantum_data)
                                if result:
                                    session.metrics["quantum_enhanced"] = True
                                    session.metrics["last_quantum_update"] = datetime.now().isoformat()

                        except Exception as e:
                            print(f"⚠️ Quantum VR integration error for session {session.session_id}: {e}")

                time.sleep(30)  # Process every 30 seconds

            except Exception as e:
                print(f"⚠️ Quantum VR integration error: {e}")
                time.sleep(60)

    def get_vr_core_status(self) -> Dict[str, Any]:
        """Get VR core status"""
        return {
            "total_devices": len(self.devices),
            "active_devices": len([d for d in self.devices.values() if d.status == "connected"]),
            "total_sessions": len(self.sessions),
            "active_sessions": len([s for s in self.sessions.values() if s.status == "active"]),
            "total_projects": len(self.projects),
            "config": self.config,
            "quantum_integration": self.config["enable_quantum_integration"],
            "ai_assistance": self.config["enable_ai_assistance"]
        }

# Global VR core instance
omni_vr_core = None

def initialize_vr_core(omni_core=None) -> OmniVRCore:
    """Initialize the VR core with Omni platform"""
    global omni_vr_core
    omni_vr_core = OmniVRCore(omni_core)
    return omni_vr_core

def get_vr_core() -> OmniVRCore:
    """Get the global VR core instance"""
    return omni_vr_core

# VR API functions for external use
def register_vr_device(device_info: Dict[str, Any], user_id: str) -> str:
    """Register a VR device"""
    if omni_vr_core:
        return omni_vr_core.register_vr_device(device_info, user_id)
    return None

def create_vr_session(device_id: str, project_id: str, user_id: str) -> str:
    """Create a VR session"""
    if omni_vr_core:
        return omni_vr_core.create_vr_session(device_id, project_id, user_id)
    return None

def get_vr_projects() -> List[Dict[str, Any]]:
    """Get list of VR projects"""
    if omni_vr_core:
        return omni_vr_core.get_vr_projects_list()
    return []

def get_vr_status() -> Dict[str, Any]:
    """Get VR core status"""
    if omni_vr_core:
        return omni_vr_core.get_vr_core_status()
    return {"error": "VR core not initialized"}

if __name__ == "__main__":
    # Test VR core initialization
    print("🧪 Testing OMNI VR Core...")
    vr_core = initialize_vr_core()
    print(f"✅ VR Core Status: {vr_core.get_vr_core_status()}")

    # Test device registration
    device_info = {
        "device_type": "oculus_quest",
        "device_name": "Test Oculus Quest",
        "capabilities": {"webxr": True, "hand_tracking": True}
    }
    device_id = register_vr_device(device_info, "test_user")
    print(f"✅ Device registered: {device_id}")

    # Test project listing
    projects = get_vr_projects()
    print(f"✅ Available projects: {len(projects)}")

    print("🎮 OMNI VR Core test completed!")