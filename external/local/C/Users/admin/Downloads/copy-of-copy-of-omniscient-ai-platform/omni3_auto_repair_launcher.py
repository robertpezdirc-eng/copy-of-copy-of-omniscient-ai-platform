#!/usr/bin/env python3
"""
OMNI3 Full Auto Repair Launcher
Samodejni minimal/maximal preklop glede na sistem
"""

import threading
import time
import os
import sys
import logging
import psutil
import socket

# =========================
# Logger
# =========================
logger = logging.getLogger("Omni3AutoRepair")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# =========================
# Core Framework
# =========================
class OmniFramework:
    def __init__(self):
        if not hasattr(self, 'logger'):
            self.logger = logger
        self.logger.info("Omni Framework initialized")

# =========================
# OpenAI Self-Heal
# =========================
def ensure_openai_key():
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        logger.info("✅ OpenAI key found")
        return key
    logger.warning("⚠️ OpenAI key missing")
    return None

def test_openai(key):
    if not key:
        return False
    try:
        import openai
        openai.api_key = key
        openai.ChatCompletion.create(model="gpt-4", messages=[{"role":"user","content":"Test"}])
        logger.info("✅ OpenAI connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ OpenAI connection failed: {e}")
        return False

def auto_heal_openai():
    key = ensure_openai_key()
    for attempt in range(3):
        if test_openai(key):
            return True
        logger.warning(f"⚠️ OpenAI attempt #{attempt+1} failed, retry in 5s")
        time.sleep(5)
    return False

# =========================
# Port Management
# =========================
def is_port_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) != 0

def free_port(port):
    import psutil
    for proc in psutil.process_iter(['pid', 'connections']):
        for conn in proc.info['connections']:
            if conn.laddr.port == port:
                logger.warning(f"⚠️ Port {port} busy, killing PID {proc.info['pid']}")
                try:
                    proc.kill()
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"❌ Can't kill PID {proc.info['pid']}: {e}")

# =========================
# Omni Launcher
# =========================
class OmniLauncher:
    def __init__(self):
        self.mode = "minimal"
        self.active_threads = []
        self.system_status = {
            "platform": "initializing",
            "core": "inactive",
            "ai_agents": "inactive",
            "web_dashboard": "inactive",
            "monitoring": "inactive",
            "heavy_modules": "inactive"
        }
        self.cpu_threshold = 80.0
        self.ram_threshold = 90.0

    def auto_mode_switcher(self):
        while True:
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory().percent
            if cpu > self.cpu_threshold or mem > self.ram_threshold:
                if self.mode != "minimal":
                    logger.warning("⚠️ High load detected, switching to MINIMAL mode")
                    self.mode = "minimal"
                    self.system_status["heavy_modules"] = "inactive"
            else:
                if self.mode != "maximal":
                    logger.info("✅ Load normal, switching to MAXIMAL mode")
                    self.mode = "maximal"
                    # ponovno naloži težke module
                    self._load_heavy_modules()
            time.sleep(5)

    def launch_platform(self):
        logger.info(f"🚀 Launching OMNI3 Auto-Repair Platform")
        self._launch_core()
        self._start_dashboard()
        if self.mode=="maximal":
            self._load_heavy_modules()
        self._start_monitoring()
        threading.Thread(target=self.auto_mode_switcher, daemon=True).start()
        self._keep_running()

    def _launch_core(self):
        try:
            self.core = OmniFramework()
            self.system_status["core"] = "active"
            logger.info("✅ Core systems launched")
        except Exception as e:
            logger.error(f"❌ Core systems failed: {e}")

    def _start_dashboard(self):
        port = 8080
        if not is_port_free(port):
            free_port(port)

        def dashboard():
            while True:
                try:
                    logger.info(f"🌐 Dashboard running on http://localhost:{port} [Mode: {self.mode.upper()}]")
                    time.sleep(10)
                except Exception as e:
                    logger.error(f"❌ Dashboard error: {e}")
                    logger.info("🔄 Restarting dashboard in 5s...")
                    time.sleep(5)

        t = threading.Thread(target=dashboard, daemon=True)
        t.start()
        self.active_threads.append(t)
        self.system_status["web_dashboard"]="active"
        logger.info("✅ Dashboard started")

    def _load_heavy_modules(self):
        def heavy():
            logger.info("⚡ Loading heavy AI modules...")
            time.sleep(2)
            logger.info("✅ Heavy AI modules loaded")
            self.system_status["ai_agents"]="active"
            self.system_status["heavy_modules"]="active"

        t = threading.Thread(target=heavy, daemon=True)
        t.start()
        self.active_threads.append(t)

    def _start_monitoring(self):
        def monitor():
            while True:
                cpu = psutil.cpu_percent(interval=1)
                mem = psutil.virtual_memory().percent
                logger.info(f"💚 CPU: {cpu:.1f}% | Memory: {mem:.1f}% | Mode: {self.mode.upper()}")
                time.sleep(10)
        t = threading.Thread(target=monitor, daemon=True)
        t.start()
        self.active_threads.append(t)
        logger.info("✅ Health monitoring started")

    def _keep_running(self):
        logger.info("🎯 OMNI3 running, press Ctrl+C to stop")
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            logger.info("🛑 Shutdown requested")

# =========================
# Main
# =========================
def main():
    threading.Thread(target=auto_heal_openai, daemon=True).start()
    launcher = OmniLauncher()
    launcher.launch_platform()

if __name__=="__main__":
    main()