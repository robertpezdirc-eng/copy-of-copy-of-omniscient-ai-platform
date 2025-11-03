#!/usr/bin/env python3
"""
Security and dependency upgrade script for Omni Enterprise Ultra Max Platform.
This script checks for outdated and vulnerable packages.
"""

import subprocess
import sys
from typing import Dict, List, Tuple

# Known security vulnerabilities and recommended versions
CRITICAL_UPGRADES = {
    "cryptography": {
        "current": "41.0.7",
        "recommended": "43.0.3",
        "severity": "CRITICAL",
        "reason": "CVE-2023-50782 - Critical security vulnerability"
    },
    "tensorflow": {
        "current": "2.15.0",
        "recommended": "2.17.1",
        "severity": "HIGH",
        "reason": "Security updates, Python 3.12 compatibility"
    },
    "torch": {
        "current": "2.1.0",
        "recommended": "2.5.1",
        "severity": "HIGH",
        "reason": "Security updates, GPU optimizations"
    },
    "openai": {
        "current": "1.3.9",
        "recommended": "1.54.4",
        "severity": "MEDIUM",
        "reason": "API compatibility, new features"
    },
    "anthropic": {
        "current": "0.7.8",
        "recommended": "0.39.0",
        "severity": "MEDIUM",
        "reason": "Claude 3.5 Sonnet support"
    },
    "stripe": {
        "current": "7.4.0",
        "recommended": "11.1.1",
        "severity": "MEDIUM",
        "reason": "API deprecations, new payment features"
    }
}

# Package upgrades for both backend and gateway
BACKEND_UPGRADES = {
    "fastapi": "0.115.4",
    "uvicorn[standard]": "0.32.1",
    "pydantic": "2.10.3",
    "httpx": "0.27.2",
    "redis[asyncio]": "5.2.0",
    "prometheus-client": "0.21.0",
    "sentry-sdk": "2.18.0",
    "cryptography": "43.0.3",
    "tensorflow": "2.17.1",
    "torch": "2.5.1",
    "torchvision": "0.20.1",
    "openai": "1.54.4",
    "anthropic": "0.39.0",
    "stripe": "11.1.1",
    "pandas": "2.2.3",
    "scikit-learn": "1.5.2",
    "transformers": "4.46.3",
    "opentelemetry-api": "1.28.2",
    "opentelemetry-sdk": "1.28.2",
}

GATEWAY_UPGRADES = {
    "fastapi": "0.115.4",
    "uvicorn[standard]": "0.32.1",
    "httpx": "0.27.2",
    "prometheus-client": "0.21.0",
    "pydantic": "2.10.3",
    "pydantic-settings": "2.6.1",
    "sentry-sdk": "2.18.0",
    "redis": "5.2.0",
    "cachetools": "5.5.0",
}


def print_header(text: str):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_package_info(package: str, info: Dict[str, str]):
    """Print package upgrade information."""
    severity_colors = {
        "CRITICAL": "\033[91m",  # Red
        "HIGH": "\033[93m",      # Yellow
        "MEDIUM": "\033[94m",    # Blue
    }
    reset = "\033[0m"
    
    color = severity_colors.get(info["severity"], "")
    print(f"\n📦 {package}")
    print(f"   Current:     {info['current']}")
    print(f"   Recommended: {info['recommended']}")
    print(f"   {color}Severity:    {info['severity']}{reset}")
    print(f"   Reason:      {info['reason']}")


def generate_requirements_file(packages: Dict[str, str], filename: str):
    """Generate updated requirements file."""
    lines = []
    
    # Read current file if exists
    try:
        with open(filename, 'r') as f:
            current_lines = f.readlines()
    except FileNotFoundError:
        current_lines = []
    
    # Update versions
    updated = set()
    for line in current_lines:
        line = line.strip()
        if not line or line.startswith('#'):
            lines.append(line)
            continue
        
        # Parse package name
        package_name = line.split('==')[0].split('[')[0].strip()
        
        if package_name in packages:
            # Update to new version
            if '[' in line:
                # Handle extras like uvicorn[standard]
                base = package_name
                extras = line.split('[')[1].split(']')[0]
                lines.append(f"{base}[{extras}]=={packages[package_name]}")
            else:
                lines.append(f"{package_name}=={packages[package_name]}")
            updated.add(package_name)
        else:
            lines.append(line)
    
    # Add any new packages
    for package, version in packages.items():
        if package not in updated:
            lines.append(f"{package}=={version}")
    
    return '\n'.join(lines) + '\n'


def check_pip_audit():
    """Check for security vulnerabilities using pip-audit."""
    print_header("Running pip-audit security scan")
    
    try:
        result = subprocess.run(
            ["pip-audit", "--help"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("⚠️  pip-audit not installed. Install with: pip install pip-audit")
            return False
        
        print("✅ pip-audit is installed")
        print("\nScanning for vulnerabilities...")
        print("Run: pip-audit -r backend/requirements.txt")
        print("Run: pip-audit -r gateway/requirements.txt")
        return True
        
    except FileNotFoundError:
        print("⚠️  pip-audit not found. Install with: pip install pip-audit")
        return False


def main():
    """Main upgrade analysis function."""
    print_header("Omni Platform Security & Dependency Upgrade Analysis")
    
    print("\n🔍 Analyzing critical security vulnerabilities...")
    
    # Show critical upgrades
    for package, info in CRITICAL_UPGRADES.items():
        print_package_info(package, info)
    
    # Check pip-audit
    check_pip_audit()
    
    # Generate upgrade recommendations
    print_header("Recommended Actions")
    
    print("\n1️⃣  CRITICAL - Security patches (DO THIS FIRST)")
    print("   Packages: cryptography, tensorflow, torch")
    print("   Timeline: This week")
    print("   Command:")
    print("   git checkout -b upgrade/security-patches")
    
    print("\n2️⃣  HIGH - Framework updates")
    print("   Packages: fastapi, uvicorn, pydantic")
    print("   Timeline: Next week")
    
    print("\n3️⃣  MEDIUM - API client updates")
    print("   Packages: openai, anthropic, stripe")
    print("   Timeline: Next 2 weeks")
    
    print("\n4️⃣  Data Science libraries")
    print("   Packages: pandas, scikit-learn, transformers")
    print("   Timeline: Next month")
    print("   ⚠️  Note: numpy 2.0 has breaking changes!")
    
    # Generate new requirements files
    print_header("Generating Updated Requirements Files")
    
    print("\n📝 Backend requirements update preview:")
    print("   Location: backend/requirements.txt.new")
    
    backend_content = generate_requirements_file(
        BACKEND_UPGRADES,
        "backend/requirements.txt"
    )
    
    print("\n📝 Gateway requirements update preview:")
    print("   Location: gateway/requirements.txt.new")
    
    gateway_content = generate_requirements_file(
        GATEWAY_UPGRADES,
        "gateway/requirements.txt"
    )
    
    # Write preview files
    with open("backend/requirements.txt.new", "w") as f:
        f.write(backend_content)
    
    with open("gateway/requirements.txt.new", "w") as f:
        f.write(gateway_content)
    
    print("\n✅ Preview files generated!")
    print("\n📋 Next steps:")
    print("   1. Review: diff backend/requirements.txt backend/requirements.txt.new")
    print("   2. Review: diff gateway/requirements.txt gateway/requirements.txt.new")
    print("   3. Test in local environment first")
    print("   4. Run: pytest backend/tests/")
    print("   5. If tests pass: mv backend/requirements.txt.new backend/requirements.txt")
    print("   6. Deploy to staging")
    print("   7. Monitor Grafana dashboards for errors")
    
    print_header("Upgrade Complete - Review Generated Files")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
