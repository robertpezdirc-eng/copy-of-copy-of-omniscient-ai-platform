#!/usr/bin/env python3
"""
OMNI PLATFORM - COMPLETE DEPLOYMENT SYSTEM
Professional deployment and management system for the entire Omni AI platform
"""

import asyncio
import json
import time
import subprocess
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import threading
import queue
import logging
import argparse
from dataclasses import dataclass, asdict
import paramiko
import requests
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('omni_deployment.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DeploymentConfig:
    """Configuration for Omni platform deployment"""
    project_id: str = "refined-graph-471712-n9"
    primary_instance: str = "omni-cpu-optimized"
    storage_instance: str = "omni-storage-node"
    zone: str = "us-central1-c"
    dashboard_port: int = 8080
    api_port: int = 8000
    enable_gpu: bool = False
    enable_monitoring: bool = True
    enable_backup: bool = True

class OmniPlatformDeployer:
    """
    Complete deployment system for the Omni AI platform
    """

    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.ssh_clients: Dict[str, paramiko.SSHClient] = {}
        self.deployment_status = "initializing"

    def wait_for_ssh_availability(self, instance_name: str, max_wait: int = 300) -> bool:
        """Wait for SSH to become available on instance"""
        logger.info(f"Waiting for SSH availability on {instance_name}...")

        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                client = self._create_ssh_client()
                client.connect(
                    hostname=self._get_instance_ip(instance_name),
                    username='omni_user',
                    timeout=10
                )

                # Test connection
                stdin, stdout, stderr = client.exec_command('echo "SSH connection successful"')
                if stdout.read().decode().strip() == "SSH connection successful":
                    logger.info(f"SSH available on {instance_name}")
                    self.ssh_clients[instance_name] = client
                    return True

            except Exception as e:
                logger.debug(f"SSH not ready on {instance_name}: {e}")
                time.sleep(10)
                continue

        logger.error(f"SSH not available on {instance_name} after {max_wait} seconds")
        return False

    def _create_ssh_client(self) -> paramiko.SSHClient:
        """Create and configure SSH client"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        return client

    def _get_instance_ip(self, instance_name: str) -> str:
        """Get external IP of instance"""
        try:
            result = subprocess.run([
                'gcloud', 'compute', 'instances', 'describe', instance_name,
                '--zone', self.config.zone,
                '--format=get(networkInterfaces[0].accessConfigs[0].natIP)'
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                raise Exception(f"Failed to get IP for {instance_name}")
        except Exception as e:
            logger.error(f"Error getting instance IP: {e}")
            return "localhost"

    def setup_ssh_user_and_keys(self, instance_name: str):
        """Set up SSH user and keys on instance"""
        logger.info(f"Setting up SSH user on {instance_name}...")

        try:
            # Create omni user
            commands = [
                'sudo useradd -m -s /bin/bash omni_user',
                'sudo usermod -aG sudo omni_user',
                'sudo mkdir -p /home/omni_user/.ssh',
                'sudo chown omni_user:omni_user /home/omni_user/.ssh',
                'echo "omni_user ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/omni_user',
                'sudo chmod 0440 /etc/sudoers.d/omni_user'
            ]

            for cmd in commands:
                stdin, stdout, stderr = self.ssh_clients[instance_name].exec_command(cmd)
                stdout.read()  # Wait for completion

            # Copy SSH public key
            with open(os.path.expanduser('~/.ssh/id_rsa.pub'), 'r') as f:
                public_key = f.read().strip()

            ssh_dir_cmd = f'sudo -u omni_user mkdir -p /home/omni_user/.ssh'
            key_cmd = f'echo "{public_key}" | sudo tee /home/omni_user/.ssh/authorized_keys'
            perm_cmd = 'sudo chmod 600 /home/omni_user/.ssh/authorized_keys && sudo chown omni_user:omni_user /home/omni_user/.ssh/authorized_keys'

            for cmd in [ssh_dir_cmd, key_cmd, perm_cmd]:
                stdin, stdout, stderr = self.ssh_clients[instance_name].exec_command(cmd)
                stdout.read()

            logger.info(f"SSH user setup completed for {instance_name}")

        except Exception as e:
            logger.error(f"Failed to setup SSH user on {instance_name}: {e}")
            raise

    def install_system_dependencies(self, instance_name: str):
        """Install all required system dependencies"""
        logger.info(f"Installing system dependencies on {instance_name}...")

        try:
            # Update system
            commands = [
                'sudo apt update',
                'sudo apt upgrade -y',
                'sudo apt install -y python3 python3-pip python3-venv nodejs npm nginx redis-server mongodb git curl wget htop vim screen',
                'sudo apt install -y build-essential libssl-dev libffi-dev python3-dev',
                'sudo apt install -y postgresql postgresql-contrib',
                'sudo apt install -y docker.io docker-compose',
                'sudo systemctl enable docker',
                'sudo usermod -aG docker omni_user'
            ]

            for cmd in commands:
                logger.info(f"Executing: {cmd}")
                stdin, stdout, stderr = self.ssh_clients[instance_name].exec_command(cmd, timeout=300)
                exit_status = stdout.channel.recv_exit_status()

                if exit_status != 0:
                    error_output = stderr.read().decode()
                    logger.warning(f"Command failed: {cmd}")
                    logger.warning(f"Error: {error_output}")

            logger.info(f"System dependencies installed on {instance_name}")

        except Exception as e:
            logger.error(f"Failed to install dependencies on {instance_name}: {e}")
            raise

    def setup_python_environment(self, instance_name: str):
        """Set up Python virtual environment and install packages"""
        logger.info(f"Setting up Python environment on {instance_name}...")

        try:
            commands = [
                'cd /home/omni_user',
                'python3 -m venv omni_env',
                'source omni_env/bin/activate && pip install --upgrade pip',
                'source omni_env/bin/activate && pip install fastapi uvicorn plotly pandas psutil paramiko requests',
                'source omni_env/bin/activate && pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu',
                'source omni_env/bin/activate && pip install transformers diffusers accelerate',
                'source omni_env/bin/activate && pip install sqlalchemy redis pymongo psycopg2-binary',
                'source omni_env/bin/activate && pip install structlog rich click tqdm pyyaml',
                'source omni_env/bin/activate && pip install python-multipart python-dotenv tenacity backoff',
                'source omni_env/bin/activate && pip install aiohttp websockets prometheus-client',
                'source omni_env/bin/activate && pip install numpy scipy pandas scikit-learn',
                'source omni_env/bin/activate && pip install qiskit pennylane cirq',
                'source omni_env/bin/activate && pip install opencv-python pillow moviepy',
                'source omni_env/bin/activate && pip install flask django starlette',
                'source omni_env/bin/activate && pip install celery flower rabbitmq',
                'source omni_env/bin/activate && pip install jupyter notebook ipykernel',
                'source omni_env/bin/activate && pip install boto3 azure-storage-blob google-cloud-storage'
            ]

            # Execute commands
            full_command = ' && '.join(commands)
            stdin, stdout, stderr = self.ssh_clients[instance_name].exec_command(full_command, timeout=600)
            exit_status = stdout.channel.recv_exit_status()

            if exit_status != 0:
                error_output = stderr.read().decode()
                logger.error(f"Python environment setup failed: {error_output}")

            logger.info(f"Python environment setup completed on {instance_name}")

        except Exception as e:
            logger.error(f"Failed to setup Python environment on {instance_name}: {e}")
            raise

    def deploy_omni_dashboard(self, instance_name: str):
        """Deploy the operational dashboard"""
        logger.info(f"Deploying Omni dashboard on {instance_name}...")

        try:
            # Copy dashboard file
            dashboard_file = 'omni_operational_dashboard.py'
            sftp = self.ssh_clients[instance_name].open_sftp()
            sftp.put(dashboard_file, f'/home/omni_user/{dashboard_file}')
            sftp.close()

            # Set up systemd service for dashboard
            service_content = f"""
[Unit]
Description=Omni Platform Operational Dashboard
After=network.target

[Service]
Type=simple
User=omni_user
WorkingDirectory=/home/omni_user
ExecStart=/home/omni_user/omni_env/bin/python omni_operational_dashboard.py
Restart=always
RestartSec=10
Environment=PATH=/home/omni_user/omni_env/bin
Environment=OMNI_HOME=/home/omni_user

[Install]
WantedBy=multi-user.target
"""

            service_cmd = f'cat > /tmp/omni-dashboard.service << \'EOF\'\n{service_content}\nEOF'
            stdin, stdout, stderr = self.ssh_clients[instance_name].exec_command(service_cmd)
            stdout.read()

            # Install and start service
            commands = [
                'sudo mv /tmp/omni-dashboard.service /etc/systemd/system/',
                'sudo systemctl daemon-reload',
                'sudo systemctl enable omni-dashboard',
                'sudo systemctl start omni-dashboard'
            ]

            for cmd in commands:
                stdin, stdout, stderr = self.ssh_clients[instance_name].exec_command(cmd)
                stdout.read()

            logger.info(f"Omni dashboard deployed on {instance_name}")

        except Exception as e:
            logger.error(f"Failed to deploy dashboard on {instance_name}: {e}")
            raise

    def setup_nginx_reverse_proxy(self, instance_name: str):
        """Set up Nginx reverse proxy"""
        logger.info(f"Setting up Nginx reverse proxy on {instance_name}...")

        try:
            nginx_config = f"""
server {{
    listen 80;
    server_name _;

    # Dashboard
    location / {{
        proxy_pass http://localhost:{self.config.dashboard_port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    # API endpoints
    location /api/ {{
        proxy_pass http://localhost:{self.config.dashboard_port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    # Health check
    location /health {{
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }}
}}
"""

            config_cmd = f'sudo tee /etc/nginx/sites-available/omni-platform > /dev/null << \'EOF\'\n{nginx_config}\nEOF'
            stdin, stdout, stderr = self.ssh_clients[instance_name].exec_command(config_cmd)
            stdout.read()

            # Enable site and restart Nginx
            commands = [
                'sudo ln -sf /etc/nginx/sites-available/omni-platform /etc/nginx/sites-enabled/',
                'sudo rm -f /etc/nginx/sites-enabled/default',
                'sudo systemctl restart nginx',
                'sudo systemctl enable nginx'
            ]

            for cmd in commands:
                stdin, stdout, stderr = self.ssh_clients[instance_name].exec_command(cmd)
                stdout.read()

            logger.info(f"Nginx reverse proxy setup completed on {instance_name}")

        except Exception as e:
            logger.error(f"Failed to setup Nginx on {instance_name}: {e}")
            raise

    def setup_directories_and_permissions(self, instance_name: str):
        """Set up required directories and permissions"""
        logger.info(f"Setting up directories and permissions on {instance_name}...")

        try:
            commands = [
                'sudo mkdir -p /opt/omni/{models,data,logs,backups,temp,uploads}',
                'sudo chown -R omni_user:omni_user /opt/omni',
                'chmod -R 755 /opt/omni',
                'sudo mkdir -p /var/log/omni',
                'sudo chown omni_user:omni_user /var/log/omni',
                'sudo mkdir -p /home/omni_user/.config',
                'sudo chown omni_user:omni_user /home/omni_user/.config'
            ]

            for cmd in commands:
                stdin, stdout, stderr = self.ssh_clients[instance_name].exec_command(cmd)
                stdout.read()

            logger.info(f"Directories and permissions setup completed on {instance_name}")

        except Exception as e:
            logger.error(f"Failed to setup directories on {instance_name}: {e}")
            raise

    def configure_firewall(self):
        """Configure firewall rules for the platform"""
        logger.info("Configuring firewall rules...")

        try:
            # Create comprehensive firewall rules
            firewall_commands = [
                'gcloud compute firewall-rules create omni-platform-http --allow tcp:80,tcp:443 --source-ranges 0.0.0.0/0 --description "Allow HTTP/HTTPS access to Omni platform"',
                'gcloud compute firewall-rules create omni-platform-api --allow tcp:8080,tcp:8000,tcp:5000,tcp:3000 --source-ranges 0.0.0.0/0 --description "Allow API access to Omni platform"',
                'gcloud compute firewall-rules create omni-platform-admin --allow tcp:22,tcp:8081,tcp:9000 --source-ranges 0.0.0.0/0 --description "Allow admin access to Omni platform"'
            ]

            for cmd in firewall_commands:
                logger.info(f"Creating firewall rule: {cmd}")
                result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=30)

                if result.returncode != 0 and "already exists" not in result.stderr:
                    logger.warning(f"Firewall rule creation returned: {result.stderr}")

            logger.info("Firewall configuration completed")

        except Exception as e:
            logger.error(f"Failed to configure firewall: {e}")
            raise

    def verify_deployment(self, instance_name: str) -> bool:
        """Verify that deployment was successful"""
        logger.info(f"Verifying deployment on {instance_name}...")

        try:
            # Check if services are running
            verification_commands = [
                'systemctl is-active omni-dashboard',
                'systemctl is-active nginx',
                'systemctl is-active redis-server',
                'python3 -c "import torch; print(\'PyTorch available\')"',
                'python3 -c "import fastapi; print(\'FastAPI available\')"'
            ]

            all_checks_passed = True

            for cmd in verification_commands:
                try:
                    stdin, stdout, stderr = self.ssh_clients[instance_name].exec_command(cmd, timeout=30)
                    exit_status = stdout.channel.recv_exit_status()

                    if exit_status == 0:
                        output = stdout.read().decode().strip()
                        logger.info(f"✓ {cmd}: {output}")
                    else:
                        logger.error(f"✗ {cmd}: Failed")
                        all_checks_passed = False

                except Exception as e:
                    logger.error(f"✗ {cmd}: Error - {e}")
                    all_checks_passed = False

            # Test web interface
            instance_ip = self._get_instance_ip(instance_name)
            try:
                response = requests.get(f"http://{instance_ip}/health", timeout=10)
                if response.status_code == 200:
                    logger.info(f"✓ Web interface accessible at http://{instance_ip}")
                else:
                    logger.error(f"✗ Web interface not accessible: HTTP {response.status_code}")
                    all_checks_passed = False
            except Exception as e:
                logger.error(f"✗ Web interface not accessible: {e}")
                all_checks_passed = False

            return all_checks_passed

        except Exception as e:
            logger.error(f"Deployment verification failed for {instance_name}: {e}")
            return False

    def deploy_to_instance(self, instance_name: str):
        """Complete deployment to a single instance"""
        logger.info(f"Starting complete deployment to {instance_name}")

        try:
            # Wait for SSH
            if not self.wait_for_ssh_availability(instance_name):
                raise Exception(f"SSH not available for {instance_name}")

            # Setup SSH user
            self.setup_ssh_user_and_keys(instance_name)

            # Install dependencies
            self.install_system_dependencies(instance_name)

            # Setup Python environment
            self.setup_python_environment(instance_name)

            # Setup directories
            self.setup_directories_and_permissions(instance_name)

            # Deploy dashboard
            self.deploy_omni_dashboard(instance_name)

            # Setup Nginx
            self.setup_nginx_reverse_proxy(instance_name)

            # Verify deployment
            if self.verify_deployment(instance_name):
                logger.info(f"✅ Deployment completed successfully for {instance_name}")
                return True
            else:
                logger.error(f"❌ Deployment verification failed for {instance_name}")
                return False

        except Exception as e:
            logger.error(f"Deployment failed for {instance_name}: {e}")
            return False

    def deploy_complete_platform(self):
        """Deploy the complete Omni platform"""
        logger.info("🚀 Starting complete Omni platform deployment...")

        self.deployment_status = "starting"

        try:
            # Configure firewall
            self.configure_firewall()

            # Deploy to all instances
            instances = [self.config.primary_instance, self.config.storage_instance]
            deployment_results = {}

            for instance in instances:
                self.deployment_status = f"deploying_to_{instance}"

                # Deploy in thread for parallel deployment
                with ThreadPoolExecutor(max_workers=2) as executor:
                    future = executor.submit(self.deploy_to_instance, instance)
                    result = future.result(timeout=1800)  # 30 minute timeout
                    deployment_results[instance] = result

            # Check results
            successful_deployments = sum(deployment_results.values())

            if successful_deployments == len(instances):
                self.deployment_status = "completed"
                logger.info("🎉 COMPLETE OMNI PLATFORM DEPLOYMENT SUCCESSFUL!")

                # Print access information
                self.print_access_information()

                return True
            else:
                self.deployment_status = "failed"
                failed_instances = [name for name, success in deployment_results.items() if not success]
                logger.error(f"❌ Deployment failed for instances: {failed_instances}")
                return False

        except Exception as e:
            self.deployment_status = "error"
            logger.error(f"Complete deployment failed: {e}")
            return False

    def print_access_information(self):
        """Print access information for the deployed platform"""
        print("\n" + "="*60)
        print("🎉 OMNI PLATFORM - DEPLOYMENT COMPLETED SUCCESSFULLY!")
        print("="*60)

        primary_ip = self._get_instance_ip(self.config.primary_instance)
        storage_ip = self._get_instance_ip(self.config.storage_instance)

        print("\n📋 PLATFORM ACCESS INFORMATION:")
        print(f"   🌐 Primary Dashboard: http://{primary_ip}")
        print(f"   💾 Storage Node:      {storage_ip}")
        print(f"   🔧 Admin Access:      http://{primary_ip}:8080")
        print(f"   📊 API Endpoint:      http://{primary_ip}:8000/api")
        print(f"   ❤️  Health Check:     http://{primary_ip}/health")

        print("\n🔍 MONITORING & MANAGEMENT:")
        print("   Dashboard Features:")
        print("   • Real-time system metrics")
        print("   • Service status monitoring")
        print("   • Resource utilization tracking")
        print("   • Cost monitoring and alerts")
        print("   • Performance analytics")
        print("   • Automated recommendations")

        print("\n💡 QUICK COMMANDS:")
        print(f"   Check status: curl http://{primary_ip}/health")
        print(f"   View metrics: curl http://{primary_ip}:8000/api/metrics")
        print(f"   Service info: curl http://{primary_ip}:8000/api/services")

        print("\n⚠️  IMPORTANT NOTES:")
        print("   • Free trial: Monitor costs at console.cloud.google.com/billing")
        print("   • SSH Access: gcloud compute ssh omni_user@{instance} --zone={zone}")
        print("   • Logs: sudo journalctl -u omni-dashboard -f")
        print("   • Restart: sudo systemctl restart omni-dashboard")
        print("="*60)

    def get_deployment_status(self) -> Dict[str, Any]:
        """Get current deployment status"""
        return {
            "status": self.deployment_status,
            "timestamp": datetime.now().isoformat(),
            "config": asdict(self.config),
            "instances": {
                "primary": self._get_instance_ip(self.config.primary_instance),
                "storage": self._get_instance_ip(self.config.storage_instance)
            }
        }

def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description='Deploy Omni Platform to Google Cloud')
    parser.add_argument('--project', default='refined-graph-471712-n9', help='Google Cloud project ID')
    parser.add_argument('--primary-instance', default='omni-cpu-optimized', help='Primary instance name')
    parser.add_argument('--storage-instance', default='omni-storage-node', help='Storage instance name')
    parser.add_argument('--zone', default='us-central1-c', help='Google Cloud zone')
    parser.add_argument('--dashboard-port', type=int, default=8080, help='Dashboard port')
    parser.add_argument('--api-port', type=int, default=8000, help='API port')

    args = parser.parse_args()

    config = DeploymentConfig(
        project_id=args.project,
        primary_instance=args.primary_instance,
        storage_instance=args.storage_instance,
        zone=args.zone,
        dashboard_port=args.dashboard_port,
        api_port=args.api_port
    )

    deployer = OmniPlatformDeployer(config)

    print("🚀 OMNI PLATFORM - PROFESSIONAL DEPLOYMENT SYSTEM")
    print("="*55)
    print(f"Project: {config.project_id}")
    print(f"Primary Instance: {config.primary_instance}")
    print(f"Storage Instance: {config.storage_instance}")
    print(f"Zone: {config.zone}")
    print("="*55)

    # Run deployment
    success = deployer.deploy_complete_platform()

    if success:
        print("\n✅ Deployment completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Deployment failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()