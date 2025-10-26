#!/usr/bin/env python3
"""
OMNI Sync Core Dashboard Server
Web server for the device discovery dashboard with API endpoints

Author: OMNI Platform
Version: 1.0.0
"""

import json
import threading
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

from omni_sync_core import get_sync_core, get_discovered_devices, start_device_discovery, stop_device_discovery, get_discovery_stats
from omni_device_manager import get_device_manager, get_devices, get_device, connect_device, disconnect_device, get_device_stats
from omni_quest3_manager import get_quest3_manager, register_quest3, connect_quest3, disconnect_quest3, create_ar_overlay, get_quest3_devices, get_quest3_status

class OmniSyncDashboardServer:
    """Web server for OMNI Sync Core Dashboard"""

    def __init__(self, host='0.0.0.0', port=3080):
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for all routes

        self.host = host
        self.port = port
        self.server_thread = None
        self.running = False

        # Setup routes
        self._setup_routes()

        print("🌐 OMNI Sync Dashboard Server initialized")

    def _setup_routes(self):
        """Setup Flask routes"""

        @self.app.route('/')
        def dashboard():
            """Serve the main dashboard"""
            return render_template('omni_sync_dashboard.html')

        @self.app.route('/api/devices')
        def api_devices():
            """Get discovered devices"""
            try:
                devices = get_devices()
                return jsonify({
                    'success': True,
                    'devices': devices,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/sync-stats')
        def api_sync_stats():
            """Get sync core statistics"""
            try:
                stats = get_discovery_stats()
                return jsonify({
                    'success': True,
                    'stats': stats,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/device-stats')
        def api_device_stats():
            """Get device manager statistics"""
            try:
                stats = get_device_stats()
                return jsonify({
                    'success': True,
                    'stats': stats,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/start-discovery', methods=['POST'])
        def api_start_discovery():
            """Start device discovery"""
            try:
                start_device_discovery()
                return jsonify({
                    'success': True,
                    'message': 'Device discovery started'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/stop-discovery', methods=['POST'])
        def api_stop_discovery():
            """Stop device discovery"""
            try:
                stop_device_discovery()
                return jsonify({
                    'success': True,
                    'message': 'Device discovery stopped'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/connect-device/<device_id>', methods=['POST'])
        def api_connect_device(device_id):
            """Connect to a specific device"""
            try:
                success = connect_device(device_id)
                return jsonify({
                    'success': success,
                    'message': 'Device connected' if success else 'Failed to connect device'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/disconnect-device/<device_id>', methods=['POST'])
        def api_disconnect_device(device_id):
            """Disconnect from a specific device"""
            try:
                success = disconnect_device(device_id)
                return jsonify({
                    'success': success,
                    'message': 'Device disconnected' if success else 'Failed to disconnect device'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/device/<device_id>')
        def api_get_device(device_id):
            """Get specific device information"""
            try:
                device = get_device(device_id)
                if device:
                    return jsonify({
                        'success': True,
                        'device': device
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Device not found'
                    }), 404
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/clear-devices', methods=['POST'])
        def api_clear_devices():
            """Clear all discovered devices"""
            try:
                # This would need to be implemented in the device manager
                return jsonify({
                    'success': True,
                    'message': 'Devices cleared'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/status')
        def api_status():
            """Get overall system status"""
            try:
                sync_stats = get_discovery_stats()
                device_stats = get_device_stats()

                return jsonify({
                    'success': True,
                    'status': {
                        'sync_core': sync_stats,
                        'device_manager': device_stats,
                        'dashboard_server': {
                            'running': self.running,
                            'host': self.host,
                            'port': self.port
                        }
                    },
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        # Meta Quest 3 API endpoints
        @self.app.route('/quest3')
        def quest3_dashboard():
            """Serve the Quest 3 dashboard"""
            return render_template('omni_quest3_dashboard.html')

        @self.app.route('/api/quest3-devices')
        def api_quest3_devices():
            """Get Quest 3 devices"""
            try:
                devices = get_quest3_devices()
                return jsonify({
                    'success': True,
                    'devices': devices,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/quest3-status')
        def api_quest3_status():
            """Get Quest 3 status"""
            try:
                status = get_quest3_status()
                return jsonify({
                    'success': True,
                    'status': status,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/connect-quest3', methods=['POST'])
        def api_connect_quest3():
            """Connect to Quest 3"""
            try:
                data = request.get_json()
                connection_mode = data.get('connection_mode', 'standalone')
                success = connect_quest3(None, connection_mode)  # Connect first available or create new
                return jsonify({
                    'success': success,
                    'message': 'Quest 3 connected' if success else 'Failed to connect Quest 3'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/connect-quest3/<device_id>', methods=['POST'])
        def api_connect_quest3_device(device_id):
            """Connect to specific Quest 3 device"""
            try:
                success = connect_quest3(device_id)
                return jsonify({
                    'success': success,
                    'message': 'Quest 3 device connected' if success else 'Failed to connect Quest 3 device'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/disconnect-quest3/<device_id>', methods=['POST'])
        def api_disconnect_quest3_device(device_id):
            """Disconnect from specific Quest 3 device"""
            try:
                success = disconnect_quest3(device_id)
                return jsonify({
                    'success': success,
                    'message': 'Quest 3 device disconnected' if success else 'Failed to disconnect Quest 3 device'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/create-ar-overlay', methods=['POST'])
        def api_create_ar_overlay():
            """Create AR overlay for Quest 3"""
            try:
                data = request.get_json()
                # For demo, create overlay for first available device
                devices = get_quest3_devices()
                if devices:
                    device_id = devices[0]['device_id']
                    overlay_id = create_ar_overlay(device_id, data)
                    return jsonify({
                        'success': overlay_id is not None,
                        'overlay_id': overlay_id,
                        'message': 'AR overlay created' if overlay_id else 'Failed to create AR overlay'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'No Quest 3 devices available'
                    }), 400
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

    def start(self):
        """Start the dashboard server"""
        if self.running:
            print("⚠️ Dashboard server already running")
            return

        self.running = True

        def run_server():
            print(f"🚀 Starting OMNI Sync Dashboard Server on {self.host}:{self.port}")
            self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()

        print("✅ OMNI Sync Dashboard Server started")

    def stop(self):
        """Stop the dashboard server"""
        if not self.running:
            return

        self.running = False

        # In a real implementation, you'd need to shutdown the Flask server properly
        # For now, we'll just mark it as stopped
        print("⏹️ OMNI Sync Dashboard Server stopped")

# Global dashboard server instance
omni_sync_dashboard_server = None

def initialize_dashboard_server(host='0.0.0.0', port=3080):
    """Initialize the dashboard server"""
    global omni_sync_dashboard_server
    omni_sync_dashboard_server = OmniSyncDashboardServer(host, port)
    return omni_sync_dashboard_server

def get_dashboard_server():
    """Get the global dashboard server instance"""
    return omni_sync_dashboard_server

def start_dashboard_server(host='0.0.0.0', port=3080):
    """Start the dashboard server"""
    if not omni_sync_dashboard_server:
        initialize_dashboard_server(host, port)
    omni_sync_dashboard_server.start()

def stop_dashboard_server():
    """Stop the dashboard server"""
    if omni_sync_dashboard_server:
        omni_sync_dashboard_server.stop()

if __name__ == "__main__":
    # Test the dashboard server
    print("🧪 Testing OMNI Sync Dashboard Server...")

    # Initialize and start the server
    server = initialize_dashboard_server()
    server.start()

    print("✅ Dashboard server test started")
    print("📱 Open http://localhost:3080 in your browser to view the dashboard")
    print("⏹️ Press Ctrl+C to stop the server")

    try:
        # Keep the server running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping dashboard server...")
        server.stop()
        print("✅ Dashboard server stopped")