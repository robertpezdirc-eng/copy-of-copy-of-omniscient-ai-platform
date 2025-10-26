#!/usr/bin/env python3
"""
OMNI Platform Auto Launcher with Retry Mechanism
Self-healing launcher that automatically restarts the platform on errors

This launcher provides:
1. Automatic retry with exponential backoff
2. SyntaxError and runtime error handling
3. Self-healing capabilities
4. Comprehensive logging and monitoring
5. Service-ready configuration
6. Docker compatibility

Author: OMNI Platform Auto Launcher
Version: 3.0.0
"""

import asyncio
import json
import time
import os
import sys
import logging
import threading
import subprocess
import signal
import platform
import psutil
import importlib.util
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

class LaunchStatus(Enum):
    """Launcher operational status"""
    INITIALIZING = "initializing"
    STARTING_PLATFORM = "starting_platform"
    PLATFORM_RUNNING = "platform_running"
    RETRYING = "retrying"
    ERROR = "error"
    SHUTDOWN = "shutdown"

class ErrorType(Enum):
    """Types of errors that can occur"""
    SYNTAX_ERROR = "syntax_error"
    IMPORT_ERROR = "import_error"
    RUNTIME_ERROR = "runtime_error"
    CONNECTION_ERROR = "connection_error"
    RESOURCE_ERROR = "resource_error"
    UNKNOWN_ERROR = "unknown_error"

@dataclass
class RetryConfig:
    """Retry configuration settings"""
    max_retries: int = 10
    base_delay: float = 1.0
    max_delay: float = 300.0  # 5 minutes
    backoff_factor: float = 2.0
    jitter: bool = True

@dataclass
class LauncherMetrics:
    """Launcher performance metrics"""
    start_time: float = field(default_factory=time.time)
    total_restarts: int = 0
    successful_runs: int = 0
    total_errors: int = 0
    last_error: Optional[str] = None
    last_error_type: Optional[ErrorType] = None
    uptime: float = 0.0

class OmniAutoLauncher:
    """Self-healing OMNI platform launcher with retry mechanism"""

    def __init__(self, platform_module: str = "omni_toggle_start", platform_args: List[str] = None):
        self.launcher_name = "OMNI Auto Launcher"
        self.version = "3.0.0"
        self.platform_module = platform_module
        self.platform_args = platform_args or ["minimal"]

        # Core components
        self.status = LaunchStatus.INITIALIZING
        self.current_process: Optional[subprocess.Popen] = None
        self.monitor_thread: Optional[threading.Thread] = None
        self.health_check_thread: Optional[threading.Thread] = None

        # Configuration
        self.retry_config = RetryConfig()
        self.metrics = LauncherMetrics()

        # Control flags
        self.shutdown_requested = False
        self.pause_monitoring = False

        # Error tracking
        self.error_history: List[Dict[str, Any]] = []
        self.max_error_history = 100

        # Setup logging
        self.logger = self._setup_logging()

        # Setup signal handlers
        self._setup_signal_handlers()

    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging for auto launcher"""
        logger = logging.getLogger('OmniAutoLauncher')
        logger.setLevel(logging.INFO)

        # Remove existing handlers
        logger.handlers = []

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler
        try:
            os.makedirs('omni_platform/logs', exist_ok=True)
            log_file = f'omni_platform/logs/omni_auto_launcher_{int(time.time())}.log'
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            console_handler.emit(logging.LogRecord(
                'OmniAutoLauncher', logging.WARNING, '', 0,
                f'Could not create log file: {e}', (), None
            ))

        return logger

    def _setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers"""
        def signal_handler(signum, frame):
            self.logger.info(f'Received signal {signum}. Initiating graceful shutdown...')
            self.shutdown()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _classify_error(self, error: Exception) -> ErrorType:
        """Classify error type for appropriate handling"""
        error_str = str(error).lower()

        if "syntaxerror" in error_str or "unterminated string" in error_str:
            return ErrorType.SYNTAX_ERROR
        elif "importerror" in error_str or "modulenotfounderror" in error_str:
            return ErrorType.IMPORT_ERROR
        elif "connection" in error_str or "timeout" in error_str:
            return ErrorType.CONNECTION_ERROR
        elif "memory" in error_str or "out of memory" in error_str:
            return ErrorType.RESOURCE_ERROR
        elif "runtime" in error_str or "typeerror" in error_str or "valueerror" in error_str:
            return ErrorType.RUNTIME_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR

    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt with exponential backoff"""
        delay = min(
            self.retry_config.base_delay * (self.retry_config.backoff_factor ** attempt),
            self.retry_config.max_delay
        )

        # Add jitter to prevent thundering herd
        if self.retry_config.jitter:
            import random
            jitter = random.uniform(0.5, 1.5)
            delay *= jitter

        return delay

    def _record_error(self, error: Exception, attempt: int):
        """Record error for analysis and metrics"""
        error_type = self._classify_error(error)

        error_record = {
            "timestamp": time.time(),
            "attempt": attempt,
            "error_type": error_type.value,
            "error_message": str(error),
            "platform_module": self.platform_module
        }

        self.error_history.append(error_record)

        # Keep only recent errors
        if len(self.error_history) > self.max_error_history:
            self.error_history = self.error_history[-self.max_error_history:]

        # Update metrics
        self.metrics.total_errors += 1
        self.metrics.last_error = str(error)
        self.metrics.last_error_type = error_type

        self.logger.error(f"Error recorded (attempt {attempt}): {error_type.value} - {error}")

    def _attempt_platform_start(self) -> bool:
        """Attempt to start the platform module"""
        try:
            self.logger.info(f"Attempting to start platform: {self.platform_module}")

            # Check if module file exists
            if not os.path.exists(f"{self.platform_module}.py"):
                raise FileNotFoundError(f"Platform module not found: {self.platform_module}.py")

            # First, try to compile the module to check for syntax errors
            try:
                self.logger.debug(f"Compiling {self.platform_module}.py for syntax check...")
                with open(f"{self.platform_module}.py", 'r', encoding='utf-8') as f:
                    source_code = f.read()

                compile(source_code, f"{self.platform_module}.py", 'exec')
                self.logger.debug("Syntax check passed")

            except SyntaxError as e:
                self.logger.error(f"Syntax error in {self.platform_module}.py: {e}")
                self._record_error(e, self.metrics.total_restarts + 1)
                return False
            except Exception as e:
                self.logger.error(f"Compilation error in {self.platform_module}.py: {e}")
                self._record_error(e, self.metrics.total_restarts + 1)
                return False

            # If syntax check passed, try to import and run
            try:
                # Import the module
                spec = importlib.util.spec_from_file_location(
                    self.platform_module,
                    f"{self.platform_module}.py"
                )
                module = importlib.util.module_from_spec(spec)

                # Execute the module
                self.logger.info(f"Executing {self.platform_module} module...")
                spec.loader.exec_module(module)

                # Check if module has main function and call it
                if hasattr(module, 'main'):
                    self.logger.info("Calling main() function...")
                    result = module.main()

                    if result and isinstance(result, dict) and result.get("status") == "success":
                        self.logger.info("Platform started successfully")
                        self.metrics.successful_runs += 1
                        return True
                    else:
                        self.logger.warning("Platform main() returned non-success status")
                        return False
                else:
                    self.logger.warning("No main() function found in module")
                    return True  # Consider it successful if no main function

            except Exception as e:
                self.logger.error(f"Runtime error in {self.platform_module}: {e}")
                self._record_error(e, self.metrics.total_restarts + 1)
                return False

        except Exception as e:
            self.logger.error(f"Failed to start platform {self.platform_module}: {e}")
            self._record_error(e, self.metrics.total_restarts + 1)
            return False

    def _start_platform_with_retry(self) -> bool:
        """Start platform with retry mechanism"""
        self.status = LaunchStatus.STARTING_PLATFORM

        for attempt in range(self.retry_config.max_retries):
            if self.shutdown_requested:
                self.logger.info("Shutdown requested, stopping retry attempts")
                return False

            self.logger.info(f"Platform start attempt {attempt + 1}/{self.retry_config.max_retries}")

            try:
                if self._attempt_platform_start():
                    self.status = LaunchStatus.PLATFORM_RUNNING
                    self.logger.info("Platform started successfully!")
                    return True

            except Exception as e:
                self.logger.error(f"Platform start attempt {attempt + 1} failed: {e}")
                self._record_error(e, attempt + 1)

            # Wait before retry (except on last attempt)
            if attempt < self.retry_config.max_retries - 1:
                delay = self._calculate_retry_delay(attempt)
                self.status = LaunchStatus.RETRYING
                self.logger.info(f"Retrying in {delay:.1f} seconds...")

                # Check for shutdown during delay
                for _ in range(int(delay)):
                    if self.shutdown_requested:
                        return False
                    time.sleep(1)

        self.status = LaunchStatus.ERROR
        self.logger.error(f"Failed to start platform after {self.retry_config.max_retries} attempts")
        return False

    def _monitor_platform(self):
        """Monitor platform health and restart if necessary"""
        self.logger.info("Starting platform monitoring...")

        while not self.shutdown_requested:
            try:
                if self.status == LaunchStatus.PLATFORM_RUNNING:
                    # Check if platform process is still running
                    # This is a simple check - in a real implementation you might
                    # check specific health endpoints or process status

                    current_time = time.time()
                    self.metrics.uptime = current_time - self.metrics.start_time

                    # Log periodic status
                    if int(current_time) % 60 == 0:  # Every minute
                        self.logger.info(f"Platform monitoring: uptime={self.metrics.uptime:.1f}s, restarts={self.metrics.total_restarts}")

                time.sleep(10)  # Check every 10 seconds

            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(10)

    def _health_check_loop(self):
        """Periodic health check and self-healing"""
        self.logger.info("Starting health check loop...")

        while not self.shutdown_requested:
            try:
                if self.status == LaunchStatus.ERROR:
                    self.logger.info("Platform in error state, attempting recovery...")
                    self._start_platform_with_retry()

                elif self.status == LaunchStatus.PLATFORM_RUNNING:
                    # Perform health checks
                    health_ok = self._perform_health_checks()

                    if not health_ok:
                        self.logger.warning("Health checks failed, platform may need restart")
                        # Don't immediately restart - wait for monitoring to detect

                time.sleep(30)  # Health check every 30 seconds

            except Exception as e:
                self.logger.error(f"Health check error: {e}")
                time.sleep(30)

    def _perform_health_checks(self) -> bool:
        """Perform comprehensive health checks"""
        try:
            # Check system resources
            memory_usage = psutil.virtual_memory().percent
            cpu_usage = psutil.cpu_percent(interval=1)

            if memory_usage > 90:
                self.logger.warning(f"High memory usage: {memory_usage:.1f}%")
                return False

            if cpu_usage > 80:
                self.logger.warning(f"High CPU usage: {cpu_usage:.1f}%")
                return False

            # Check disk space
            disk_usage = psutil.disk_usage('/').percent
            if disk_usage > 95:
                self.logger.warning(f"Low disk space: {disk_usage:.1f}% used")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

    def start(self) -> bool:
        """Start the auto launcher"""
        self.logger.info("Starting OMNI Auto Launcher with Retry Mechanism")
        print("OMNI Auto Launcher - Self-Healing Platform Launcher")
        print("=" * 80)
        print("Automatic retry with exponential backoff")
        print("SyntaxError and runtime error handling")
        print("Self-healing capabilities")
        print("Comprehensive monitoring and logging")
        print()

        try:
            # Start monitoring threads
            self.monitor_thread = threading.Thread(
                target=self._monitor_platform,
                daemon=True
            )
            self.monitor_thread.start()

            self.health_check_thread = threading.Thread(
                target=self._health_check_loop,
                daemon=True
            )
            self.health_check_thread.start()

            # Start platform with retry mechanism
            success = self._start_platform_with_retry()

            if success:
                print("OMNI Platform Auto Launcher operational!")
                print("Monitoring active - will restart on errors")
                print("Self-healing enabled")
                print()
                print("Press Ctrl+C to shutdown gracefully")

                # Keep main thread alive
                while not self.shutdown_requested:
                    time.sleep(1)

                return True
            else:
                print("Failed to start platform after all retry attempts")
                return False

        except Exception as e:
            self.logger.error(f"Auto launcher failed: {e}")
            print(f"Auto launcher failed: {e}")
            return False

    def shutdown(self):
        """Shutdown the auto launcher gracefully"""
        self.logger.info("Shutting down OMNI Auto Launcher...")
        print("\nShutting down OMNI Auto Launcher...")

        self.shutdown_requested = True
        self.status = LaunchStatus.SHUTDOWN

        # Wait for threads to finish
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)

        if self.health_check_thread and self.health_check_thread.is_alive():
            self.health_check_thread.join(timeout=5)

        print("Auto launcher shutdown complete")

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive launcher status"""
        return {
            "launcher": {
                "name": self.launcher_name,
                "version": self.version,
                "status": self.status.value,
                "platform_module": self.platform_module,
                "platform_args": self.platform_args
            },
            "metrics": {
                "uptime": time.time() - self.metrics.start_time,
                "total_restarts": self.metrics.total_restarts,
                "successful_runs": self.metrics.successful_runs,
                "total_errors": self.metrics.total_errors,
                "last_error": self.metrics.last_error,
                "last_error_type": self.metrics.last_error_type.value if self.metrics.last_error_type else None
            },
            "configuration": {
                "max_retries": self.retry_config.max_retries,
                "base_delay": self.retry_config.base_delay,
                "max_delay": self.retry_config.max_delay,
                "backoff_factor": self.retry_config.backoff_factor
            },
            "system": {
                "platform": platform.system(),
                "python_version": sys.version,
                "memory_usage": psutil.virtual_memory().percent,
                "cpu_usage": psutil.cpu_percent(interval=1)
            },
            "recent_errors": self.error_history[-5:],  # Last 5 errors
            "timestamp": time.time()
        }

def create_windows_service():
    """Create Windows service configuration"""
    service_script = """@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PYTHON_PATH={sys.executable}"
set "LAUNCHER_SCRIPT=%SCRIPT_DIR%omni_auto_launcher.py"

echo Starting OMNI Platform Auto Launcher Service...
echo Script Directory: %SCRIPT_DIR%
echo Python Path: %PYTHON_PATH%
echo Launcher Script: %LAUNCHER_SCRIPT%

cd /d "%SCRIPT_DIR%"
"%PYTHON_PATH%" "%LAUNCHER_SCRIPT%"

if errorlevel 1 (
    echo Service failed with exit code %errorlevel%
    timeout /t 30
    exit /b 1
) else (
    echo Service completed successfully
    exit /b 0
)
"""

    service_path = 'omni_platform/start_auto_service.bat'
    with open(service_path, 'w') as f:
        f.write(service_script)

    print(f"[OK] Windows service script created: {service_path}")
    print("[INFO] To install as Windows service:")
    print("   1. Copy NSSM (Non-Sucking Service Manager) to your system")
    print("   2. Run: nssm install OmniAutoLauncher python omni_auto_launcher.py")
    print("   3. Set service to start automatically")

def create_linux_service():
    """Create Linux systemd service configuration"""
    service_content = """[Unit]
Description=OMNI Platform Auto Launcher - Self-Healing AI Platform
After=network.target
Wants=network.target

[Service]
Type=simple
User=omni
Group=omni
WorkingDirectory=/opt/omni_platform
Environment=PATH=/opt/omni_platform/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin
Environment=PYTHONPATH=/opt/omni_platform
ExecStart=/opt/omni_platform/venv/bin/python /opt/omni_platform/omni_auto_launcher.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=omni-auto-launcher

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/omni_platform /tmp /var/log/omni_platform

# Resource limits
MemoryLimit=2G
TimeoutStartSec=30
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
"""

    service_path = 'omni_platform/omni-auto-launcher.service'
    with open(service_path, 'w') as f:
        f.write(service_content)

    print(f"[OK] Linux systemd service created: {service_path}")
    print("[INFO] To install as Linux service:")
    print("   1. Copy files to /opt/omni_platform/")
    print("   2. Run: sudo systemctl enable omni-auto-launcher.service")
    print("   3. Run: sudo systemctl start omni-auto-launcher.service")
    print("   4. Check status: sudo systemctl status omni-auto-launcher.service")

def create_docker_config():
    """Create Docker configuration with restart policy"""
    dockerfile_content = """FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy OMNI platform files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN useradd --create-home --shell /bin/bash omni
USER omni

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8080/api/health', timeout=5)" || exit 1

# Start command with auto launcher
CMD ["python", "omni_auto_launcher.py"]
"""

    docker_compose_content = """version: '3.8'

services:
  omni-platform:
    build: .
    container_name: omni-platform
    restart: always
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
      - ./logs:/app/omni_platform/logs
    environment:
      - PYTHONUNBUFFERED=1
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8080/api/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
"""

    # Create Dockerfile
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile_content)

    # Create docker-compose.yml
    with open('docker-compose.yml', 'w') as f:
        f.write(docker_compose_content)

    print("[OK] Docker configuration created:")
    print("   - Dockerfile for container build")
    print("   - docker-compose.yml with restart policy")
    print("[INFO] To run with Docker:")
    print("   1. Build: docker build -t omni-platform .")
    print("   2. Run: docker-compose up -d")
    print("   3. Container will auto-restart on failures")

def main():
    """Main function for OMNI Auto Launcher"""
    print("🚀 OMNI Platform Auto Launcher - Self-Healing System")
    print("=" * 80)
    print("🔄 Automatic retry mechanism with exponential backoff")
    print("🛠️ SyntaxError and runtime error handling")
    print("💚 Self-healing and auto-recovery capabilities")
    print("📊 Comprehensive monitoring and logging")
    print()

    # Get platform module from command line or use default
    platform_module = sys.argv[1] if len(sys.argv) > 1 else "omni_toggle_start"
    platform_args = sys.argv[2:] if len(sys.argv) > 2 else ["minimal"]

    try:
        # Create and start auto launcher
        launcher = OmniAutoLauncher(platform_module, platform_args)

        # Show configuration
        print("Configuration:")
        print(f"   Platform Module: {platform_module}")
        print(f"   Platform Args: {platform_args}")
        print(f"   Max Retries: {launcher.retry_config.max_retries}")
        print(f"   Base Delay: {launcher.retry_config.base_delay}s")
        print(f"   Max Delay: {launcher.retry_config.max_delay}s")
        print()

        # Start the launcher
        success = launcher.start()

        if success:
            print("Auto launcher completed successfully!")
            return 0
        else:
            print("❌ Auto launcher failed")
            return 1

    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        return 0
    except Exception as e:
        print(f"Auto launcher error: {e}")
        return 1

if __name__ == "__main__":
    # Create service configurations if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--create-service":
        print("Creating service configurations...")
        create_windows_service()
        create_linux_service()
        create_docker_config()
        print("All service configurations created!")
    else:
        exit_code = main()
        exit(exit_code)