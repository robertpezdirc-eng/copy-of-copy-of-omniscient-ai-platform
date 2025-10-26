#!/usr/bin/env python3
"""
OMNI Platform - Simple Google Cloud Deployment
Simplified deployment script without Unicode issues
"""

import os
import subprocess
import sys
import json
from datetime import datetime

def run_command(cmd):
    """Run command and return success status"""
    try:
        print(f"Running: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        if result.stderr:
            print(f"Error: {result.stderr.strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"Exception: {e}")
        return False

def main():
    print("OMNI Platform - Google Cloud Deployment")
    print("=" * 50)

    project_id = "gen-lang-client-0885737339"
    region = "europe-west1"

    # Check current services
    print("\nChecking enabled services...")
    run_command("gcloud services list --enabled")

    # Try to deploy Cloud Function
    print("\nDeploying Cloud Function...")
    deploy_cmd = f"gcloud functions deploy omni-chat --runtime=python311 --trigger-http --allow-unauthenticated --region={region} --source=. --entry-point=omni_chat"

    if run_command(deploy_cmd):
        print("SUCCESS: Cloud Function deployed!")
        function_url = f"https://{region}-{project_id}.cloudfunctions.net/omni-chat"
        print(f"Function URL: {function_url}")
    else:
        print("FAILED: Cloud Function deployment")

    # Setup storage
    print("\nSetting up Cloud Storage...")
    bucket_name = f"omni-platform-storage-{project_id}"

    if run_command(f"gsutil mb gs://{bucket_name}/"):
        print(f"SUCCESS: Storage bucket created: {bucket_name}")

        # Upload web interface
        if run_command(f"gsutil cp index.html gs://{bucket_name}/"):
            print("SUCCESS: Web interface uploaded")
            web_url = f"https://storage.googleapis.com/{bucket_name}/index.html"
            print(f"Web URL: {web_url}")
        else:
            print("FAILED: Web interface upload")
    else:
        print("FAILED: Storage bucket creation")

    # Create summary
    summary = {
        "deployment_time": datetime.utcnow().isoformat(),
        "project_id": project_id,
        "platform": "google-cloud",
        "status": "partial",
        "endpoints": {
            "function": f"https://{region}-{project_id}.cloudfunctions.net/omni-chat",
            "web": f"https://storage.googleapis.com/{bucket_name}/index.html"
        }
    }

    with open("deployment_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("\nDeployment summary saved to deployment_summary.json")
    print("OMNI Platform deployment completed!")

if __name__ == "__main__":
    main()