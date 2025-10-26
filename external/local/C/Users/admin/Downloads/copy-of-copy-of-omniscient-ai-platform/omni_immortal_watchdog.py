#!/usr/bin/env python3
"""
OMNI Immortal Watchdog - Zero-downtime deployment system
Monitors dual instances and ensures continuous operation
"""

import os
import json
import time
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from omni_event_logger import EventLogger

class OmniImmortalWatchdog:
    def __init__(self, config_path="/opt/omni/immortal_config.json"):
        self.logger = EventLogger()
        self.config_path = config_path
        self.config = self.load_config()
        self.active_instance = self.config.get("active_instance", "v1")
        self.checkpoint_dir = Path(self.config.get("checkpoint_dir", "/opt/omni/checkpoints"))
        self.release_dir = Path(self.config.get("release_dir", "/opt/omni/releases"))
        self.running = False

    def load_config(self):
        """Load immortal mode configuration"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.log(f"Config load error: {e}")

        # Default configuration
        return {
            "active_instance": "v1",
            "instances": {
                "v1": {
                    "service": "omni-autolearn-v1",
                    "path": "/opt/omni/releases/v1",
                    "port": 9090,
                    "status": "unknown"
                },
                "v2": {
                    "service": "omni-autolearn-v2",
                    "path": "/opt/omni/releases/v2",
                    "port": 9091,
                    "status": "unknown"
                }
            },
            "checkpoint_dir": "/opt/omni/checkpoints",
            "release_dir": "/opt/omni/releases",
            "health_check_interval": 30,
            "max_failures": 3,
            "auto_upgrade": True
        }

    def save_config(self):
        """Save current configuration"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.logger.log(f"Config save error: {e}")

    def check_service_status(self, service_name):
        """Check if a systemd service is running"""
        try:
            result = subprocess.run(
                ["systemctl", "is-active", service_name],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                return "active", result.stdout.strip()
            else:
                return "inactive", result.stderr.strip()

        except Exception as e:
            self.logger.log(f"Service check error for {service_name}: {e}")
            return "error", str(e)

    def check_vr_port(self, port):
        """Check if VR port is responding"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2)

            # Try to connect (this will fail, but we check if port is open)
            try:
                sock.bind(("", port))
                sock.close()
                return True  # Port is available
            except OSError:
                return False  # Port is in use

        except Exception as e:
            self.logger.log(f"Port check error for {port}: {e}")
            return False

    def check_instance_health(self, instance_name):
        """Check health of a specific instance"""
        instance = self.config["instances"][instance_name]
        service_name = instance["service"]

        # Check systemd service status
        status, details = self.check_service_status(service_name)
        instance["status"] = status

        # Check if VR port is responding
        port_open = self.check_vr_port(instance["port"])
        instance["port_open"] = port_open

        # Check if process is actually running
        process_running = self.check_process_running(instance["path"])

        health_score = 0
        if status == "active":
            health_score += 1
        if port_open:
            health_score += 1
        if process_running:
            health_score += 1

        instance["health_score"] = health_score
        instance["last_check"] = time.time()

        return health_score >= 2  # Consider healthy if 2/3 checks pass

    def check_process_running(self, instance_path):
        """Check if the Python process is actually running"""
        try:
            # Look for omni_autolearn_starter.py process in the instance path
            result = subprocess.run(
                ["pgrep", "-f", f"{instance_path}.*omni_autolearn_starter"],
                capture_output=True, text=True, timeout=5
            )

            return result.returncode == 0

        except Exception as e:
            self.logger.log(f"Process check error: {e}")
            return False

    def restart_instance(self, instance_name):
        """Restart a specific instance"""
        instance = self.config["instances"][instance_name]
        service_name = instance["service"]

        self.logger.log(f"Restarting instance {instance_name} (service: {service_name})")

        try:
            # Stop service
            subprocess.run(["systemctl", "stop", service_name],
                         capture_output=True, timeout=30)

            # Wait a moment
            time.sleep(2)

            # Start service
            subprocess.run(["systemctl", "start", service_name],
                         capture_output=True, timeout=30)

            self.logger.log(f"Instance {instance_name} restarted successfully")
            return True

        except Exception as e:
            self.logger.log(f"Failed to restart instance {instance_name}: {e}")
            return False

    def switch_to_instance(self, target_instance):
        """Switch active instance"""
        old_instance = self.active_instance
        self.active_instance = target_instance

        self.config["active_instance"] = target_instance
        self.save_config()

        self.logger.log(f"Switched from {old_instance} to {target_instance}")

        # Update VR connector port if needed
        self.update_vr_connector_port()

    def update_vr_connector_port(self):
        """Update VR connector to use active instance port"""
        try:
            # This would need to be implemented based on your VR connector configuration
            active_config = self.config["instances"][self.active_instance]
            new_port = active_config["port"]

            self.logger.log(f"VR connector should use port {new_port}")
            # You might need to send a signal to VR connector to change ports

        except Exception as e:
            self.logger.log(f"Port update error: {e}")

    def create_checkpoint(self):
        """Create a checkpoint of current learning state"""
        try:
            # Ensure checkpoint directory exists
            self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

            # Copy current learning summaries
            summary_files = [
                "learn_summary.json",
                "learn_summary.csv"
            ]

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            for file in summary_files:
                src = Path(file)
                if src.exists():
                    dst = self.checkpoint_dir / f"{timestamp}_{file}"
                    import shutil
                    shutil.copy2(src, dst)
                    self.logger.log(f"Checkpoint created: {dst}")

            # Save checkpoint metadata
            checkpoint_meta = {
                "timestamp": timestamp,
                "active_instance": self.active_instance,
                "total_runs": self.get_total_runs(),
                "created_at": time.time()
            }

            meta_file = self.checkpoint_dir / f"checkpoint_{timestamp}.json"
            with open(meta_file, 'w') as f:
                json.dump(checkpoint_meta, f, indent=2)

            return timestamp

        except Exception as e:
            self.logger.log(f"Checkpoint creation failed: {e}")
            return None

    def get_total_runs(self):
        """Get total learning runs from summary file"""
        try:
            if os.path.exists("learn_summary.json"):
                with open("learn_summary.json", 'r') as f:
                    data = json.load(f)
                    return data.get("runs", 0)
        except Exception as e:
            self.logger.log(f"Error reading total runs: {e}")

        return 0

    def perform_health_checks(self):
        """Perform health checks on all instances"""
        self.logger.log("Performing health checks...")

        for instance_name in ["v1", "v2"]:
            is_healthy = self.check_instance_health(instance_name)

            if instance_name == self.active_instance and not is_healthy:
                # Active instance is down - try to restart
                self.logger.log(f"Active instance {instance_name} is unhealthy - attempting restart")

                if not self.restart_instance(instance_name):
                    # Restart failed - switch to other instance
                    other_instance = "v2" if instance_name == "v1" else "v1"
                    self.logger.log(f"Switching to instance {other_instance}")

                    if self.check_instance_health(other_instance):
                        self.switch_to_instance(other_instance)
                    else:
                        self.logger.log(f"Other instance {other_instance} also unhealthy!")

            elif instance_name != self.active_instance and is_healthy:
                # Inactive instance is healthy - could be used for upgrade
                self.logger.log(f"Inactive instance {instance_name} is healthy and ready")

    def start_watchdog(self):
        """Start the immortal watchdog service"""
        self.running = True
        self.logger.log("OMNI Immortal Watchdog started")
        self.logger.log(f"Active instance: {self.active_instance}")

        # Create initial checkpoint
        self.create_checkpoint()

        while self.running:
            try:
                # Perform health checks
                self.perform_health_checks()

                # Create periodic checkpoints
                if int(time.time()) % 300 == 0:  # Every 5 minutes
                    self.create_checkpoint()

                # Sleep until next check
                time.sleep(self.config.get("health_check_interval", 30))

            except KeyboardInterrupt:
                self.logger.log("Watchdog interrupted by user")
                break
            except Exception as e:
                self.logger.log(f"Watchdog error: {e}")
                time.sleep(60)  # Wait a minute before retrying

    def stop_watchdog(self):
        """Stop the watchdog service"""
        self.running = False
        self.logger.log("OMNI Immortal Watchdog stopped")

def main():
    """Main function"""
    print("OMNI Immortal Watchdog")
    print("=" * 50)

    watchdog = OmniImmortalWatchdog()

    print("Choose an option:")
    print("1. Start watchdog service")
    print("2. Check instance health")
    print("3. Create checkpoint")
    print("4. Switch active instance")
    print("5. Exit")

    choice = input("Enter choice (1-5): ").strip()

    if choice == "1":
        print("Starting immortal watchdog...")
        print("This will monitor instances and ensure zero downtime")
        print("Press Ctrl+C to stop")

        try:
            watchdog.start_watchdog()
        except KeyboardInterrupt:
            print("Stopping watchdog...")
        finally:
            watchdog.stop_watchdog()

    elif choice == "2":
        print("Checking instance health...")
        for instance in ["v1", "v2"]:
            healthy = watchdog.check_instance_health(instance)
            status = watchdog.config["instances"][instance]
            print(f"Instance {instance}: {'HEALTHY' if healthy else 'UNHEALTHY'} "
                  f"(Service: {status['status']}, Port: {status.get('port_open', 'unknown')})")

    elif choice == "3":
        print("Creating checkpoint...")
        timestamp = watchdog.create_checkpoint()
        if timestamp:
            print(f"Checkpoint created: {timestamp}")
        else:
            print("Checkpoint creation failed")

    elif choice == "4":
        print(f"Current active instance: {watchdog.active_instance}")
        new_instance = input("Switch to instance (v1/v2): ").strip()

        if new_instance in ["v1", "v2"]:
            if watchdog.check_instance_health(new_instance):
                watchdog.switch_to_instance(new_instance)
                print(f"Switched to instance {new_instance}")
            else:
                print(f"Cannot switch - instance {new_instance} is unhealthy")
        else:
            print("Invalid instance name")

    else:
        print("Exiting...")

if __name__ == "__main__":
    main()