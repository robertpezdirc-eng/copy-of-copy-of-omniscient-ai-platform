#!/usr/bin/env python3
"""
OMNI Singularity v10.0 - Markec Package Creator
Creates complete OMNI platform package in markec folder for Google Cloud deployment
"""

import os
import shutil
import json
from pathlib import Path

def create_markec_package():
    """Create complete OMNI Singularity package in markec folder"""
    print("Creating OMNI Singularity v10.0 - Markec Package")
    print("=" * 55)

    # Essential files to copy
    essential_files = [
        # Core quantum components
        "omni_quantum_cores.py",
        "omni_quantum_storage.py",
        "omni_quantum_entanglement.py",
        "omni_quantum_security.py",
        "omni_quantum_monitoring.py",
        "omni_quantum_industrial_integration.py",
        "omni_quantum_autoscaling.py",
        "omni_quantum_validation.py",

        # Singularity core
        "omni_singularity_core.py",
        "omni_singularity_launcher.py",

        # Google Cloud integration
        "omni_google_cloud_integration.py",

        # Configuration
        "config.txt",
        "requirements.txt",
        "requirements-gpu.txt",
        "requirements-omni.txt",

        # Docker files
        "Dockerfile.omni-singularity",
        "docker-compose.omni.yml",

        # Deployment scripts
        "start-omni-singularity.sh",
        "setup-google-cloud.sh",

        # Documentation
        "README-OMNI-SINGULARITY.md"
    ]

    # Create markec directory structure
    markec_dir = Path("markec")
    markec_dir.mkdir(exist_ok=True)

    # Copy essential files
    copied_files = []
    for file_path in essential_files:
        if os.path.exists(file_path):
            shutil.copy2(file_path, markec_dir / file_path)
            copied_files.append(file_path)
            print(f"  ✅ Copied: {file_path}")
        else:
            print(f"  ⚠️ File not found: {file_path}")

    # Create package manifest
    package_manifest = {
        "package_name": "OMNI Singularity v10.0 - Markec Edition",
        "google_cloud_api_key": "AIzaSyAyKCIUE1b8SQF9g-Ok2WDB_zvtkCkYC8M",
        "created_at": time.time(),
        "total_files": len(copied_files),
        "files": copied_files,
        "version": "10.0",
        "description": "Complete OMNI Singularity Quantum Platform for Google Cloud",
        "features": [
            "Neural Fusion Engine (10 cores)",
            "Omni Memory Core (Personal learning)",
            "Quantum Compression (RAM optimization)",
            "Adaptive Reasoning (Task-adaptive)",
            "8 Specialized Modules",
            "5 Specialized Agents",
            "BCI Integration (OpenBCI, Emotiv, Muse)",
            "Google Cloud Integration",
            "Post-Quantum Security",
            "Real-Time Monitoring"
        ]
    }

    # Save package manifest
    with open(markec_dir / "package-manifest.json", 'w') as f:
        json.dump(package_manifest, f, indent=2)

    print(f"\n✅ Package created successfully in 'markec' folder")
    print(f"📦 Total files copied: {len(copied_files)}")

    return len(copied_files)

def create_google_cloud_deployment_package():
    """Create Google Cloud specific deployment package"""
    print("\n☁️ Creating Google Cloud deployment package...")

    # Create Google Cloud deployment files
    gcp_files = {
        "deploy-to-google-cloud.py": """
#!/usr/bin/env python3
import os
import sys

def deploy_to_google_cloud():
    print("☁️ Deploying OMNI Singularity to Google Cloud...")
    print("🔑 API Key: AIzaSyAyKCIUE1b8SQF9g-Ok2WDB_zvtkCkYC8M")

    # Set environment variables
    os.environ['GOOGLE_CLOUD_KEY'] = 'AIzaSyAyKCIUE1b8SQF9g-Ok2WDB_zvtkCkYC8M'
    os.environ['GOOGLE_CLOUD_PROJECT'] = 'omni-singularity-project'

    print("✅ Google Cloud environment configured")
    print("🚀 Ready for deployment to Google Cloud Platform")

if __name__ == "__main__":
    deploy_to_google_cloud()
""",
        "gcp-credentials.json": """{
  "type": "service_account",
  "project_id": "omni-singularity-project",
  "private_key_id": "key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\\n-----END PRIVATE KEY-----\\n",
  "client_email": "omni-singularity@omni-singularity-project.iam.gserviceaccount.com",
  "client_id": "client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}""",
        ".env": """# OMNI Singularity Google Cloud Configuration
GOOGLE_API_KEY=AIzaSyAyKCIUE1b8SQF9g-Ok2WDB_zvtkCkYC8M
GOOGLE_CLOUD_KEY=AIzaSyAyKCIUE1b8SQF9g-Ok2WDB_zvtkCkYC8M
GOOGLE_CLOUD_PROJECT=omni-singularity-project
GOOGLE_APPLICATION_CREDENTIALS=/app/gcp-credentials.json

# OpenAI Configuration (add your key)
OPENAI_API_KEY=your_openai_key_here

# Redis Configuration
REDIS_PASSWORD=omni_redis_secure_pass

# Grafana Configuration
GRAFANA_PASSWORD=omni_grafana_admin
"""
    }

    # Create Google Cloud files
    for filename, content in gcp_files.items():
        filepath = Path("markec") / filename
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  ✅ Created: {filename}")

    print("✅ Google Cloud deployment package created")

def display_package_summary():
    """Display package summary"""
    print("\n📊 OMNI Singularity v10.0 - Markec Package Summary")
    print("=" * 55)

    markec_path = Path("markec")
    if markec_path.exists():
        files = list(markec_path.glob("**/*"))
        files = [f for f in files if f.is_file()]

        print(f"📁 Package location: {markec_path.absolute()}")
        print(f"📦 Total files: {len(files)}")

        # Categorize files
        categories = {
            "Core Components": [f for f in files if "omni_" in f.name and f.suffix == ".py"],
            "Configuration": [f for f in files if f.suffix in [".txt", ".json", ".env"]],
            "Deployment": [f for f in files if "deploy" in f.name or "docker" in f.name],
            "Documentation": [f for f in files if "README" in f.name or "manifest" in f.name]
        }

        for category, category_files in categories.items():
            print(f"  {category}: {len(category_files)} files")

        print("\n🚀 Ready for Google Cloud deployment!")
        print("💡 Usage: cd markec && python omni_singularity_v10_complete.py")

if __name__ == "__main__":
    # Create the complete package
    files_copied = create_markec_package()
    create_google_cloud_deployment_package()
    display_package_summary()

    print("\n🎉 OMNI Singularity v10.0 - Markec Package Complete!")
    print("\n🌟 Next Steps:")
    print("1. cd markec")
    print("2. python omni_singularity_v10_complete.py")
    print("3. python deploy-to-google-cloud.py")
    print("\n☁️ Google Cloud Integration Ready!")
    print("🔑 API Key: AIzaSyAyKCIUE1b8SQF9g-Ok2WDB_zvtkCkYC8M")