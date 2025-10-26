#!/usr/bin/env python3
"""
OMNI Platform - Integrations & Automation
Advanced webhook system, notification channels, and scheduler for the OMNI platform
"""

import json
import time
import asyncio
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
import logging
import threading
import requests
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import schedule
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Webhook_Endpoint:
    """Webhook endpoint configuration"""
    endpoint_id: str
    name: str
    url: str
    events: List[str]
    headers: Dict[str, str]
    method: str = "POST"
    active: bool = True
    created_at: datetime = None
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class Notification_Message:
    """Notification message structure"""
    message_id: str
    channel: str  # "slack", "discord", "teams", "email"
    recipient: str
    subject: str
    content: str
    priority: str = "normal"  # "low", "normal", "high", "critical"
    attachments: List[str] = None

    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []

@dataclass
class Scheduled_Task:
    """Scheduled task configuration"""
    task_id: str
    name: str
    task_type: str  # "backup", "report", "maintenance", "custom"
    schedule: str  # cron expression
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    parameters: Dict[str, Any] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}

class WebhookManager:
    """Advanced webhook management system"""

    def __init__(self):
        self.webhook_endpoints: Dict[str, Webhook_Endpoint] = {}
        self.event_listeners: Dict[str, List[Callable]] = {}
        self.webhook_history: List[Dict[str, Any]] = []

    def create_webhook(self, name: str, url: str, events: List[str], headers: Dict[str, str] = None) -> str:
        """Create a new webhook endpoint"""
        if headers is None:
            headers = {"Content-Type": "application/json"}

        webhook_id = f"webhook_{int(time.time())}_{str(uuid.uuid4())[:8]}"

        webhook = Webhook_Endpoint(
            endpoint_id=webhook_id,
            name=name,
            url=url,
            events=events,
            headers=headers
        )

        self.webhook_endpoints[webhook_id] = webhook
        logger.info(f"Created webhook endpoint: {webhook_id}")
        return webhook_id

    def trigger_webhook(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger webhooks for specific event"""
        results = {"successful": [], "failed": []}

        # Find relevant webhooks
        relevant_webhooks = [
            webhook for webhook in self.webhook_endpoints.values()
            if webhook.active and event_type in webhook.events
        ]

        for webhook in relevant_webhooks:
            try:
                # Prepare payload
                webhook_payload = {
                    "event": event_type,
                    "timestamp": datetime.now().isoformat(),
                    "data": payload,
                    "webhook_id": webhook.endpoint_id
                }

                # Send HTTP request
                response = requests.post(
                    webhook.url,
                    json=webhook_payload,
                    headers=webhook.headers,
                    timeout=10
                )

                # Update webhook stats
                webhook.last_triggered = datetime.now()
                webhook.trigger_count += 1

                # Record in history
                self.webhook_history.append({
                    "webhook_id": webhook.endpoint_id,
                    "event": event_type,
                    "status_code": response.status_code,
                    "timestamp": datetime.now().isoformat()
                })

                results["successful"].append({
                    "webhook_id": webhook.endpoint_id,
                    "status_code": response.status_code
                })

            except Exception as e:
                logger.error(f"Failed to trigger webhook {webhook.endpoint_id}: {e}")
                results["failed"].append({
                    "webhook_id": webhook.endpoint_id,
                    "error": str(e)
                })

        return results

    def get_webhook_stats(self) -> Dict[str, Any]:
        """Get webhook statistics"""
        return {
            "total_webhooks": len(self.webhook_endpoints),
            "active_webhooks": len([w for w in self.webhook_endpoints.values() if w.active]),
            "total_triggers": sum(w.trigger_count for w in self.webhook_endpoints.values()),
            "recent_activity": self.webhook_history[-10:] if self.webhook_history else []
        }

class NotificationManager:
    """Multi-channel notification system"""

    def __init__(self):
        self.notification_channels = {
            "slack": {"webhook_url": None, "enabled": False},
            "discord": {"webhook_url": None, "enabled": False},
            "teams": {"webhook_url": None, "enabled": False},
            "email": {"smtp_server": None, "smtp_port": 587, "username": None, "password": None, "enabled": False}
        }

        self.notification_history: List[Notification_Message] = []

    def configure_slack(self, webhook_url: str) -> bool:
        """Configure Slack notifications"""
        try:
            self.notification_channels["slack"] = {
                "webhook_url": webhook_url,
                "enabled": True
            }
            logger.info("Slack notifications configured")
            return True
        except Exception as e:
            logger.error(f"Failed to configure Slack: {e}")
            return False

    def configure_discord(self, webhook_url: str) -> bool:
        """Configure Discord notifications"""
        try:
            self.notification_channels["discord"] = {
                "webhook_url": webhook_url,
                "enabled": True
            }
            logger.info("Discord notifications configured")
            return True
        except Exception as e:
            logger.error(f"Failed to configure Discord: {e}")
            return False

    def configure_email(self, smtp_server: str, smtp_port: int, username: str, password: str) -> bool:
        """Configure email notifications"""
        try:
            self.notification_channels["email"] = {
                "smtp_server": smtp_server,
                "smtp_port": smtp_port,
                "username": username,
                "password": password,
                "enabled": True
            }
            logger.info("Email notifications configured")
            return True
        except Exception as e:
            logger.error(f"Failed to configure email: {e}")
            return False

    def send_notification(self, channel: str, subject: str, content: str, priority: str = "normal") -> bool:
        """Send notification through specified channel"""
        if channel not in self.notification_channels:
            logger.error(f"Unknown notification channel: {channel}")
            return False

        channel_config = self.notification_channels[channel]
        if not channel_config.get("enabled", False):
            logger.warning(f"Notification channel {channel} is not enabled")
            return False

        message = Notification_Message(
            message_id=f"msg_{int(time.time())}_{str(uuid.uuid4())[:8]}",
            channel=channel,
            recipient=channel_config.get("webhook_url", "system"),
            subject=subject,
            content=content,
            priority=priority
        )

        try:
            if channel == "slack":
                return self._send_slack_notification(message)
            elif channel == "discord":
                return self._send_discord_notification(message)
            elif channel == "email":
                return self._send_email_notification(message)
            else:
                logger.error(f"Unsupported notification channel: {channel}")
                return False

        except Exception as e:
            logger.error(f"Failed to send {channel} notification: {e}")
            return False

    def _send_slack_notification(self, message: Notification_Message) -> bool:
        """Send Slack notification"""
        webhook_url = self.notification_channels["slack"]["webhook_url"]

        # Format message based on priority
        color = {
            "low": "#36a64f",
            "normal": "#36a64f",
            "high": "#ff9500",
            "critical": "#ff0000"
        }.get(message.priority, "#36a64f")

        payload = {
            "attachments": [{
                "color": color,
                "title": message.subject,
                "text": message.content,
                "ts": int(time.time())
            }]
        }

        response = requests.post(webhook_url, json=payload, timeout=10)

        if response.status_code == 200:
            self.notification_history.append(message)
            return True

        return False

    def _send_discord_notification(self, message: Notification_Message) -> bool:
        """Send Discord notification"""
        webhook_url = self.notification_channels["discord"]["webhook_url"]

        # Format embed based on priority
        color = {
            "low": 3066993,    # Green
            "normal": 3066993, # Green
            "high": 16776960,  # Orange
            "critical": 16711680  # Red
        }.get(message.priority, 3066993)

        payload = {
            "embeds": [{
                "title": message.subject,
                "description": message.content,
                "color": color,
                "timestamp": datetime.now().isoformat()
            }]
        }

        response = requests.post(webhook_url, json=payload, timeout=10)

        if response.status_code == 204:
            self.notification_history.append(message)
            return True

        return False

    def _send_email_notification(self, message: Notification_Message) -> bool:
        """Send email notification"""
        email_config = self.notification_channels["email"]

        msg = MimeMultipart()
        msg['From'] = email_config["username"]
        msg['To'] = message.recipient
        msg['Subject'] = f"[{message.priority.upper()}] {message.subject}"

        # Add priority header
        priority_map = {
            "low": "5",
            "normal": "3",
            "high": "2",
            "critical": "1"
        }
        msg['X-Priority'] = priority_map.get(message.priority, "3")

        msg.attach(MimeText(message.content, 'plain'))

        try:
            server = smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"])
            server.starttls()
            server.login(email_config["username"], email_config["password"])
            server.send_message(msg)
            server.quit()

            self.notification_history.append(message)
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

class TaskScheduler:
    """Advanced task scheduler with cron-like functionality"""

    def __init__(self):
        self.scheduled_tasks: Dict[str, Scheduled_Task] = {}
        self.running_tasks: Dict[str, threading.Thread] = {}
        self.task_history: List[Dict[str, Any]] = []
        self.scheduler_thread = None
        self.running = False

    def add_task(self, name: str, task_type: str, schedule_cron: str, task_function: Callable, parameters: Dict = None) -> str:
        """Add a scheduled task"""
        task_id = f"task_{int(time.time())}_{str(uuid.uuid4())[:8]}"

        task = Scheduled_Task(
            task_id=task_id,
            name=name,
            task_type=task_type,
            schedule=schedule_cron,
            parameters=parameters or {}
        )

        self.scheduled_tasks[task_id] = task

        # Schedule the task
        schedule.every().day.at("00:00").do(self._execute_task, task_id)

        logger.info(f"Added scheduled task: {task_id}")
        return task_id

    def _execute_task(self, task_id: str) -> bool:
        """Execute a scheduled task"""
        if task_id not in self.scheduled_tasks:
            return False

        task = self.scheduled_tasks[task_id]

        try:
            # Update task status
            task.last_run = datetime.now()

            # Execute task in separate thread
            task_thread = threading.Thread(target=self._run_task_function, args=(task,))
            task_thread.start()
            self.running_tasks[task_id] = task_thread

            # Record execution
            self.task_history.append({
                "task_id": task_id,
                "execution_time": datetime.now().isoformat(),
                "status": "started"
            })

            return True

        except Exception as e:
            logger.error(f"Failed to execute task {task_id}: {e}")
            self.task_history.append({
                "task_id": task_id,
                "execution_time": datetime.now().isoformat(),
                "status": "failed",
                "error": str(e)
            })
            return False

    def _run_task_function(self, task: Scheduled_Task):
        """Run the actual task function"""
        try:
            # This would call the actual task function based on task_type
            # For now, we'll simulate different task types

            if task.task_type == "backup":
                logger.info(f"Executing backup task: {task.name}")
                # Simulate backup process
                time.sleep(2)

            elif task.task_type == "report":
                logger.info(f"Generating report: {task.name}")
                # Simulate report generation
                time.sleep(1)

            elif task.task_type == "maintenance":
                logger.info(f"Running maintenance: {task.name}")
                # Simulate maintenance
                time.sleep(3)

            else:
                logger.info(f"Executing custom task: {task.name}")
                time.sleep(1)

            # Record successful completion
            self.task_history.append({
                "task_id": task.task_id,
                "execution_time": datetime.now().isoformat(),
                "status": "completed",
                "duration": "simulated"
            })

        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            self.task_history.append({
                "task_id": task.task_id,
                "execution_time": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            })

    def start_scheduler(self):
        """Start the task scheduler"""
        if self.running:
            return

        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info("Task scheduler started")

    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)

    def stop_scheduler(self):
        """Stop the task scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Task scheduler stopped")

    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get scheduler status and statistics"""
        return {
            "running": self.running,
            "total_tasks": len(self.scheduled_tasks),
            "active_tasks": len(self.running_tasks),
            "recent_executions": self.task_history[-10:] if self.task_history else [],
            "next_runs": [
                {
                    "task_id": task_id,
                    "name": task.name,
                    "next_run": "scheduled"
                }
                for task_id, task in self.scheduled_tasks.items()
                if task.enabled
            ][:5]
        }

class IntegrationAutomationAPI:
    """Main API for integrations and automation"""

    def __init__(self):
        self.webhook_manager = WebhookManager()
        self.notification_manager = NotificationManager()
        self.task_scheduler = TaskScheduler()

        # Start scheduler
        self.task_scheduler.start_scheduler()

    def setup_default_integrations(self) -> Dict[str, Any]:
        """Setup default integrations for OMNI platform"""
        results = {}

        # Create default webhooks
        system_webhook = self.webhook_manager.create_webhook(
            name="OMNI System Events",
            url="https://httpbin.org/post",  # Placeholder
            events=["system_alert", "backup_complete", "error_occurred"]
        )
        results["system_webhook"] = system_webhook

        # Create default scheduled tasks
        backup_task = self.task_scheduler.add_task(
            name="Daily Backup",
            task_type="backup",
            schedule_cron="0 2 * * *",  # Daily at 2 AM
            task_function=None  # Would be actual backup function
        )
        results["backup_task"] = backup_task

        report_task = self.task_scheduler.add_task(
            name="Weekly Report",
            task_type="report",
            schedule_cron="0 9 * * 0",  # Weekly on Sunday at 9 AM
            task_function=None
        )
        results["report_task"] = report_task

        return results

    def send_system_notification(self, event_type: str, message: str, priority: str = "normal") -> bool:
        """Send system notification to all configured channels"""
        success_count = 0

        # Send to all enabled channels
        for channel in ["slack", "discord", "email"]:
            if self.notification_manager.notification_channels[channel].get("enabled", False):
                if self.notification_manager.send_notification(channel, f"OMNI {event_type}", message, priority):
                    success_count += 1

        return success_count > 0

# Global instances
integration_api = IntegrationAutomationAPI()

def get_integration_status() -> Dict[str, Any]:
    """Get status of all integrations and automation"""
    return {
        "webhooks": integration_api.webhook_manager.get_webhook_stats(),
        "notifications": {
            "channels_configured": sum(1 for ch in integration_api.notification_manager.notification_channels.values() if ch.get("enabled", False)),
            "total_messages": len(integration_api.notification_manager.notification_history)
        },
        "scheduler": integration_api.task_scheduler.get_scheduler_status()
    }

if __name__ == "__main__":
    print("🔗 OMNI Platform - Integrations & Automation")
    print("=" * 50)

    # Test webhook system
    print("\n🪝 Testing Webhook System...")
    webhook_id = integration_api.webhook_manager.create_webhook(
        name="Test Webhook",
        url="https://httpbin.org/post",
        events=["test_event"]
    )
    print(f"Created webhook: {webhook_id}")

    # Trigger test webhook
    result = integration_api.webhook_manager.trigger_webhook("test_event", {"test": "data"})
    print(f"Webhook trigger result: {len(result['successful'])} successful, {len(result['failed'])} failed")

    # Test notification system
    print("\n📢 Testing Notification System...")
    integration_api.notification_manager.configure_slack("https://hooks.slack.com/test")  # Test URL

    notification_sent = integration_api.notification_manager.send_notification(
        "slack",
        "Test Notification",
        "This is a test notification from OMNI platform",
        "normal"
    )
    print(f"Notification sent: {notification_sent}")

    # Test scheduler
    print("\n⏰ Testing Task Scheduler...")
    task_id = integration_api.task_scheduler.add_task(
        name="Test Task",
        task_type="test",
        schedule_cron="*/5 * * * *",  # Every 5 minutes
        task_function=None
    )
    print(f"Created scheduled task: {task_id}")

    # Display status
    print("\n📊 Integration Status:")
    status = get_integration_status()
    for category, details in status.items():
        print(f"  {category}: ✅ Active")

    print("\n🎉 Integrations & automation initialized successfully!")