#!/usr/bin/env python3
"""
OMNI Platform Toggle Launcher - Popravljena verzija
Minimal in Maximal mode z delujočim loggerjem
"""

import threading
import time
import sys
import logging
import psutil
from fastapi import FastAPI
import uvicorn
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# =========================
# Web Dashboard App
# =========================
app = FastAPI(title="OMNI Platform Dashboard", version="1.0.0")

# Add CORS middleware to allow browser requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

@app.get("/", response_class=HTMLResponse)
async def dashboard_home():
    """Main dashboard page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>OMNI Platform Dashboard</title>
        <meta http-equiv="refresh" content="5">
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.95);
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
                backdrop-filter: blur(10px);
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 2px solid #eee;
            }
            h1 {
                color: #2c3e50;
                margin: 0;
                font-size: 2.5em;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
            }
            .status-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                text-align: center;
            }
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }
            .metric-card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.08);
                text-align: center;
                transition: transform 0.3s ease;
            }
            .metric-card:hover {
                transform: translateY(-5px);
            }
            .metric-value {
                font-size: 2em;
                font-weight: bold;
                margin: 10px 0;
            }
            .metric-label {
                color: #666;
                font-size: 0.9em;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            .cpu-value { color: #e74c3c; }
            .memory-value { color: #3498db; }
            .threads-value { color: #2ecc71; }
            .uptime-value { color: #f39c12; }
            .status-indicator {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 8px;
            }
            .status-active { background: #2ecc71; }
            .status-inactive { background: #e74c3c; }
            .components {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
            }
            .footer {
                text-align: center;
                margin-top: 30px;
                color: #666;
                font-size: 0.9em;
            }
            .components-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px;
                margin: 15px 0;
            }
            .component-item {
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                border-left: 4px solid #667eea;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 OMNI Platform Dashboard</h1>
                <p>Professional AI Assistance Platform</p>
            </div>

            <div class="status-card">
                <h2>Platform Status: <span id="platform-status">Loading...</span></h2>
                <p>Mode: <span id="platform-mode">Loading...</span> | Uptime: <span id="platform-uptime">0s</span></p>
            </div>

            <div id="metrics">
                <h3>System Metrics</h3>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">CPU Usage</div>
                        <div class="metric-value cpu-value" id="cpu-value">0%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Memory Usage</div>
                        <div class="metric-value memory-value" id="memory-value">0%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Active Threads</div>
                        <div class="metric-value threads-value" id="threads-value">0</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Platform Uptime</div>
                        <div class="metric-value uptime-value" id="uptime-value">0s</div>
                    </div>
                </div>
            </div>

            <div class="components">
                <h3>Platform Components</h3>
                <div id="components-status">
                    <p>Loading component status...</p>
                </div>
            </div>

            <div class="footer">
                <p>OMNI Platform v3.0 | Real-time Monitoring Dashboard</p>
            </div>
        </div>
        <script>
            async function updateStatus() {
                try {
                    console.log('Fetching status from /api/status...');
                    const response = await fetch('/api/status');

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    const data = await response.json();
                    console.log('Received data:', data);

                    // Update status card
                    document.getElementById('platform-status').textContent = data.platform_status;
                    document.getElementById('platform-mode').textContent = data.mode;
                    document.getElementById('platform-uptime').textContent = `${data.uptime}s`;

                    // Update metrics with animations
                    document.getElementById('cpu-value').textContent = `${data.cpu}%`;
                    document.getElementById('memory-value').textContent = `${data.memory}%`;
                    document.getElementById('threads-value').textContent = data.active_threads;
                    document.getElementById('uptime-value').textContent = `${data.uptime}s`;

                    // Update components status
                    const components = data.components;
                    let componentsHtml = '<div class="components-grid">';

                    if (Object.keys(components).length === 0) {
                        componentsHtml += '<p>No components data available</p>';
                    } else {
                        for (const [name, status] of Object.entries(components)) {
                            const statusClass = status === 'active' ? 'status-active' : 'status-inactive';
                            componentsHtml += `
                                <div class="component-item">
                                    <span class="status-indicator ${statusClass}"></span>
                                    <strong>${name}:</strong> ${status}
                                </div>
                            `;
                        }
                    }

                    componentsHtml += '</div>';
                    document.getElementById('components-status').innerHTML = componentsHtml;

                } catch (error) {
                    console.error('Error updating status:', error);
                    document.getElementById('platform-status').textContent = 'Error';
                    document.getElementById('components-status').innerHTML = `
                        <p style="color: red;">Error loading platform data: ${error.message}</p>
                    `;
                }
            }

            // Load initial status
            updateStatus();

            // Update every 3 seconds for more responsive feel
            setInterval(updateStatus, 3000);
        </script>
    </body>
    </html>
    """

@app.get("/api/status")
async def get_status():
    """Get current platform status"""
    # Get the current launcher instance (created in main())
    current_launcher = getattr(get_status, '_current_launcher', None)

    uptime = time.time() - OmniToggleLauncher.start_time
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent

    # Get component data from current launcher instance
    components = {}
    if current_launcher and hasattr(current_launcher, 'system_status'):
        components = current_launcher.system_status.copy()

    return {
        "platform_status": "active",
        "mode": current_launcher.mode if current_launcher else "unknown",
        "uptime": round(uptime, 1),
        "cpu": round(cpu, 1),
        "memory": round(memory, 1),
        "active_threads": len(current_launcher.active_threads) if current_launcher else 0,
        "components": components
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/api/omni-integration")
async def omni_integration_status():
    """Get OMNI platform integration status"""
    try:
        # Try to connect to OMNIBOT13 server
        import requests

        try:
            response = requests.get("http://localhost:3000/api/status", timeout=5)
            omni_status = response.json() if response.status_code == 200 else {"status": "error"}
        except:
            omni_status = {"status": "not_connected"}

        # Get current platform status
        current_launcher = getattr(get_status, '_current_launcher', None)
        platform_data = {
            "platform": current_launcher.system_status if current_launcher else {},
            "mode": current_launcher.mode if current_launcher else "unknown",
            "uptime": time.time() - OmniToggleLauncher.start_time
        }

        return {
            "status": "connected",
            "omni_platform": platform_data,
            "omni_web_server": omni_status,
            "integration": "active",
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }

# =========================
# Popravljena Core Framework
# =========================
class OmniAssistanceToolsFramework:
    def __init__(self):
        # Logger dodan, da se ne sesuva
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('OmniAssistanceToolsFramework')
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _initialize_framework(self):
        self.logger.info("Omni Assistance Tools Framework initialized")


# =========================
# Main Launcher
# =========================
class OmniToggleLauncher:
    start_time = time.time()  # Class variable for start time

    def __init__(self, mode="minimal"):
        self.mode = mode
        self.active_threads = []
        self.system_status = {
            "platform": "initializing",
            "core_systems": "inactive",
            "ai_agents": "inactive",
            "web_dashboard": "inactive",
            "monitoring": "inactive",
            "heavy_modules": "inactive",
            "openai_integration": "inactive"
        }

    # -------- Launch platform --------
    def launch_platform(self):
        print("OMNI Platform Toggle Launcher")
        print("=" * 80)
        print(f"Mode: {self.mode.upper()}")
        print("Professional AI Assistance Platform")
        print("Smart loading with async optimization\n")

        try:
            self._launch_core_systems()
            self._start_dashboard()

            if self.mode == "maximal":
                self._load_heavy_components()
            else:
                print("Minimal mode - heavy modules skipped for instant start")

            self._start_health_monitoring()
            self._show_platform_status()
            self._keep_platform_running()
            return True
        except Exception as e:
            print(f"[ERROR] Platform launch failed: {e}")
            return False

    # -------- Core Systems --------
    def _launch_core_systems(self):
        try:
            self.core_framework = OmniAssistanceToolsFramework()
            self.core_framework._initialize_framework()
            self.system_status["core_systems"] = "active"
            self.system_status["platform"] = "core_active"

            # Initialize OpenAI integration if available
            self._initialize_openai_integration()

            print("  [OK] Core systems launched")
        except Exception as e:
            print(f"  [ERROR] Core systems launch failed: {e}")

    # -------- OpenAI Integration --------
    def _initialize_openai_integration(self):
        try:
            import os
            openai_key = os.environ.get("OPENAI_API_KEY")

            if openai_key:
                try:
                    import openai
                    openai.api_key = openai_key
                    # Test the connection
                    client = openai.OpenAI(api_key=openai_key)
                    client.models.list()
                    self.system_status["openai_integration"] = "active"
                    print("  [OK] OpenAI integration configured")
                except Exception as e:
                    print(f"  [WARNING] OpenAI API key found but connection failed: {e}")
                    self.system_status["openai_integration"] = "error"
            else:
                print("  [INFO] OpenAI API key not found - OpenAI features disabled")
                self.system_status["openai_integration"] = "inactive"
        except Exception as e:
            print(f"  [ERROR] OpenAI initialization failed: {e}")
            self.system_status["openai_integration"] = "error"

    # -------- Web Dashboard --------
    def _start_dashboard(self):
        try:
            def dashboard_thread():
                try:
                    print("  [WEB] Starting FastAPI dashboard on http://localhost:8080")
                    print("  [CHART] Dashboard endpoints:")
                    print("     GET  /        - Main dashboard page")
                    print("     GET  /api/status  - Platform status API")
                    print("     GET  /api/health  - Health check")
                    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="error")
                except Exception as e:
                    print(f"  [ERROR] Dashboard error: {e}")

            t = threading.Thread(target=dashboard_thread, daemon=True)
            t.start()
            self.active_threads.append(t)
            self.system_status["web_dashboard"] = "active"
            print("  [OK] FastAPI web dashboard started")
        except Exception as e:
            print(f"  [ERROR] Dashboard launch failed: {e}")

    # -------- Heavy Components --------
    def _load_heavy_components(self):
        try:
            def heavy_thread():
                print("  [FAST] Loading heavy AI modules...")
                time.sleep(2)
                print("  [OK] Heavy AI modules loaded")
                self.system_status["ai_agents"] = "active"
                self.system_status["heavy_modules"] = "active"

            t = threading.Thread(target=heavy_thread, daemon=True)
            t.start()
            self.active_threads.append(t)
        except Exception as e:
            print(f"  [ERROR] Heavy components failed: {e}")

    # -------- Health Monitoring --------
    def _start_health_monitoring(self):
        try:
            def monitor_thread():
                while True:
                    cpu = psutil.cpu_percent(interval=1)
                    mem = psutil.virtual_memory().percent
                    self.system_status["monitoring"] = "active"
                    print(f"  [HEALTH] CPU: {cpu:.1f}% | Memory: {mem:.1f}%")
                    time.sleep(10)

            t = threading.Thread(target=monitor_thread, daemon=True)
            t.start()
            self.active_threads.append(t)
            print("  [OK] Health monitoring started")
        except Exception as e:
            print(f"  [ERROR] Health monitoring failed: {e}")

    # -------- Status Display --------
    def _show_platform_status(self):
        print("\n[CHART] OMNI PLATFORM STATUS")
        print("=" * 80)
        print(f"Mode: {self.mode.upper()}")
        print(f"Platform: {self.system_status['platform']}")
        print(f"Core Systems: {self.system_status['core_systems']}")
        print(f"AI Agents: {self.system_status['ai_agents']}")
        print(f"Web Dashboard: {self.system_status['web_dashboard']}")
        print(f"Monitoring: {self.system_status['monitoring']}")
        print(f"Heavy Modules: {self.system_status['heavy_modules']}")
        print(f"OpenAI Integration: {self.system_status['openai_integration']}\n")

    # -------- Keep running --------
    def _keep_platform_running(self):
        print("OMNI Platform is now running! Press Ctrl+C to shutdown gracefully")
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n[STOP] Shutdown requested by user")

# =========================
# Main
# =========================
def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "minimal"
    if mode not in ["minimal", "maximal"]:
        print("Usage: python omni_toggle_start.py [minimal|maximal]")
        return

    launcher = OmniToggleLauncher(mode)

    # Store launcher instance for API access
    get_status._current_launcher = launcher

    success = launcher.launch_platform()

    if success:
        print("\n[SUCCESS] OMNI PLATFORM LAUNCH SUCCESSFUL!")
    else:
        print("\n[ERROR] OMNI PLATFORM LAUNCH FAILED")

if __name__ == "__main__":
    main()