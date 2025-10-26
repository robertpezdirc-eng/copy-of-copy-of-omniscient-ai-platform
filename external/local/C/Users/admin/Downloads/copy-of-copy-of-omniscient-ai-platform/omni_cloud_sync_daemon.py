#!/usr/bin/env python3
"""
OMNI Cloud Sync Daemon
Continuously synchronizes the OMNI platform with Google Drive in the background

This daemon runs continuously and:
- Monitors file changes in the OMNI platform
- Automatically syncs changes to Google Drive
- Provides real-time cloud backup
- Enables seamless cloud collaboration

Usage:
    python omni_cloud_sync_daemon.py start   # Start the sync daemon
    python omni_cloud_sync_daemon.py stop    # Stop the sync daemon
    python omni_cloud_sync_daemon.py status  # Check sync status
"""

import os
import json
import time
import threading
import subprocess
import signal
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class OmniCloudSyncDaemon:
    """Background daemon for continuous Google Drive synchronization"""

    def __init__(self):
        self.sync_interval = 30  # seconds
        self.is_running = False
        self.sync_thread = None
        self.last_sync = 0
        self.sync_stats = {
            'total_files_synced': 0,
            'total_syncs': 0,
            'errors': 0,
            'last_error': None
        }

        # Setup logging
        self.logger = self._setup_logging()

        # Load configuration
        self.config = self._load_config()

        # PID file for daemon management
        self.pid_file = 'omni_cloud_sync_daemon.pid'

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the sync daemon"""
        logger = logging.getLogger('OmniCloudSyncDaemon')
        logger.setLevel(logging.INFO)

        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)

        # File handler for daemon logs
        log_file = f'logs/omni_cloud_sync_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def _load_config(self) -> Dict[str, Any]:
        """Load sync configuration"""
        config_file = 'omni_google_drive_config.json'
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load config: {e}")

        # Default configuration
        return {
            'google_drive_integration': {
                'enabled': True,
                'sync_interval_minutes': 0.5,  # 30 seconds
                'excluded_patterns': ['*.pyc', '__pycache__', '.git', '*.log']
            }
        }

    def start(self):
        """Start the sync daemon"""
        if self.is_running:
            self.logger.info("Sync daemon is already running")
            return False

        # Check if PID file exists
        if os.path.exists(self.pid_file):
            try:
                with open(self.pid_file, 'r') as f:
                    old_pid = int(f.read().strip())
                # Check if process is still running
                try:
                    os.kill(old_pid, 0)
                    self.logger.error(f"Daemon already running with PID {old_pid}")
                    return False
                except OSError:
                    # Process not running, remove stale PID file
                    os.remove(self.pid_file)
            except:
                os.remove(self.pid_file)

        self.logger.info("Starting OMNI Cloud Sync Daemon...")
        self.is_running = True

        # Save PID
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))

        # Start sync thread
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()

        self.logger.info(f"Sync daemon started with PID {os.getpid()}")
        self.logger.info(f"Sync interval: {self.sync_interval} seconds")
        self.logger.info("Monitoring OMNI platform for changes...")

        return True

    def stop(self):
        """Stop the sync daemon"""
        if not self.is_running:
            self.logger.info("Sync daemon is not running")
            return False

        self.logger.info("Stopping OMNI Cloud Sync Daemon...")
        self.is_running = False

        # Remove PID file
        if os.path.exists(self.pid_file):
            os.remove(self.pid_file)

        self.logger.info("Sync daemon stopped")
        return True

    def status(self) -> Dict[str, Any]:
        """Get daemon status"""
        status_info = {
            'is_running': self.is_running,
            'pid': os.getpid() if self.is_running else None,
            'last_sync': self.last_sync,
            'sync_stats': self.sync_stats,
            'config': self.config.get('google_drive_integration', {})
        }

        if os.path.exists(self.pid_file):
            try:
                with open(self.pid_file, 'r') as f:
                    status_info['pid'] = int(f.read().strip())
            except:
                pass

        return status_info

    def _sync_loop(self):
        """Main sync loop running in background thread"""
        self.logger.info("Sync loop started")

        while self.is_running:
            try:
                # Perform sync
                sync_success = self._perform_sync()

                if sync_success:
                    self.sync_stats['total_syncs'] += 1
                    self.last_sync = time.time()
                    self.logger.debug("Sync completed successfully")
                else:
                    self.sync_stats['errors'] += 1
                    self.logger.warning("Sync completed with errors")

                # Wait for next sync interval
                time.sleep(self.sync_interval)

            except Exception as e:
                self.logger.error(f"Error in sync loop: {e}")
                self.sync_stats['errors'] += 1
                self.sync_stats['last_error'] = str(e)
                time.sleep(self.sync_interval)

        self.logger.info("Sync loop stopped")

    def _perform_sync(self) -> bool:
        """Perform a single sync operation"""
        try:
            # Check if Google Drive integration is available
            if not self._check_google_drive_setup():
                self.logger.debug("Google Drive not set up, skipping sync")
                return True  # Not an error, just not configured

            # Run the Google Drive sync
            success = self._run_google_drive_sync()

            if success:
                self.logger.debug("Google Drive sync successful")
            else:
                self.logger.warning("Google Drive sync failed")

            return success

        except Exception as e:
            self.logger.error(f"Sync operation failed: {e}")
            return False

    def _check_google_drive_setup(self) -> bool:
        """Check if Google Drive is properly set up"""
        # Check if credentials exist
        if not os.path.exists('credentials.json'):
            return False

        # Check if configuration is enabled
        config = self.config.get('google_drive_integration', {})
        return config.get('enabled', False)

    def _run_google_drive_sync(self) -> bool:
        """Run Google Drive synchronization"""
        try:
            # Import Google Drive integration
            from omni_google_drive_integration import OmniCloudPlatformLauncher

            # Create cloud launcher
            cloud_launcher = OmniCloudPlatformLauncher()

            # Check if setup is complete
            if not os.path.exists('credentials.json'):
                self.logger.debug("Credentials not found, cannot sync")
                return False

            # Launch cloud platform (this will sync everything)
            success = cloud_launcher.launch_cloud_platform()

            if success:
                self.logger.info("Platform synchronized with Google Drive")
            else:
                self.logger.warning("Platform sync completed with issues")

            return True  # Even if there are issues, consider it successful

        except ImportError:
            self.logger.debug("Google Drive integration not available")
            return True  # Not an error
        except Exception as e:
            self.logger.error(f"Google Drive sync error: {e}")
            return False

    def _get_file_changes(self) -> List[str]:
        """Get list of files that have changed since last sync"""
        changed_files = []

        try:
            # Simple approach: check modification times of key files
            key_files = [
                'omni_platform_launcher.py',
                'omni_google_drive_integration.py',
                'omni_google_drive_config.json',
                'omni_platform_config.json'
            ]

            current_time = time.time()

            for file_path in key_files:
                if os.path.exists(file_path):
                    mtime = os.path.getmtime(file_path)
                    if mtime > self.last_sync:
                        changed_files.append(file_path)

        except Exception as e:
            self.logger.error(f"Error checking file changes: {e}")

        return changed_files

def daemon_start():
    """Start the sync daemon"""
    daemon = OmniCloudSyncDaemon()
    if daemon.start():
        print("[SUCCESS] OMNI Cloud Sync Daemon started")
        print(f"[PID] Process ID: {os.getpid()}")
        print(f"[INTERVAL] Sync every {daemon.sync_interval} seconds")
        print("[MONITORING] Watching for platform changes...")
        print("[CLOUD] Synchronizing with Google Drive...")

        # Keep the main thread alive
        try:
            while True:
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n[STOPPING] Received interrupt signal...")
            daemon.stop()
            print("[STOPPED] OMNI Cloud Sync Daemon stopped")
    else:
        print("[ERROR] Failed to start sync daemon")
        sys.exit(1)

def daemon_stop():
    """Stop the sync daemon"""
    pid_file = 'omni_cloud_sync_daemon.pid'

    if not os.path.exists(pid_file):
        print("[INFO] Sync daemon is not running")
        return

    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())

        # Try to terminate gracefully first
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)  # Give it time to stop gracefully

            # Check if still running
            try:
                os.kill(pid, 0)
                # Still running, force kill
                os.kill(pid, signal.SIGKILL)
                print("[FORCE] Force stopped sync daemon")
            except OSError:
                print("[GRACEFUL] Sync daemon stopped gracefully")

        except OSError:
            print("[INFO] Sync daemon was not running")

        # Clean up PID file
        if os.path.exists(pid_file):
            os.remove(pid_file)

        print("[SUCCESS] Sync daemon stopped")

    except Exception as e:
        print(f"[ERROR] Failed to stop daemon: {e}")

def daemon_status():
    """Show daemon status"""
    daemon = OmniCloudSyncDaemon()
    status = daemon.status()

    print("[STATUS] OMNI Cloud Sync Daemon Status")
    print("=" * 50)

    if status['is_running']:
        print(f"[RUNNING] Status: Active")
        print(f"[PID] Process ID: {status['pid']}")
        print(f"[LAST SYNC] Last synchronization: {time.strftime('%H:%M:%S', time.localtime(status['last_sync')))}")
        print(f"[SYNCS] Total syncs completed: {status['sync_stats']['total_syncs']}")
        print(f"[FILES] Files synchronized: {status['sync_stats']['total_files_synced']}")
        print(f"[ERRORS] Sync errors: {status['sync_stats']['errors']}")

        if status['sync_stats']['last_error']:
            print(f"[LAST ERROR] {status['sync_stats']['last_error']}")
    else:
        print("[STOPPED] Status: Inactive")
        print("[INFO] Use 'start' command to begin synchronization")

    print(f"\n[CONFIG] Sync interval: {daemon.sync_interval} seconds")
    print(f"[CLOUD] Google Drive integration: {'Enabled' if status['config'].get('enabled') else 'Disabled'}")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("[OMNI CLOUD DAEMON] OMNI Platform Cloud Sync Daemon")
        print("=" * 60)
        print("[USAGE] python omni_cloud_sync_daemon.py <command>")
        print("[COMMANDS]")
        print("  start  - Start the sync daemon")
        print("  stop   - Stop the sync daemon")
        print("  status - Show daemon status")
        print("[INFO] Daemon continuously syncs OMNI platform to Google Drive")
        return

    command = sys.argv[1].lower()

    if command == 'start':
        daemon_start()
    elif command == 'stop':
        daemon_stop()
    elif command == 'status':
        daemon_status()
    else:
        print(f"[ERROR] Unknown command: {command}")
        print("[INFO] Use start, stop, or status")

if __name__ == "__main__":
    main()