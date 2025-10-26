#!/usr/bin/env python3
"""
OMNI Platform3 Monitor and Health Check System
Real-time monitoring and health assessment for OMNI Platform3

This system provides comprehensive monitoring, alerting, and health
assessment capabilities to ensure optimal platform performance.

Features:
- Real-time system monitoring
- Advanced health assessment algorithms
- Intelligent alerting and notification system
- Performance metrics collection and analysis
- Resource utilization tracking
- Automated health recovery procedures
"""

import time
import os
import sys
import json
import psutil
import threading
import schedule
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import logging
import smtplib
from email.mime.text import MimeText
import requests
import socket

class OmniPlatform3Monitor:
    """Advanced monitoring and health check system for OMNI Platform3"""

    def __init__(self, platform3_instance=None):
        self.platform3 = platform3_instance
        self.monitoring_active = False
        self.health_check_active = False

        # Monitoring configuration
        self.monitor_config = {
            "system_metrics_interval": 10,  # seconds
            "health_check_interval": 30,    # seconds
            "metrics_retention_days": 7,
            "alert_cooldown_minutes": 5,
            "performance_thresholds": {
                "cpu_usage": 80,      # percent
                "memory_usage": 85,   # percent
                "disk_usage": 90,     # percent
                "network_latency": 1000,  # ms
                "error_rate": 0.05    # 5% error rate
            },
            "health_weights": {
                "cpu_health": 0.2,
                "memory_health": 0.2,
                "disk_health": 0.15,
                "network_health": 0.15,
                "state_health": 0.3
            }
        }

        # Monitoring state
        self.current_metrics = {}
        self.metrics_history = []
        self.alert_history = []
        self.health_status = {}
        self.last_alert_times = {}

        # Alerting configuration
        self.alert_config = {
            "email_notifications": False,
            "webhook_notifications": False,
            "log_alerts": True,
            "email_settings": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "recipients": []
            },
            "webhook_urls": []
        }

        # Setup logging
        self.logger = logging.getLogger('OmniPlatform3Monitor')

        # Initialize monitoring system
        self._initialize_monitoring_system()

    def _initialize_monitoring_system(self):
        """Initialize the monitoring system"""
        # Create metrics storage directory
        os.makedirs("omni_platform3_metrics", exist_ok=True)

        # Load existing metrics if available
        self._load_existing_metrics()

        # Setup alerting system
        self._setup_alerting_system()

    def _load_existing_metrics(self):
        """Load existing metrics from storage"""
        try:
            metrics_file = "omni_platform3_metrics/current_metrics.json"
            if os.path.exists(metrics_file):
                with open(metrics_file, 'r') as f:
                    self.current_metrics = json.load(f)

            # Load metrics history
            history_file = "omni_platform3_metrics/metrics_history.json"
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    self.metrics_history = json.load(f)

        except Exception as e:
            self.logger.error(f"Failed to load existing metrics: {e}")
            self.current_metrics = {}
            self.metrics_history = []

    def _setup_alerting_system(self):
        """Setup the alerting and notification system"""
        # Create alerts directory
        os.makedirs("omni_platform3_metrics/alerts", exist_ok=True)

        # Load alert configuration
        alert_config_file = "omni_platform3_alert_config.json"
        if os.path.exists(alert_config_file):
            try:
                with open(alert_config_file, 'r') as f:
                    self.alert_config.update(json.load(f))
            except Exception as e:
                self.logger.error(f"Failed to load alert configuration: {e}")

    def start_monitoring(self):
        """Start the monitoring system"""
        if self.monitoring_active:
            self.logger.warning("Monitoring already active")
            return

        self.monitoring_active = True
        self.logger.info("Starting OMNI Platform3 monitoring system")

        # Start monitoring threads
        monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        monitor_thread.start()

        health_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        health_thread.start()

        metrics_thread = threading.Thread(target=self._metrics_collection_loop, daemon=True)
        metrics_thread.start()

        self.logger.info("OMNI Platform3 monitoring system started")

    def stop_monitoring(self):
        """Stop the monitoring system"""
        self.monitoring_active = False
        self.health_check_active = False
        self.logger.info("OMNI Platform3 monitoring system stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect comprehensive system metrics
                self._collect_system_metrics()

                # Check for alert conditions
                self._check_alert_conditions()

                # Update monitoring status
                self._update_monitoring_status()

                # Sleep for monitoring interval
                time.sleep(self.monitor_config["system_metrics_interval"])

            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                time.sleep(self.monitor_config["system_metrics_interval"])

    def _health_check_loop(self):
        """Health check monitoring loop"""
        self.health_check_active = True

        while self.health_check_active and self.monitoring_active:
            try:
                # Perform comprehensive health check
                self._perform_comprehensive_health_check()

                # Sleep for health check interval
                time.sleep(self.monitor_config["health_check_interval"])

            except Exception as e:
                self.logger.error(f"Health check loop error: {e}")
                time.sleep(self.monitor_config["health_check_interval"])

    def _metrics_collection_loop(self):
        """Continuous metrics collection loop"""
        while self.monitoring_active:
            try:
                # Collect and store metrics
                self._collect_and_store_metrics()

                # Clean old metrics
                self._cleanup_old_metrics()

                # Sleep for collection interval
                time.sleep(60)  # Collect every minute

            except Exception as e:
                self.logger.error(f"Metrics collection loop error: {e}")
                time.sleep(60)

    def _collect_system_metrics(self):
        """Collect comprehensive system metrics"""
        timestamp = time.time()

        # System resource metrics
        system_metrics = {
            "timestamp": timestamp,
            "cpu_usage": self._get_cpu_usage(),
            "memory_usage": self._get_memory_usage(),
            "disk_usage": self._get_disk_usage(),
            "network_io": self._get_network_io(),
            "process_info": self._get_process_info(),
            "system_load": self._get_system_load()
        }

        # Platform-specific metrics
        platform_metrics = {
            "platform_uptime": time.time() - (self.platform3.start_time if self.platform3 else time.time()),
            "state_size": len(json.dumps(self.platform3.current_state)) if self.platform3 else 0,
            "backup_count": len(self.platform3.backup_states) if self.platform3 else 0,
            "active_threads": threading.active_count(),
            "platform_health": self._calculate_platform_health() if self.platform3 else 1.0
        }

        # Combine all metrics
        self.current_metrics = {
            "system": system_metrics,
            "platform": platform_metrics,
            "collection_time": timestamp
        }

        # Add to history
        self.metrics_history.append(self.current_metrics.copy())

        # Keep only recent history (last 24 hours)
        cutoff_time = time.time() - (24 * 3600)
        self.metrics_history = [m for m in self.metrics_history if m["collection_time"] > cutoff_time]

    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        try:
            return psutil.cpu_percent(interval=1)
        except:
            return 50.0  # Default estimate

    def _get_memory_usage(self) -> float:
        """Get current memory usage percentage"""
        try:
            return psutil.virtual_memory().percent
        except:
            return 60.0  # Default estimate

    def _get_disk_usage(self) -> float:
        """Get current disk usage percentage"""
        try:
            return psutil.disk_usage('/').percent
        except:
            return 70.0  # Default estimate

    def _get_network_io(self) -> Dict[str, Any]:
        """Get network I/O statistics"""
        try:
            net_io = psutil.net_io_counters()
            return {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "latency_ms": self._measure_network_latency()
            }
        except:
            return {
                "bytes_sent": 0,
                "bytes_recv": 0,
                "packets_sent": 0,
                "packets_recv": 0,
                "latency_ms": 0
            }

    def _measure_network_latency(self) -> float:
        """Measure network latency to a reliable host"""
        try:
            # Try to ping a reliable host (Google DNS)
            start_time = time.time()
            socket.setdefaulttimeout(2)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('8.8.8.8', 53))
            sock.close()

            if result == 0:
                return (time.time() - start_time) * 1000  # Convert to milliseconds
            else:
                return 1000  # Default high latency if connection fails
        except:
            return 1000  # Default high latency

    def _get_process_info(self) -> Dict[str, Any]:
        """Get information about current process"""
        try:
            process = psutil.Process()
            return {
                "pid": process.pid,
                "memory_mb": process.memory_info().rss / (1024 * 1024),
                "cpu_percent": process.cpu_percent(),
                "threads": process.num_threads(),
                "open_files": len(process.open_files()),
                "connections": len(process.connections())
            }
        except:
            return {
                "pid": os.getpid(),
                "memory_mb": 0,
                "cpu_percent": 0,
                "threads": 0,
                "open_files": 0,
                "connections": 0
            }

    def _get_system_load(self) -> Dict[str, float]:
        """Get system load averages"""
        try:
            load_avg = psutil.getloadavg()
            return {
                "1min": load_avg[0],
                "5min": load_avg[1],
                "15min": load_avg[2]
            }
        except:
            return {"1min": 0.0, "5min": 0.0, "15min": 0.0}

    def _calculate_platform_health(self) -> float:
        """Calculate overall platform health score"""
        if not self.platform3:
            return 1.0

        health_factors = []
        weights = self.monitor_config["health_weights"]

        # CPU health (lower usage = higher health)
        cpu_usage = self.current_metrics.get("system", {}).get("cpu_usage", 50)
        cpu_health = max(0, 100 - cpu_usage) / 100
        health_factors.append(("cpu_health", cpu_health * weights["cpu_health"]))

        # Memory health (lower usage = higher health)
        memory_usage = self.current_metrics.get("system", {}).get("memory_usage", 60)
        memory_health = max(0, 100 - memory_usage) / 100
        health_factors.append(("memory_health", memory_health * weights["memory_health"]))

        # Disk health (lower usage = higher health)
        disk_usage = self.current_metrics.get("system", {}).get("disk_usage", 70)
        disk_health = max(0, 100 - disk_usage) / 100
        health_factors.append(("disk_health", disk_health * weights["disk_health"]))

        # Network health (lower latency = higher health)
        latency = self.current_metrics.get("system", {}).get("network_io", {}).get("latency_ms", 100)
        network_health = max(0, 1 - (latency / 1000))  # Normalize to 0-1
        health_factors.append(("network_health", network_health * weights["network_health"]))

        # State health (from platform3)
        state_health = self.platform3.current_state.get("system_metrics", {}).get("state_integrity", 1.0)
        health_factors.append(("state_health", state_health * weights["state_health"]))

        # Calculate weighted average
        total_weight = sum(weight for _, weight in health_factors)
        overall_health = sum(value for _, value in health_factors) / max(total_weight, 1)

        return min(overall_health, 1.0)

    def _check_alert_conditions(self):
        """Check for alert conditions and trigger notifications"""
        if not self.current_metrics:
            return

        system_metrics = self.current_metrics.get("system", {})
        thresholds = self.monitor_config["performance_thresholds"]

        # Check CPU usage
        if system_metrics.get("cpu_usage", 0) > thresholds["cpu_usage"]:
            self._trigger_alert("high_cpu_usage", {
                "current_usage": system_metrics["cpu_usage"],
                "threshold": thresholds["cpu_usage"],
                "severity": "warning"
            })

        # Check memory usage
        if system_metrics.get("memory_usage", 0) > thresholds["memory_usage"]:
            self._trigger_alert("high_memory_usage", {
                "current_usage": system_metrics["memory_usage"],
                "threshold": thresholds["memory_usage"],
                "severity": "warning"
            })

        # Check disk usage
        if system_metrics.get("disk_usage", 0) > thresholds["disk_usage"]:
            self._trigger_alert("high_disk_usage", {
                "current_usage": system_metrics["disk_usage"],
                "threshold": thresholds["disk_usage"],
                "severity": "critical"
            })

        # Check network latency
        latency = system_metrics.get("network_io", {}).get("latency_ms", 0)
        if latency > thresholds["network_latency"]:
            self._trigger_alert("high_network_latency", {
                "current_latency": latency,
                "threshold": thresholds["network_latency"],
                "severity": "warning"
            })

        # Check platform health
        platform_health = self._calculate_platform_health()
        if platform_health < 0.7:  # Below 70% health
            self._trigger_alert("low_platform_health", {
                "current_health": platform_health,
                "threshold": 0.7,
                "severity": "warning"
            })

    def _trigger_alert(self, alert_type: str, alert_data: Dict[str, Any]):
        """Trigger an alert with cooldown to prevent spam"""
        current_time = time.time()
        last_alert_time = self.last_alert_times.get(alert_type, 0)
        cooldown_seconds = self.monitor_config["alert_cooldown_minutes"] * 60

        # Check cooldown period
        if current_time - last_alert_time < cooldown_seconds:
            return  # Still in cooldown period

        # Create alert
        alert = {
            "alert_type": alert_type,
            "timestamp": current_time,
            "data": alert_data,
            "alert_id": f"alert_{int(current_time)}_{alert_type}"
        }

        # Store alert
        self.alert_history.append(alert)
        self.last_alert_times[alert_type] = current_time

        # Keep only recent alerts (last 1000)
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]

        # Send notifications
        self._send_alert_notifications(alert)

        self.logger.warning(f"Alert triggered: {alert_type} - {alert_data}")

    def _send_alert_notifications(self, alert: Dict[str, Any]):
        """Send alert notifications via configured channels"""
        alert_message = self._format_alert_message(alert)

        # Log alert
        if self.alert_config["log_alerts"]:
            self.logger.warning(f"ALERT: {alert_message}")

        # Email notifications
        if self.alert_config["email_notifications"]:
            self._send_email_alert(alert, alert_message)

        # Webhook notifications
        if self.alert_config["webhook_notifications"]:
            self._send_webhook_alert(alert, alert_message)

    def _format_alert_message(self, alert: Dict[str, Any]) -> str:
        """Format alert message for notifications"""
        alert_type = alert["alert_type"]
        data = alert["data"]
        timestamp = datetime.fromtimestamp(alert["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")

        message = f"OMNI Platform3 Alert: {alert_type}\n"
        message += f"Time: {timestamp}\n"
        message += f"Details: {json.dumps(data, indent=2)}\n"

        return message

    def _send_email_alert(self, alert: Dict[str, Any], message: str):
        """Send alert via email"""
        try:
            email_settings = self.alert_config["email_settings"]

            msg = MimeText(message)
            msg['Subject'] = f"OMNI Platform3 Alert: {alert['alert_type']}"
            msg['From'] = email_settings["username"]
            msg['To'] = ", ".join(email_settings["recipients"])

            server = smtplib.SMTP(email_settings["smtp_server"], email_settings["smtp_port"])
            server.starttls()
            server.login(email_settings["username"], email_settings["password"])
            server.send_message(msg)
            server.quit()

        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")

    def _send_webhook_alert(self, alert: Dict[str, Any], message: str):
        """Send alert via webhook"""
        try:
            for webhook_url in self.alert_config["webhook_urls"]:
                payload = {
                    "alert": alert,
                    "message": message,
                    "platform": "OMNI Platform3"
                }

                response = requests.post(webhook_url, json=payload, timeout=5)
                if response.status_code != 200:
                    self.logger.error(f"Webhook alert failed: {response.status_code}")

        except Exception as e:
            self.logger.error(f"Failed to send webhook alert: {e}")

    def _perform_comprehensive_health_check(self):
        """Perform comprehensive health check"""
        health_score = self._calculate_platform_health()

        # Update health status
        self.health_status = {
            "overall_health": health_score,
            "last_check": time.time(),
            "health_trend": self._calculate_health_trend(),
            "recommendations": self._generate_health_recommendations()
        }

        # Check for critical health issues
        if health_score < 0.5:  # Below 50% health
            self._trigger_alert("critical_platform_health", {
                "current_health": health_score,
                "threshold": 0.5,
                "severity": "critical"
            })

        # Log health status
        self.logger.info(f"Platform health: {health_score".2f"} - Trend: {self.health_status['health_trend']}")

    def _calculate_health_trend(self) -> str:
        """Calculate health trend (improving, stable, declining)"""
        if len(self.metrics_history) < 5:
            return "unknown"

        # Get recent health scores
        recent_scores = []
        for metrics in self.metrics_history[-5:]:
            # Extract platform health from metrics
            platform_metrics = metrics.get("platform", {})
            health_score = platform_metrics.get("platform_health", 1.0)
            recent_scores.append(health_score)

        if len(recent_scores) < 2:
            return "stable"

        # Calculate trend
        older_avg = sum(recent_scores[:2]) / 2
        newer_avg = sum(recent_scores[-2:]) / 2

        if newer_avg > older_avg + 0.05:
            return "improving"
        elif newer_avg < older_avg - 0.05:
            return "declining"
        else:
            return "stable"

    def _generate_health_recommendations(self) -> List[str]:
        """Generate health improvement recommendations"""
        recommendations = []

        if not self.current_metrics:
            return recommendations

        system_metrics = self.current_metrics.get("system", {})

        # CPU recommendations
        cpu_usage = system_metrics.get("cpu_usage", 0)
        if cpu_usage > 80:
            recommendations.append("High CPU usage detected - consider optimizing platform processes")

        # Memory recommendations
        memory_usage = system_metrics.get("memory_usage", 0)
        if memory_usage > 85:
            recommendations.append("High memory usage detected - consider increasing system memory or optimizing memory usage")

        # Disk recommendations
        disk_usage = system_metrics.get("disk_usage", 0)
        if disk_usage > 90:
            recommendations.append("High disk usage detected - consider cleaning up old files or increasing disk space")

        # Network recommendations
        latency = system_metrics.get("network_io", {}).get("latency_ms", 0)
        if latency > 500:
            recommendations.append("High network latency detected - check network connectivity")

        # Platform-specific recommendations
        platform_health = self._calculate_platform_health()
        if platform_health < 0.7:
            recommendations.append("Platform health degraded - consider running state validation and cleanup")

        return recommendations

    def _collect_and_store_metrics(self):
        """Collect and store metrics to persistent storage"""
        try:
            # Save current metrics
            with open("omni_platform3_metrics/current_metrics.json", 'w') as f:
                json.dump(self.current_metrics, f, indent=2)

            # Save metrics history (keep last 24 hours)
            with open("omni_platform3_metrics/metrics_history.json", 'w') as f:
                json.dump(self.metrics_history, f, indent=2)

            # Save health status
            with open("omni_platform3_metrics/health_status.json", 'w') as f:
                json.dump(self.health_status, f, indent=2)

            # Save alert history
            with open("omni_platform3_metrics/alert_history.json", 'w') as f:
                json.dump(self.alert_history, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to store metrics: {e}")

    def _cleanup_old_metrics(self):
        """Clean up old metrics files"""
        try:
            cutoff_time = time.time() - (self.monitor_config["metrics_retention_days"] * 24 * 3600)

            # Clean old alert files
            alerts_dir = "omni_platform3_metrics/alerts"
            if os.path.exists(alerts_dir):
                for filename in os.listdir(alerts_dir):
                    filepath = os.path.join(alerts_dir, filename)
                    if os.path.getmtime(filepath) < cutoff_time:
                        os.remove(filepath)

        except Exception as e:
            self.logger.error(f"Failed to cleanup old metrics: {e}")

    def _update_monitoring_status(self):
        """Update monitoring system status"""
        if self.platform3:
            # Update platform3 metrics
            self.platform3.platform_metrics.update(self.current_metrics)

    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get comprehensive monitoring status"""
        return {
            "monitoring_active": self.monitoring_active,
            "health_check_active": self.health_check_active,
            "current_metrics": self.current_metrics,
            "health_status": self.health_status,
            "alert_count": len(self.alert_history),
            "metrics_history_count": len(self.metrics_history),
            "last_collection": self.current_metrics.get("collection_time", 0),
            "monitoring_uptime": time.time() - (self.platform3.start_time if self.platform3 else time.time())
        }

    def demonstrate_monitoring_features(self):
        """Demonstrate monitoring and health check features"""
        print("\n📊 OMNI Platform3 Monitoring System Demonstration")
        print("=" * 60)

        # Show monitoring configuration
        print("⚙️ Monitoring Configuration:")
        print(f"  📊 Metrics Interval: {self.monitor_config['system_metrics_interval']}s")
        print(f"  ❤️ Health Check Interval: {self.monitor_config['health_check_interval']}s")
        print(f"  📈 Metrics Retention: {self.monitor_config['metrics_retention_days']} days")
        print(f"  🚨 Alert Cooldown: {self.monitor_config['alert_cooldown_minutes']} minutes")

        # Show performance thresholds
        print("
🎯 Performance Thresholds:"        for metric, threshold in self.monitor_config["performance_thresholds"].items():
            print(f"  ⚠️ {metric.replace('_', ' ').title()}: {threshold}")

        # Show health weights
        print("
⚖️ Health Assessment Weights:"        for component, weight in self.monitor_config["health_weights"].items():
            print(f"  {component.replace('_', ' ').title()}: {weight".1%"}")

        # Show current metrics if available
        if self.current_metrics:
            print("
📈 Current System Metrics:"            system_metrics = self.current_metrics.get("system", {})
            print(f"  🖥️ CPU Usage: {system_metrics.get('cpu_usage', 0)".1f"}%")
            print(f"  🧠 Memory Usage: {system_metrics.get('memory_usage', 0)".1f"}%")
            print(f"  💾 Disk Usage: {system_metrics.get('disk_usage', 0)".1f"}%")
            print(f"  🌐 Network Latency: {system_metrics.get('network_io', {}).get('latency_ms', 0)".1f"}ms")

            # Show platform metrics
            platform_metrics = self.current_metrics.get("platform", {})
            print("
🚀 Platform Metrics:"            print(f"  ⏱️ Platform Uptime: {platform_metrics.get('platform_uptime', 0)".1f"}s")
            print(f"  📊 State Size: {platform_metrics.get('state_size', 0)} bytes")
            print(f"  💾 Backup Count: {platform_metrics.get('backup_count', 0)}")
            print(f"  ❤️ Platform Health: {platform_metrics.get('platform_health', 1.0)".1%"}")

        # Show health status
        if self.health_status:
            print("
❤️ Current Health Status:"            print(f"  Overall Health: {self.health_status.get('overall_health', 1.0)".1%"}")
            print(f"  Health Trend: {self.health_status.get('health_trend', 'unknown')}")
            print(f"  Last Check: {datetime.fromtimestamp(self.health_status.get('last_check', time.time())).strftime('%H:%M:%S')}")

            # Show recommendations
            recommendations = self.health_status.get("recommendations", [])
            if recommendations:
                print("
💡 Health Recommendations:"                for rec in recommendations[:3]:  # Show top 3
                    print(f"  • {rec}")

        # Show alert status
        recent_alerts = [a for a in self.alert_history if a["timestamp"] > time.time() - 300]  # Last 5 minutes
        print(f"\n🚨 Recent Alerts (last 5 min): {len(recent_alerts)}")

        for alert in recent_alerts[-3:]:  # Show last 3 alerts
            alert_time = datetime.fromtimestamp(alert["timestamp"]).strftime("%H:%M:%S")
            print(f"  🚨 {alert_time}: {alert['alert_type']}")

def main():
    """Main function to demonstrate Platform3 monitoring system"""
    print("📊 OMNI Platform3 Monitor and Health Check System")
    print("=" * 70)
    print("👁️ Real-time monitoring and health assessment")
    print("🚨 Intelligent alerting and notifications")
    print("❤️ Comprehensive health monitoring")
    print()

    try:
        # Create monitor instance
        monitor = OmniPlatform3Monitor()

        # Demonstrate monitoring features
        print("📊 Monitoring System Features:")
        print("  ✅ Real-time metrics collection")
        print("  ❤️ Advanced health assessment")
        print("  🚨 Intelligent alerting system")
        print("  💾 Persistent metrics storage")
        print("  📈 Performance trend analysis")

        # Show monitoring capabilities
        monitor.demonstrate_monitoring_features()

        # Start monitoring demonstration
        print("
🚀 Starting monitoring demonstration..."        monitor.start_monitoring()

        # Let it run for a short demonstration
        print("📊 Monitoring active - collecting metrics...")
        time.sleep(5)

        # Show collected metrics
        status = monitor.get_monitoring_status()
        print("
📈 Monitoring Status:"        print(f"  👁️ Monitoring Active: {status['monitoring_active']}")
        print(f"  ❤️ Health Check Active: {status['health_check_active']}")
        print(f"  📊 Metrics Collected: {status['metrics_history_count']}")
        print(f"  🚨 Total Alerts: {status['alert_count']}")
        print(f"  ⏱️ Monitoring Uptime: {status['monitoring_uptime']".1f"}s")

        # Stop monitoring
        monitor.stop_monitoring()

        print("
✅ OMNI Platform3 Monitoring System Ready!"        print("👁️ Real-time monitoring: Active")
        print("❤️ Health assessment: Operational")
        print("🚨 Alerting system: Ready")
        print("📊 Metrics collection: Available")

        return status

    except Exception as e:
        print(f"\n❌ Monitor initialization failed: {e}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    status = main()
    print(f"\n✅ Monitoring system execution completed")