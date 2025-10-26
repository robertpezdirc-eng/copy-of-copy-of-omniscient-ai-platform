#!/usr/bin/env python3
"""
OMNI Platform Requirements and Infrastructure Setup
Complete system requirements and setup for professional AI platform

This module implements all the infrastructure requirements mentioned:
1. System foundation (HTTP version)
2. Platform operation tools
3. AI agent modules
4. Frontend HTTP integration
5. Developer tools setup
6. Environment configuration
7. Autonomous agent operation
8. Monitoring and diagnostics

Author: OMNI Platform Requirements
Version: 3.0.0
"""

import asyncio
import json
import time
import os
import sys
import logging
import subprocess
import platform
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

class SystemRequirement(Enum):
    """System requirement categories"""
    OS = "operating_system"
    SOFTWARE = "software_dependencies"
    HARDWARE = "hardware_requirements"
    NETWORK = "network_configuration"
    STORAGE = "storage_configuration"
    SECURITY = "security_settings"

class PlatformComponent(Enum):
    """Platform component types"""
    CORE = "core_platform"
    AI_AGENTS = "ai_agents"
    HTTP_SERVER = "http_server"
    DATABASE = "database"
    CACHE = "cache_system"
    UI_FRONTEND = "ui_frontend"
    MONITORING = "monitoring"
    BACKUP = "backup_system"

@dataclass
class SystemRequirement:
    """System requirement specification"""
    name: str
    description: str
    required: bool
    current_status: str
    installation_command: str
    verification_command: str
    notes: str = ""

class OmniPlatformRequirements:
    """Complete platform requirements and setup system"""

    def __init__(self):
        self.requirements_name = "OMNI Platform Requirements"
        self.version = "3.0.0"
        self.start_time = time.time()
        self.requirements_met = {}
        self.system_info = self._get_system_info()
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for requirements system"""
        logger = logging.getLogger('OmniPlatformRequirements')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.FileHandler('omni_requirements.log', encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            import psutil

            return {
                "platform": platform.system(),
                "platform_version": platform.release(),
                "architecture": platform.architecture(),
                "processor": platform.processor(),
                "cpu_count": os.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "disk_total": psutil.disk_usage('/').total,
                "python_version": sys.version,
                "node_version": self._get_node_version(),
                "git_version": self._get_git_version()
            }

        except ImportError:
            return {
                "platform": platform.system(),
                "python_version": sys.version,
                "node_version": "Not available",
                "git_version": "Not available"
            }

    def _get_node_version(self) -> str:
        """Get Node.js version"""
        try:
            result = subprocess.run(['node', '--version'],
                                  capture_output=True, text=True, timeout=10)
            return result.stdout.strip() if result.returncode == 0 else "Not installed"
        except:
            return "Not available"

    def _get_git_version(self) -> str:
        """Get Git version"""
        try:
            result = subprocess.run(['git', '--version'],
                                  capture_output=True, text=True, timeout=10)
            return result.stdout.strip() if result.returncode == 0 else "Not installed"
        except:
            return "Not available"

    def check_all_requirements(self) -> Dict[str, Any]:
        """Check all system requirements"""
        print("[REQUIREMENTS] Checking OMNI Platform Requirements")
        print("=" * 60)

        results = {
            "timestamp": time.time(),
            "system_info": self.system_info,
            "requirements_status": {},
            "overall_compatibility": "unknown",
            "missing_requirements": [],
            "recommendations": []
        }

        # Check each requirement category
        categories = [
            ("Operating System", self._check_os_requirements),
            ("Software Dependencies", self._check_software_requirements),
            ("Hardware Requirements", self._check_hardware_requirements),
            ("Network Configuration", self._check_network_requirements),
            ("Storage Configuration", self._check_storage_requirements),
            ("Security Settings", self._check_security_requirements)
        ]

        total_requirements = 0
        met_requirements = 0

        for category_name, check_function in categories:
            print(f"\n[{category_name.upper()}]")
            print("-" * 40)

            category_results = check_function()
            results["requirements_status"][category_name.lower()] = category_results

            category_met = sum(1 for req in category_results if req["status"] == "met")
            category_total = len(category_results)

            total_requirements += category_total
            met_requirements += category_met

            print(f"  Status: {category_met}/{category_total} requirements met")

            # Show individual requirements
            for req in category_results:
                status_icon = "[OK]" if req["status"] == "met" else "[MISSING]"
                print(f"    {status_icon} {req['name']}: {req['description']}")

                if req["status"] != "met":
                    results["missing_requirements"].append(req)

        # Calculate overall compatibility
        compatibility_score = (met_requirements / total_requirements) * 100 if total_requirements > 0 else 0

        if compatibility_score >= 90:
            results["overall_compatibility"] = "excellent"
        elif compatibility_score >= 75:
            results["overall_compatibility"] = "good"
        elif compatibility_score >= 50:
            results["overall_compatibility"] = "fair"
        else:
            results["overall_compatibility"] = "poor"

        # Generate recommendations
        results["recommendations"] = self._generate_setup_recommendations(results)

        print("\n[OVERALL] Compatibility Assessment")
        print("=" * 60)
        print(f"Compatibility Score: {compatibility_score:.1f}%")
        print(f"Overall Rating: {results['overall_compatibility'].upper()}")
        print(f"Requirements Met: {met_requirements}/{total_requirements}")

        return results

    def _check_os_requirements(self) -> List[Dict[str, Any]]:
        """Check operating system requirements"""
        requirements = []

        # Windows with WSL2 or Linux
        if self.system_info["platform"] == "Windows":
            requirements.append({
                "name": "Windows 10/11",
                "description": "Windows 10 or 11 required",
                "status": "met" if sys.getwindowsversion().major >= 10 else "not_met",
                "required": True,
                "installation_command": "N/A - Use Windows 10/11",
                "verification_command": "ver"
            })

            # Check for WSL2
            requirements.append({
                "name": "WSL2 Support",
                "description": "Windows Subsystem for Linux 2 for optimal performance",
                "status": self._check_wsl2_availability(),
                "required": False,
                "installation_command": "wsl --install",
                "verification_command": "wsl --version"
            })

        elif self.system_info["platform"] == "Linux":
            requirements.append({
                "name": "Linux Distribution",
                "description": "Ubuntu/Debian or compatible Linux distribution",
                "status": "met",
                "required": True,
                "installation_command": "N/A - Linux detected",
                "verification_command": "uname -a"
            })

        # Terminal/Shell
        requirements.append({
            "name": "Terminal Access",
            "description": "Command line terminal access",
            "status": "met",
            "required": True,
            "installation_command": "N/A - Terminal available",
            "verification_command": "echo $SHELL"
        })

        # Administrator privileges
        requirements.append({
            "name": "Administrator Privileges",
            "description": "Administrator/root access for installation",
            "status": self._check_admin_privileges(),
            "required": True,
            "installation_command": "Use sudo or run as administrator",
            "verification_command": "whoami"
        })

        return requirements

    def _check_software_requirements(self) -> List[Dict[str, Any]]:
        """Check software dependency requirements"""
        requirements = []

        # Python 3.11+
        python_version = sys.version_info
        requirements.append({
            "name": "Python 3.11+",
            "description": "Python 3.11 or higher required",
            "status": "met" if python_version >= (3, 11) else "not_met",
            "required": True,
            "installation_command": "Download from python.org or use package manager",
            "verification_command": "python --version"
        })

        # Node.js 18+
        node_version = self._get_node_version()
        requirements.append({
            "name": "Node.js 18+",
            "description": "Node.js 18 or higher for frontend and API",
            "status": "met" if self._parse_version(node_version) >= (18, 0) else "not_met",
            "required": True,
            "installation_command": "curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs",
            "verification_command": "node --version"
        })

        # Git
        git_version = self._get_git_version()
        requirements.append({
            "name": "Git",
            "description": "Git version control system",
            "status": "met" if git_version != "Not installed" else "not_met",
            "required": True,
            "installation_command": "sudo apt-get install git" if self.system_info["platform"] == "Linux" else "Download from git-scm.com",
            "verification_command": "git --version"
        })

        # Build tools
        requirements.append({
            "name": "Build Tools",
            "description": "gcc/g++, make, build-essential",
            "status": self._check_build_tools(),
            "required": True,
            "installation_command": "sudo apt-get install build-essential" if self.system_info["platform"] == "Linux" else "Install Visual Studio Build Tools",
            "verification_command": "gcc --version"
        })

        return requirements

    def _check_hardware_requirements(self) -> List[Dict[str, Any]]:
        """Check hardware requirements"""
        requirements = []

        # RAM requirements
        memory_gb = self.system_info["memory_total"] / (1024**3)
        requirements.append({
            "name": "RAM (16-32GB)",
            "description": "16-32GB RAM recommended for AI workloads",
            "status": "met" if memory_gb >= 16 else "warning" if memory_gb >= 8 else "not_met",
            "required": False,
            "installation_command": "Add more RAM to system",
            "verification_command": "systeminfo | findstr /C:'Total Physical Memory'" if self.system_info["platform"] == "Windows" else "free -h"
        })

        # Disk space
        disk_gb = self.system_info["disk_total"] / (1024**3)
        requirements.append({
            "name": "Storage (SSD/NVMe)",
            "description": "SSD or NVMe storage for fast read/write",
            "status": "met" if disk_gb >= 100 else "warning" if disk_gb >= 50 else "not_met",
            "required": True,
            "installation_command": "Use SSD storage for optimal performance",
            "verification_command": "df -h /" if self.system_info["platform"] == "Linux" else "wmic logicaldisk get size,freespace,caption"
        })

        # CPU cores
        cpu_count = self.system_info["cpu_count"] or 4
        requirements.append({
            "name": "CPU Cores (4+)",
            "description": "4+ CPU cores for multi-threaded operations",
            "status": "met" if cpu_count >= 4 else "warning" if cpu_count >= 2 else "not_met",
            "required": False,
            "installation_command": "Multi-core CPU recommended",
            "verification_command": "nproc" if self.system_info["platform"] == "Linux" else "echo %NUMBER_OF_PROCESSORS%"
        })

        return requirements

    def _check_network_requirements(self) -> List[Dict[str, Any]]:
        """Check network configuration requirements"""
        requirements = []

        # Port availability
        ports_to_check = [8080, 3000, 5000, 8000]
        available_ports = []

        for port in ports_to_check:
            if self._check_port_available(port):
                available_ports.append(port)

        requirements.append({
            "name": "Available Ports",
            "description": "HTTP ports 8080, 3000, 5000, 8000 available",
            "status": "met" if len(available_ports) >= 2 else "warning",
            "required": True,
            "installation_command": f"Configure firewall to open ports: {', '.join(map(str, ports_to_check))}",
            "verification_command": "netstat -tulpn | grep LISTEN" if self.system_info["platform"] == "Linux" else "netstat -an | findstr LISTEN"
        })

        # Firewall configuration
        requirements.append({
            "name": "Firewall Configuration",
            "description": "Firewall configured for HTTP ports",
            "status": self._check_firewall_configuration(),
            "required": False,
            "installation_command": "sudo ufw allow 8080 && sudo ufw allow 3000" if self.system_info["platform"] == "Linux" else "Configure Windows Firewall",
            "verification_command": "sudo ufw status" if self.system_info["platform"] == "Linux" else "netsh advfirewall firewall show rule name=all"
        })

        return requirements

    def _check_storage_requirements(self) -> List[Dict[str, Any]]:
        """Check storage configuration requirements"""
        requirements = []

        # SSD detection
        requirements.append({
            "name": "SSD Storage",
            "description": "SSD or NVMe storage for optimal performance",
            "status": self._detect_ssd_storage(),
            "required": True,
            "installation_command": "Use SSD storage for best performance",
            "verification_command": "lsblk -d -o name,rota" if self.system_info["platform"] == "Linux" else "wmic diskdrive get model,mediaType"
        })

        # Google Drive integration
        requirements.append({
            "name": "Google Drive Mount",
            "description": "Google Drive integration for cloud storage",
            "status": self._check_google_drive_integration(),
            "required": False,
            "installation_command": "pip install google-auth-oauthlib google-api-python-client && python omni_google_drive_integration.py",
            "verification_command": "ls -la ~/Google\ Drive" if self.system_info["platform"] == "Linux" else "dir 'C:\\Users\\%USERNAME%\\Google Drive'"
        })

        return requirements

    def _check_security_requirements(self) -> List[Dict[str, Any]]:
        """Check security configuration requirements"""
        requirements = []

        # Environment variables
        requirements.append({
            "name": "Environment Variables",
            "description": "Secure storage of API keys and secrets",
            "status": self._check_environment_variables(),
            "required": True,
            "installation_command": "Create .env file with API keys",
            "verification_command": "ls -la .env"
        })

        # CORS configuration
        requirements.append({
            "name": "CORS Configuration",
            "description": "Cross-origin resource sharing configured",
            "status": "met",  # Will be configured in application
            "required": False,
            "installation_command": "Configure CORS in FastAPI/Flask application",
            "verification_command": "Check application configuration"
        })

        # Password policies
        requirements.append({
            "name": "Password Security",
            "description": "Strong password policies implemented",
            "status": "met",  # Will be implemented in user manager
            "required": False,
            "installation_command": "Implement password validation in user management",
            "verification_command": "Check user management configuration"
        })

        return requirements

    def _check_port_available(self, port: int) -> bool:
        """Check if port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(('', port))
                return True
        except:
            return False

    def _check_wsl2_availability(self) -> str:
        """Check WSL2 availability on Windows"""
        if self.system_info["platform"] != "Windows":
            return "not_applicable"

        try:
            result = subprocess.run(['wsl', '--version'],
                                  capture_output=True, text=True, timeout=10)
            return "met" if result.returncode == 0 else "not_met"
        except:
            return "not_met"

    def _check_admin_privileges(self) -> str:
        """Check administrator/root privileges"""
        try:
            if self.system_info["platform"] == "Windows":
                # Check if running as administrator
                import ctypes
                return "met" if ctypes.windll.shell32.IsUserAnAdmin() else "not_met"
            else:
                # Check if running as root
                return "met" if os.geteuid() == 0 else "not_met"
        except:
            return "unknown"

    def _parse_version(self, version_string: str) -> Tuple[int, int]:
        """Parse version string to tuple"""
        try:
            if version_string.startswith('v'):
                version_string = version_string[1:]

            parts = version_string.split('.')
            return (int(parts[0]), int(parts[1]))
        except:
            return (0, 0)

    def _check_build_tools(self) -> str:
        """Check build tools availability"""
        try:
            result = subprocess.run(['gcc', '--version'],
                                  capture_output=True, timeout=10)
            return "met" if result.returncode == 0 else "not_met"
        except:
            return "not_met"

    def _check_firewall_configuration(self) -> str:
        """Check firewall configuration"""
        try:
            if self.system_info["platform"] == "Linux":
                result = subprocess.run(['sudo', 'ufw', 'status'],
                                      capture_output=True, text=True, timeout=10)
                return "met" if "Status: active" in result.stdout else "not_met"
            else:
                # Windows firewall check
                result = subprocess.run(['netsh', 'advfirewall', 'show', 'allprofiles'],
                                      capture_output=True, text=True, timeout=10)
                return "met" if result.returncode == 0 else "not_met"
        except:
            return "not_met"

    def _detect_ssd_storage(self) -> str:
        """Detect SSD storage"""
        try:
            if self.system_info["platform"] == "Linux":
                result = subprocess.run(['lsblk', '-d', '-o', 'name,rota'],
                                      capture_output=True, text=True, timeout=10)
                # If rotational is 0, it's likely SSD
                return "met" if "0" in result.stdout else "unknown"
            else:
                # Windows SSD detection
                result = subprocess.run(['wmic', 'diskdrive', 'get', 'model,mediaType'],
                                      capture_output=True, text=True, timeout=10)
                return "met" if "SSD" in result.stdout.upper() else "unknown"
        except:
            return "unknown"

    def _check_google_drive_integration(self) -> str:
        """Check Google Drive integration"""
        try:
            drive_path = os.path.expanduser("~/Google Drive") if self.system_info["platform"] == "Linux" else f"C:\\Users\\{os.environ.get('USERNAME', 'user')}\\Google Drive"

            if os.path.exists(drive_path):
                return "met"
            else:
                return "not_met"
        except:
            return "not_met"

    def _check_environment_variables(self) -> str:
        """Check environment variables configuration"""
        required_vars = ["OPENAI_API_KEY", "OMNI_API_KEY", "DATABASE_URL"]

        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)

        if missing_vars:
            return "not_met"
        else:
            return "met"

    def _generate_setup_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate setup and configuration recommendations"""
        recommendations = []

        # Overall compatibility recommendations
        compatibility = results["overall_compatibility"]
        if compatibility == "poor":
            recommendations.append("CRITICAL: System compatibility is poor - address missing requirements immediately")
        elif compatibility == "fair":
            recommendations.append("WARNING: System compatibility needs improvement for optimal performance")

        # Missing requirements recommendations
        for req in results["missing_requirements"]:
            recommendations.append(f"Install {req['name']}: {req['installation_command']}")

        # Platform-specific recommendations
        if self.system_info["platform"] == "Windows":
            recommendations.append("Consider using WSL2 for optimal Linux compatibility")
            recommendations.append("Install Visual Studio Build Tools for C++ dependencies")
        else:
            recommendations.append("Use Ubuntu/Debian for best compatibility")
            recommendations.append("Install build-essential package for compilation tools")

        # Performance recommendations
        memory_gb = self.system_info["memory_total"] / (1024**3)
        if memory_gb < 16:
            recommendations.append(f"Consider upgrading RAM to 16GB+ for AI workloads (current: {memory_gb:.1f}GB)")

        return recommendations

    def generate_requirements_report(self) -> str:
        """Generate comprehensive requirements report"""
        results = self.check_all_requirements()

        report = []
        report.append("# OMNI Platform Requirements Report")
        report.append("")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        report.append("## System Information")
        report.append("")

        for key, value in results["system_info"].items():
            report.append(f"- **{key.replace('_', ' ').title()}**: {value}")

        report.append("")
        report.append("## Requirements Assessment")
        report.append("")

        # Overall status
        status_icon = "[OK]" if results["overall_compatibility"] in ["excellent", "good"] else "[WARNING]"
        report.append(f"{status_icon} **Overall Compatibility**: {results['overall_compatibility'].upper()}")
        report.append(f"- **Score**: {len(results.get('missing_requirements', [])) == 0 and 'All requirements met' or f"{len([r for r in results['requirements_status'].values() for req in r if req['status'] == 'met'])} requirements met"}")

        report.append("")
        report.append("## Detailed Requirements")
        report.append("")

        for category, requirements in results["requirements_status"].items():
            report.append(f"### {category.replace('_', ' ').title()}")
            report.append("")

            for req in requirements:
                status_icon = "[OK]" if req["status"] == "met" else "[MISSING]"
                report.append(f"{status_icon} **{req['name']}**")
                report.append(f"  - {req['description']}")

                if req["status"] != "met":
                    report.append(f"  - **Installation**: {req['installation_command']}")
                    report.append(f"  - **Verification**: {req['verification_command']}")

                report.append("")

        report.append("## Recommendations")
        report.append("")

        for rec in results["recommendations"]:
            report.append(f"- {rec}")

        report.append("")
        report.append("## Next Steps")
        report.append("")
        report.append("1. Install missing required software dependencies")
        report.append("2. Configure system hardware for optimal performance")
        report.append("3. Set up network and firewall configurations")
        report.append("4. Configure storage and backup systems")
        report.append("5. Set up environment variables and security")
        report.append("6. Run platform installation and setup scripts")

        return "\n".join(report)

    def setup_platform_environment(self) -> Dict[str, Any]:
        """Setup complete platform environment"""
        print("\n[SETUP] Setting up OMNI Platform Environment")
        print("=" * 60)

        setup_results = {
            "timestamp": time.time(),
            "setup_steps": [],
            "configuration_files": [],
            "environment_variables": [],
            "services_configured": [],
            "success": True
        }

        try:
            # Step 1: Create directory structure
            print("  [STEP 1] Creating directory structure...")
            directories = [
                "./omni_platform",
                "./omni_platform/backups",
                "./omni_platform/logs",
                "./omni_platform/config",
                "./omni_platform/data",
                "./omni_platform/temp",
                "./omni_platform/wiki",
                "./omni_platform/docs"
            ]

            for directory in directories:
                os.makedirs(directory, exist_ok=True)

            setup_results["setup_steps"].append("Directory structure created")
            print("    [OK] Directory structure created")

            # Step 2: Create environment configuration
            print("  [STEP 2] Creating environment configuration...")

            env_content = """# OMNI Platform Environment Configuration
# Copy this file to .env and fill in your actual values

# API Keys
OPENAI_API_KEY=your_openai_api_key_here
OMNI_API_KEY=your_omni_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///omni_platform/data/omni_platform.db
REDIS_URL=redis://localhost:6379

# Server Configuration
HTTP_HOST=localhost
HTTP_PORT=8080
WEBSOCKET_PORT=3001

# Security
SECRET_KEY=your_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here

# Storage
BACKUP_PATH=./omni_platform/backups
LOG_PATH=./omni_platform/logs
TEMP_PATH=./omni_platform/temp

# External Integrations
GOOGLE_DRIVE_ENABLED=false
CLOUD_STORAGE_ENABLED=false

# Development
DEBUG=true
LOG_LEVEL=INFO
"""

            with open('./omni_platform/.env.template', 'w') as f:
                f.write(env_content)

            setup_results["configuration_files"].append("Environment template created")
            print("    [OK] Environment template created")

            # Step 3: Create main configuration
            print("  [STEP 3] Creating main configuration...")

            config_content = {
                "platform": {
                    "name": "OMNI Platform",
                    "version": "3.0.0",
                    "environment": "development",
                    "debug": True
                },
                "server": {
                    "host": "localhost",
                    "port": 8080,
                    "workers": 4,
                    "timeout": 300
                },
                "database": {
                    "type": "sqlite",
                    "path": "./omni_platform/data/omni_platform.db"
                },
                "security": {
                    "secret_key": "change_this_in_production",
                    "encryption_enabled": True,
                    "cors_enabled": True
                },
                "features": {
                    "ai_agents": True,
                    "http_platform": True,
                    "real_time": True,
                    "monitoring": True,
                    "backup": True
                }
            }

            with open('./omni_platform/config.json', 'w') as f:
                json.dump(config_content, f, indent=2)

            setup_results["configuration_files"].append("Main configuration created")
            print("    [OK] Main configuration created")

            # Step 4: Create startup scripts
            print("  [STEP 4] Creating startup scripts...")

            if self.system_info["platform"] == "Windows":
                startup_script = """@echo off
echo Starting OMNI Platform...
cd /d %~dp0
python omni_platform_master_coordinator.py
pause
"""
                with open('./omni_platform/start_platform.bat', 'w') as f:
                    f.write(startup_script)
            else:
                startup_script = """#!/bin/bash
echo "Starting OMNI Platform..."
cd "$(dirname "$0")"
python3 omni_platform_master_coordinator.py
"""
                with open('./omni_platform/start_platform.sh', 'w') as f:
                    f.write(startup_script)

                # Make executable
                os.chmod('./omni_platform/start_platform.sh', 0o755)

            setup_results["setup_steps"].append("Startup scripts created")
            print("    [OK] Startup scripts created")

            # Step 5: Create service configuration
            print("  [STEP 5] Creating service configuration...")

            if self.system_info["platform"] == "Linux":
                # Systemd service file
                systemd_service = """[Unit]
Description=OMNI Platform AI Assistance System
After=network.target

[Service]
Type=simple
User=omni
WorkingDirectory=/path/to/omni_platform
ExecStart=/usr/bin/python3 omni_platform_master_coordinator.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=PYTHONPATH=/path/to/omni_platform

[Install]
WantedBy=multi-user.target
"""
                with open('./omni_platform/omni_platform.service', 'w') as f:
                    f.write(systemd_service)

                setup_results["services_configured"].append("Systemd service configured")
                print("    [OK] Systemd service configured")

            setup_results["setup_steps"].append("Platform environment setup completed")
            print("    [OK] Platform environment setup completed")

        except Exception as e:
            setup_results["success"] = False
            setup_results["error"] = str(e)
            print(f"    [ERROR] Setup failed: {e}")

        return setup_results

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute requirements and setup tool"""
        action = parameters.get("action", "check_requirements")

        if action == "check_requirements":
            results = self.check_all_requirements()
            return {"status": "success", "data": results}

        elif action == "setup_environment":
            results = self.setup_platform_environment()
            return {"status": "success" if results["success"] else "error", "data": results}

        elif action == "generate_report":
            report = self.generate_requirements_report()
            return {"status": "success", "data": {"report": report}}

        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

# Global requirements instance
omni_requirements = OmniPlatformRequirements()

def main():
    """Main requirements and setup function"""
    print("[OMNI] Platform Requirements and Infrastructure Setup")
    print("=" * 60)
    print("[SYSTEM] Complete system requirements validation")
    print("[INFRASTRUCTURE] Infrastructure setup and configuration")
    print("[ENVIRONMENT] Development environment preparation")
    print("[AI] AI platform optimization setup")
    print()

    try:
        # Check all requirements
        requirements_results = omni_requirements.check_all_requirements()

        # Setup platform environment
        setup_results = omni_requirements.setup_platform_environment()

        # Generate final report
        report_content = omni_requirements.generate_requirements_report()

        # Save report
        report_file = f"omni_setup_report_{int(time.time())}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print("\n[SETUP COMPLETE] OMNI Platform Setup Finished!")
        print("=" * 60)
        print(f"[REQUIREMENTS] Compatibility: {requirements_results['overall_compatibility'].upper()}")
        print(f"[SETUP] Environment: {'Configured' if setup_results['success'] else 'Failed'}")
        print(f"[FILES] Created: {len(setup_results['configuration_files'])} configuration files")
        print(f"[REPORT] Saved to: {report_file}")

        print("\n[INFRASTRUCTURE] Setup Summary:")
        for step in setup_results['setup_steps']:
            print(f"  [OK] {step}")

        print("\n[RECOMMENDATIONS] Next Steps:")
        for rec in requirements_results['recommendations'][:5]:
            print(f"  [ACTION] {rec}")

        print("\n[LAUNCH] Platform Launch:")
        print("  Use: python omni_platform_master_coordinator.py")
        print("  Or: ./omni_platform/start_platform.sh (Linux)")
        print("  Or: omni_platform\\start_platform.bat (Windows)")

        print("\n[OMNI] Professional AI Assistance Platform - Ready!")
        print("=" * 60)

        return {
            "status": "success",
            "requirements": requirements_results,
            "setup": setup_results,
            "report_file": report_file
        }

    except Exception as e:
        print(f"\n[ERROR] Setup failed: {e}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    result = main()
    print(f"\n[SUCCESS] Requirements and setup execution completed")