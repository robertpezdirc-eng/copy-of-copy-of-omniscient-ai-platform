#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 Intelligent Omni Build Manager
Automatically detects next module to build and guides development

This script:
- Scans deployment packages for build status
- Identifies next module to build
- Provides build recommendations
- Tracks build progress across all 10 modules
"""

import os
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import subprocess

class OmniBuildManager:
    """Intelligent build manager for Omni platform"""

    def __init__(self, deployment_dir: str = "deployment-packages"):
        self.deployment_dir = deployment_dir
        self.build_state_file = "omni_build_state.json"
        self.modules = [
            "omni-platform-v1.0.0",
            "omni-desktop-v1.0.0",
            "omni-frontend-v1.0.0"
        ]

    def get_last_build_time(self, module_path: str) -> Optional[datetime]:
        """Get last build time for module"""
        if not os.path.exists(module_path):
            return None

        last_time = None
        for root, dirs, files in os.walk(module_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if last_time is None or mtime > last_time:
                        last_time = mtime
                except (OSError, ValueError):
                    continue

        return last_time

    def check_modules_status(self) -> Dict[str, Dict[str, Any]]:
        """Check status of all modules"""
        modules_status = {}

        for module in self.modules:
            module_path = os.path.join(self.deployment_dir, module)
            last_build = self.get_last_build_time(module_path)

            modules_status[module] = {
                'path': module_path,
                'exists': os.path.exists(module_path),
                'last_build': last_build.isoformat() if last_build else None,
                'is_built': last_build is not None,
                'build_age_hours': self._calculate_build_age(last_build) if last_build else None
            }

        return modules_status

    def _calculate_build_age(self, build_time: datetime) -> float:
        """Calculate age of build in hours"""
        if build_time:
            age = datetime.now() - build_time
            return age.total_seconds() / 3600
        return float('inf')

    def determine_next_module(self, modules_status: Dict[str, Dict[str, Any]]) -> str:
        """Determine next module to build"""

        # Find unbuilt modules first
        unbuilt_modules = [
            module for module, status in modules_status.items()
            if not status['is_built']
        ]

        if unbuilt_modules:
            return unbuilt_modules[0]

        # If all built, find oldest build
        built_modules = [
            (module, status['build_age_hours'])
            for module, status in modules_status.items()
            if status['is_built']
        ]

        if built_modules:
            oldest_module = max(built_modules, key=lambda x: x[1])
            return oldest_module[0]

        return self.modules[0]  # Fallback to first module

    def generate_build_command(self, module: str) -> str:
        """Generate build command for module"""

        build_commands = {
            "omni-platform-v1.0.0": "python build_platform.py",
            "omni-desktop-v1.0.0": "npm run build-desktop",
            "omni-frontend-v1.0.0": "npm run build-frontend"
        }

        return build_commands.get(module, f"echo 'Build command for {module} not defined'")

    def save_build_state(self, modules_status: Dict[str, Dict[str, Any]], next_module: str):
        """Save current build state"""

        build_state = {
            'last_check': datetime.now().isoformat(),
            'modules_status': modules_status,
            'next_module': next_module,
            'total_modules': len(self.modules),
            'built_modules': sum(1 for status in modules_status.values() if status['is_built']),
            'build_coverage': sum(1 for status in modules_status.values() if status['is_built']) / len(self.modules)
        }

        with open(self.build_state_file, 'w') as f:
            json.dump(build_state, f, indent=2)

    def display_build_status(self, modules_status: Dict[str, Dict[str, Any]], next_module: str):
        """Display comprehensive build status"""

        print("OMNI Platform - Build Status Report")
        print("=" * 50)

        # Overall statistics
        total_modules = len(modules_status)
        built_modules = sum(1 for status in modules_status.values() if status['is_built'])
        build_coverage = (built_modules / total_modules) * 100

        print(f"[STATS] Overall Progress: {built_modules}/{total_modules} modules built ({build_coverage:.1f}%)")
        print(f"[TARGET] Next Module: {next_module}")
        print()

        # Individual module status
        print("[MODULES] Module Details:")
        print("-" * 30)

        for module, status in modules_status.items():
            if status['is_built']:
                age_hours = status['build_age_hours']
                age_str = f"{age_hours:.1f} hours old"
                status_icon = "[BUILT]"
            else:
                age_str = "Not built"
                status_icon = "[MISSING]"

            print(f"{status_icon} {module}")
            print(f"   Path: {status['path']}")
            print(f"   Status: {age_str}")
            print(f"   Exists: {'Yes' if status['exists'] else 'No'}")
            print()

        # Build recommendations
        print("[RECOMMENDATIONS] Build Recommendations:")
        print("-" * 30)
        print(f"1. Next: Build {next_module}")
        print(f"2. Command: {self.generate_build_command(next_module)}")

        if build_coverage < 1.0:
            remaining = total_modules - built_modules
            print(f"3. Remaining: {remaining} modules to build")
        else:
            print("3. All modules built! Consider updates or new features.")

        print()
        print("[ACTIONS] Quick Actions:")
        print("-" * 20)
        print(f"Build next: python build_module.py --module {next_module}")
        print("Check status: python omni_build_manager.py")
        print("Full rebuild: python rebuild_all.py")
    def run(self):
        """Main execution method"""
        print("[INFO] Scanning Omni build status...")

        # Check modules status
        modules_status = self.check_modules_status()

        # Determine next module
        next_module = self.determine_next_module(modules_status)

        # Save build state
        self.save_build_state(modules_status, next_module)

        # Display comprehensive status
        self.display_build_status(modules_status, next_module)

        return next_module

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='OMNI Build Manager')
    parser.add_argument('--deployment-dir', default='deployment-packages',
                       help='Deployment directory path')
    parser.add_argument('--auto-build', action='store_true',
                       help='Automatically start building next module')

    args = parser.parse_args()

    # Create build manager
    manager = OmniBuildManager(args.deployment_dir)

    # Run analysis
    next_module = manager.run()

    # Auto-build if requested
    if args.auto_build:
        print(f"\n🔨 Auto-building {next_module}...")
        build_command = manager.generate_build_command(next_module)

        try:
            result = subprocess.run(build_command, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"✅ Build successful for {next_module}")
            else:
                print(f"❌ Build failed for {next_module}")
                print(f"Error: {result.stderr}")

        except Exception as e:
            print(f"❌ Build execution failed: {e}")

if __name__ == "__main__":
    main()