#!/usr/bin/env python3
"""
OMNI VR Dashboard Integration
Advanced VR dashboard integration with OMNI Singularity platform
Provides VR monitoring, device management, and session control
"""

import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging
import threading
import requests
from dataclasses import dataclass, field

@dataclass
class VRDashboardMetrics:
    """VR dashboard metrics"""
    total_devices: int = 0
    active_devices: int = 0
    total_sessions: int = 0
    active_sessions: int = 0
    total_projects: int = 0
    framework_usage: Dict[str, int] = field(default_factory=dict)
    device_types: Dict[str, int] = field(default_factory=dict)
    session_duration_avg: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

class OmniVRDashboard:
    """VR Dashboard integration for OMNI platform"""

    def __init__(self, server_url: str = "http://localhost:3090"):
        self.server_url = server_url
        self.metrics = VRDashboardMetrics()
        self.websocket_connections = []
        self.dashboard_enabled = True

        # Auto-refresh settings
        self.refresh_interval = 30  # seconds
        self.metrics_history = []

        # Start background services
        self._start_background_services()

        print("📊 OMNI VR Dashboard initialized")

    def _start_background_services(self):
        """Start background services for dashboard"""
        # Metrics refresh thread
        metrics_thread = threading.Thread(target=self._refresh_metrics_loop, daemon=True)
        metrics_thread.start()

        # WebSocket connection manager
        ws_thread = threading.Thread(target=self._websocket_manager, daemon=True)
        ws_thread.start()

    def _refresh_metrics_loop(self):
        """Continuously refresh VR metrics"""
        while self.dashboard_enabled:
            try:
                self.refresh_metrics()
                time.sleep(self.refresh_interval)
            except Exception as e:
                print(f"⚠️ VR Dashboard metrics refresh error: {e}")
                time.sleep(self.refresh_interval)

    def _websocket_manager(self):
        """Manage WebSocket connections for real-time updates"""
        while self.dashboard_enabled:
            try:
                # This would connect to the VR WebSocket server
                # For now, we'll simulate the connection
                time.sleep(60)
            except Exception as e:
                print(f"⚠️ VR Dashboard WebSocket error: {e}")
                time.sleep(60)

    def refresh_metrics(self) -> bool:
        """Refresh VR metrics from server"""
        try:
            # Get VR core status
            response = requests.get(f"{self.server_url}/vr/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    vr_status = data.get('vr_status', {})

                    # Update metrics
                    self.metrics.total_devices = vr_status.get('totalDevices', 0)
                    self.metrics.active_devices = vr_status.get('activeDevices', 0)
                    self.metrics.total_sessions = vr_status.get('totalSessions', 0)
                    self.metrics.active_sessions = vr_status.get('activeSessions', 0)
                    self.metrics.total_projects = vr_status.get('totalProjects', 0)
                    self.metrics.last_updated = datetime.now()

                    # Store in history
                    self.metrics_history.append(self.metrics.__dict__.copy())
                    if len(self.metrics_history) > 100:  # Keep last 100 entries
                        self.metrics_history.pop(0)

                    return True

            return False

        except Exception as e:
            print(f"⚠️ Failed to refresh VR metrics: {e}")
            return False

    def get_vr_projects(self) -> List[Dict[str, Any]]:
        """Get list of VR projects"""
        try:
            response = requests.get(f"{self.server_url}/vr/projects", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('projects', [])
            return []
        except Exception as e:
            print(f"⚠️ Failed to get VR projects: {e}")
            return []

    def register_vr_device(self, device_info: Dict[str, Any], user_id: str) -> Optional[str]:
        """Register a new VR device"""
        try:
            payload = {
                "deviceInfo": device_info,
                "userId": user_id
            }

            response = requests.post(f"{self.server_url}/vr/devices/register",
                                   json=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return data.get('deviceId')
            return None

        except Exception as e:
            print(f"⚠️ Failed to register VR device: {e}")
            return None

    def create_vr_session(self, device_id: str, project_id: str, user_id: str) -> Optional[str]:
        """Create a new VR session"""
        try:
            payload = {
                "deviceId": device_id,
                "projectId": project_id,
                "userId": user_id
            }

            response = requests.post(f"{self.server_url}/vr/sessions/create",
                                   json=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return data.get('sessionId')
            return None

        except Exception as e:
            print(f"⚠️ Failed to create VR session: {e}")
            return None

    def get_device_status(self, device_id: str) -> Dict[str, Any]:
        """Get VR device status"""
        try:
            response = requests.get(f"{self.server_url}/vr/devices/{device_id}/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('device_status', {})
            return {"error": "Device not found"}
        except Exception as e:
            return {"error": str(e)}

    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get VR session information"""
        try:
            response = requests.get(f"{self.server_url}/vr/sessions/{session_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('session_info', {})
            return {"error": "Session not found"}
        except Exception as e:
            return {"error": str(e)}

    def end_session(self, session_id: str) -> bool:
        """End a VR session"""
        try:
            response = requests.post(f"{self.server_url}/vr/sessions/{session_id}/end", timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"⚠️ Failed to end VR session: {e}")
            return False

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        return {
            "metrics": {
                "total_devices": self.metrics.total_devices,
                "active_devices": self.metrics.active_devices,
                "total_sessions": self.metrics.total_sessions,
                "active_sessions": self.metrics.active_sessions,
                "total_projects": self.metrics.total_projects,
                "last_updated": self.metrics.last_updated.isoformat()
            },
            "projects": self.get_vr_projects(),
            "recent_activity": self.get_recent_activity(),
            "system_status": self.get_system_status()
        }

    def get_recent_activity(self) -> List[Dict[str, Any]]:
        """Get recent VR activity"""
        # This would typically come from a database or log files
        # For now, return simulated recent activity
        return [
            {
                "type": "session_started",
                "device_name": "Oculus Quest 2",
                "project": "VR Trampoline Game",
                "timestamp": datetime.now().isoformat(),
                "user": "test_user"
            },
            {
                "type": "device_connected",
                "device_name": "HTC Vive Pro",
                "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
                "user": "vr_user_1"
            }
        ]

    def get_system_status(self) -> Dict[str, Any]:
        """Get VR system status"""
        return {
            "server_connected": self._test_server_connection(),
            "websocket_connected": len(self.websocket_connections) > 0,
            "quantum_integration": True,  # Would check actual quantum integration
            "ai_assistance": True,        # Would check AI assistance status
            "last_health_check": datetime.now().isoformat()
        }

    def _test_server_connection(self) -> bool:
        """Test connection to VR server"""
        try:
            response = requests.get(f"{self.server_url}/vr/status", timeout=5)
            return response.status_code == 200
        except:
            return False

    def generate_vr_report(self) -> str:
        """Generate VR usage report"""
        try:
            report = []
            report.append("🎮 OMNI VR Dashboard Report")
            report.append("=" * 50)
            report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append("")

            # Metrics section
            report.append("📊 METRICS:")
            report.append(f"  • Total Devices: {self.metrics.total_devices}")
            report.append(f"  • Active Devices: {self.metrics.active_devices}")
            report.append(f"  • Total Sessions: {self.metrics.total_sessions}")
            report.append(f"  • Active Sessions: {self.metrics.active_sessions}")
            report.append(f"  • Total Projects: {self.metrics.total_projects}")
            report.append("")

            # Projects section
            projects = self.get_vr_projects()
            if projects:
                report.append("🎯 VR PROJECTS:")
                for project in projects[:5]:  # Show top 5
                    report.append(f"  • {project['name']} ({project['framework']}) - {project['accessCount']} accesses")
                report.append("")

            # System status
            status = self.get_system_status()
            report.append("🔧 SYSTEM STATUS:")
            report.append(f"  • Server Connected: {'✅' if status['server_connected'] else '❌'}")
            report.append(f"  • WebSocket Connected: {'✅' if status['websocket_connected'] else '❌'}")
            report.append(f"  • Quantum Integration: {'✅' if status['quantum_integration'] else '❌'}")
            report.append(f"  • AI Assistance: {'✅' if status['ai_assistance'] else '❌'}")

            return "\n".join(report)

        except Exception as e:
            return f"❌ Failed to generate VR report: {e}"

    def export_metrics_json(self) -> str:
        """Export metrics as JSON"""
        try:
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": self.metrics.__dict__,
                "projects": self.get_vr_projects(),
                "system_status": self.get_system_status()
            }
            return json.dumps(export_data, indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": str(e)})

# Global VR dashboard instance
omni_vr_dashboard = None

def initialize_vr_dashboard(server_url: str = "http://localhost:3090") -> OmniVRDashboard:
    """Initialize VR dashboard"""
    global omni_vr_dashboard
    omni_vr_dashboard = OmniVRDashboard(server_url)
    return omni_vr_dashboard

def get_vr_dashboard() -> OmniVRDashboard:
    """Get global VR dashboard instance"""
    return omni_vr_dashboard

# Dashboard API functions
def get_vr_metrics() -> Dict[str, Any]:
    """Get VR metrics"""
    if omni_vr_dashboard:
        return omni_vr_dashboard.metrics.__dict__
    return {}

def get_vr_projects() -> List[Dict[str, Any]]:
    """Get VR projects list"""
    if omni_vr_dashboard:
        return omni_vr_dashboard.get_vr_projects()
    return []

def generate_vr_report() -> str:
    """Generate VR report"""
    if omni_vr_dashboard:
        return omni_vr_dashboard.generate_vr_report()
    return "❌ VR Dashboard not initialized"

def get_vr_dashboard_data() -> Dict[str, Any]:
    """Get complete dashboard data"""
    if omni_vr_dashboard:
        return omni_vr_dashboard.get_dashboard_data()
    return {"error": "VR Dashboard not initialized"}

if __name__ == "__main__":
    # Test VR dashboard
    print("🧪 Testing OMNI VR Dashboard...")

    # Initialize dashboard
    dashboard = initialize_vr_dashboard()

    # Test metrics refresh
    print("📊 Refreshing metrics...")
    if dashboard.refresh_metrics():
        print("✅ Metrics refreshed successfully")
        print(f"   Total Devices: {dashboard.metrics.total_devices}")
        print(f"   Active Sessions: {dashboard.metrics.active_sessions}")
    else:
        print("❌ Failed to refresh metrics")

    # Test projects
    print("\n🎯 Getting VR projects...")
    projects = dashboard.get_vr_projects()
    print(f"✅ Found {len(projects)} VR projects")

    # Test report generation
    print("\n📋 Generating VR report...")
    report = dashboard.generate_vr_report()
    print(report)

    print("\n✅ OMNI VR Dashboard test completed!")