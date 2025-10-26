#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 Individual Module Builder
Builds specific Omni modules with intelligent dependency management

Usage:
    python build_module.py --module omni-platform-v1.0.0
    python build_module.py --module omni-desktop-v1.0.0 --force
    python build_module.py --list-modules
"""

import os
import json
import argparse
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
import sys

class OmniModuleBuilder:
    """Intelligent builder for individual Omni modules"""

    def __init__(self):
        self.deployment_dir = "deployment-packages"
        self.build_configs = {
            "omni-platform-v1.0.0": {
                "type": "python_backend",
                "source_dir": "omni_platform/backend",
                "requirements": "omni_platform/backend/requirements.txt",
                "build_command": "python setup_platform.py",
                "output_dir": "deployment-packages/omni-platform-v1.0.0",
                "dependencies": []
            },
            "omni-desktop-v1.0.0": {
                "type": "electron_app",
                "source_dir": "omni_desktop",
                "requirements": "omni_desktop/package.json",
                "build_command": "cd omni_desktop && npm install && npm run build",
                "output_dir": "deployment-packages/omni-desktop-v1.0.0",
                "dependencies": ["omni-platform-v1.0.0"]
            },
            "omni-frontend-v1.0.0": {
                "type": "react_app",
                "source_dir": "omni_platform/frontend",
                "requirements": "omni_platform/frontend/package.json",
                "build_command": "cd omni_platform/frontend && npm install && npm run build",
                "output_dir": "deployment-packages/omni-frontend-v1.0.0",
                "dependencies": ["omni-platform-v1.0.0"]
            }
        }

    def list_available_modules(self):
        """List all available modules"""
        print("Available Omni Modules:")
        print("=" * 40)

        for module_name, config in self.build_configs.items():
            print(f"Module: {module_name}")
            print(f"  Type: {config['type']}")
            print(f"  Source: {config['source_dir']}")
            print(f"  Dependencies: {', '.join(config['dependencies']) if config['dependencies'] else 'None'}")
            print()

    def check_dependencies(self, module_name: str) -> tuple[bool, list]:
        """Check if module dependencies are satisfied"""
        if module_name not in self.build_configs:
            return False, [f"Module {module_name} not found in build configuration"]

        config = self.build_configs[module_name]
        dependencies = config.get('dependencies', [])
        missing_deps = []

        for dep in dependencies:
            dep_path = os.path.join(self.deployment_dir, dep)
            if not os.path.exists(dep_path):
                missing_deps.append(dep)

        return len(missing_deps) == 0, missing_deps

    def build_module(self, module_name: str, force: bool = False) -> bool:
        """Build specific module"""

        print(f"Building module: {module_name}")
        print("-" * 40)

        # Check if module exists in config
        if module_name not in self.build_configs:
            print(f"ERROR: Module {module_name} not found in build configuration")
            return False

        config = self.build_configs[module_name]

        # Check dependencies unless forced
        if not force:
            deps_ok, missing_deps = self.check_dependencies(module_name)
            if not deps_ok:
                print(f"ERROR: Missing dependencies: {', '.join(missing_deps)}")
                print("Use --force to build anyway, or build dependencies first")
                return False

        # Create output directory
        output_dir = config['output_dir']
        os.makedirs(output_dir, exist_ok=True)

        # Execute build command
        build_command = config['build_command']
        print(f"Executing: {build_command}")

        try:
            # Change to source directory if needed
            source_dir = config['source_dir']
            if os.path.exists(source_dir):
                original_cwd = os.getcwd()
                os.chdir(source_dir)

                # Execute build
                result = subprocess.run(build_command, shell=True, capture_output=True, text=True)

                # Return to original directory
                os.chdir(original_cwd)

                if result.returncode == 0:
                    print(f"SUCCESS: {module_name} built successfully")

                    # Copy build artifacts to deployment directory
                    self._copy_build_artifacts(config, output_dir)

                    # Update build timestamp
                    self._update_build_timestamp(module_name)

                    return True
                else:
                    print(f"BUILD FAILED: {module_name}")
                    print(f"Error: {result.stderr}")
                    return False

            else:
                print(f"ERROR: Source directory {source_dir} not found")
                return False

        except Exception as e:
            print(f"ERROR: Exception during build: {e}")
            return False

    def _copy_build_artifacts(self, config: dict, output_dir: str):
        """Copy build artifacts to deployment directory"""

        source_dir = config['source_dir']

        # Copy common build artifacts
        common_artifacts = [
            'dist',
            'build',
            'output',
            '*.exe',
            '*.app',
            '*.deb',
            '*.rpm'
        ]

        for artifact in common_artifacts:
            source_path = os.path.join(source_dir, artifact)
            if os.path.exists(source_path):
                if os.path.isdir(source_path):
                    # Copy directory
                    dest_path = os.path.join(output_dir, os.path.basename(source_path))
                    if os.path.exists(dest_path):
                        shutil.rmtree(dest_path)
                    shutil.copytree(source_path, dest_path)
                    print(f"Copied directory: {artifact}")
                elif os.path.isfile(source_path):
                    # Copy file
                    shutil.copy2(source_path, output_dir)
                    print(f"Copied file: {artifact}")

    def _update_build_timestamp(self, module_name: str):
        """Update build timestamp for module"""

        timestamp_file = os.path.join(self.deployment_dir, module_name, "build_timestamp.txt")

        with open(timestamp_file, 'w') as f:
            f.write(f"Built on: {datetime.now().isoformat()}\n")
            f.write(f"Module: {module_name}\n")
            f.write(f"Build system: Omni All-in-One Platform\n")

    def get_module_info(self, module_name: str) -> dict:
        """Get detailed information about module"""

        if module_name not in self.build_configs:
            return {"error": "Module not found"}

        config = self.build_configs[module_name]
        output_dir = config['output_dir']

        # Get build information
        build_info = {
            "module_name": module_name,
            "module_type": config['type'],
            "source_directory": config['source_dir'],
            "output_directory": output_dir,
            "dependencies": config['dependencies'],
            "exists": os.path.exists(output_dir),
            "build_timestamp": None,
            "build_size": 0
        }

        # Check for build timestamp
        timestamp_file = os.path.join(output_dir, "build_timestamp.txt")
        if os.path.exists(timestamp_file):
            with open(timestamp_file, 'r') as f:
                build_info["build_timestamp"] = f.read().strip()

        # Calculate build size
        if os.path.exists(output_dir):
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(output_dir):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, IOError):
                        pass

            build_info["build_size"] = total_size / (1024 * 1024)  # Size in MB

        return build_info

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='OMNI Module Builder')
    parser.add_argument('--module', type=str, help='Module to build')
    parser.add_argument('--list-modules', action='store_true', help='List available modules')
    parser.add_argument('--info', type=str, help='Get info about specific module')
    parser.add_argument('--force', action='store_true', help='Force build even with missing dependencies')
    parser.add_argument('--deployment-dir', default='deployment-packages', help='Deployment directory')

    args = parser.parse_args()

    # Create builder instance
    builder = OmniModuleBuilder()

    if args.list_modules:
        builder.list_available_modules()
        return

    if args.info:
        info = builder.get_module_info(args.info)
        print(f"Module Information: {args.info}")
        print("=" * 40)
        for key, value in info.items():
            print(f"{key}: {value}")
        return

    if not args.module:
        print("ERROR: Module name required. Use --module <module_name> or --list-modules")
        return

    # Build the module
    success = builder.build_module(args.module, args.force)

    if success:
        print(f"\nModule {args.module} build completed successfully!")
        print("\nNext steps:")
        print(f"1. Check module: python build_module.py --info {args.module}")
        print("2. Test platform: python omni_build_runner.py"
        print("3. Check all builds: python omni_build_manager.py"
    else:
        print(f"\nModule {args.module} build failed!")
        print("Check error messages above for details.")

if __name__ == "__main__":
    main()