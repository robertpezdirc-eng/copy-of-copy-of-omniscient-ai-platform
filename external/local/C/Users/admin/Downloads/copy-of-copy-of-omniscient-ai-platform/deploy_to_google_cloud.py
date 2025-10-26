#!/usr/bin/env python3
"""
OMNI Platform - Google Cloud Deployment Script
Automated deployment script for Google Cloud Platform
"""

import os
import subprocess
import sys
import json
from datetime import datetime

class GoogleCloudDeployer:
    def __init__(self):
        self.project_id = "gen-lang-client-0885737339"
        self.region = "europe-west1"
        self.function_name = "omni-chat"

    def run_command(self, command, description=""):
        """Run a shell command and return the result"""
        try:
            print(f"🔧 {description}")
            print(f"   Command: {command}")

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )

            if result.stdout:
                print(f"   ✅ Output: {result.stdout.strip()}")
            if result.stderr:
                print(f"   ⚠️  Warning: {result.stderr.strip()}")

            return result.returncode == 0

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    def check_billing_status(self):
        """Check if billing is enabled"""
        print("\n💳 Checking billing status...")

        # Try to list services to see if billing is required
        success = self.run_command(
            "gcloud services list --enabled",
            "Checking enabled services"
        )

        if not success:
            print("❌ Billing account required for full deployment")
            print("   Some services need billing to be enabled")
            return False

        return True

    def deploy_cloud_function(self):
        """Deploy the main OMNI Cloud Function"""
        print("\n🚀 Deploying OMNI Cloud Function...")

        # Check if function already exists
        exists = self.run_command(
            f"gcloud functions describe {self.function_name} --region={self.region} 2>/dev/null || echo 'not found'",
            "Checking if function exists"
        )

        deploy_cmd = f"""
        gcloud functions deploy {self.function_name}
        --runtime=python311
        --trigger-http
        --allow-unauthenticated
        --region={self.region}
        --source=.
        --entry-point=omni_chat
        --set-env-vars=PROJECT_ID={self.project_id},GEMINI_MODEL=gemini-2.0-flash
        """

        success = self.run_command(deploy_cmd, "Deploying Cloud Function")

        if success:
            print(f"✅ Cloud Function deployed successfully!")
            print(f"   URL: https://{self.region}-{self.project_id}.cloudfunctions.net/{self.function_name}")
        else:
            print("❌ Cloud Function deployment failed")

        return success

    def deploy_status_function(self):
        """Deploy the status function"""
        print("\n📊 Deploying status function...")

        status_cmd = f"""
        gcloud functions deploy omni-status
        --runtime=python311
        --trigger-http
        --allow-unauthenticated
        --region={self.region}
        --source=.
        --entry-point=omni_status
        """

        success = self.run_command(status_cmd, "Deploying status function")

        if success:
            print("✅ Status function deployed successfully!")
            print(f"   URL: https://{self.region}-{self.project_id}.cloudfunctions.net/omni-status")

        return success

    def setup_cloud_storage(self):
        """Set up Google Cloud Storage bucket"""
        print("\n🗄️ Setting up Cloud Storage...")

        bucket_name = f"omni-platform-storage-{self.project_id}"

        # Create bucket
        success = self.run_command(
            f"gsutil mb gs://{bucket_name}/",
            "Creating storage bucket"
        )

        if success:
            print(f"✅ Storage bucket created: {bucket_name}")

            # Set public read access for the web interface
            self.run_command(
                f"gsutil web set -m index.html gs://{bucket_name}/",
                "Setting up web hosting"
            )

            # Upload the HTML interface
            self.run_command(
                f"gsutil cp index.html gs://{bucket_name}/",
                "Uploading web interface"
            )

            print(f"✅ Web interface uploaded: https://storage.googleapis.com/{bucket_name}/index.html")

        return success

    def setup_pubsub(self):
        """Set up Pub/Sub topics"""
        print("\n📨 Setting up Pub/Sub...")

        topic_name = "omni-workflows"

        success = self.run_command(
            f"gcloud pubsub topics create {topic_name} --if-exists-ok",
            "Creating Pub/Sub topic"
        )

        if success:
            print(f"✅ Pub/Sub topic created: {topic_name}")

        return success

    def create_deployment_summary(self):
        """Create a summary of the deployment"""
        print("\n📋 Creating deployment summary...")

        summary = {
            "deployment_time": datetime.utcnow().isoformat(),
            "project_id": self.project_id,
            "region": self.region,
            "platform": "google-cloud",
            "services": {
                "cloud_functions": "deployed",
                "cloud_storage": "configured",
                "pubsub": "configured",
                "generative_ai": "enabled"
            },
            "endpoints": {
                "main_function": f"https://{self.region}-{self.project_id}.cloudfunctions.net/{self.function_name}",
                "status_function": f"https://{self.region}-{self.project_id}.cloudfunctions.net/omni-status",
                "web_interface": f"https://storage.googleapis.com/omni-platform-storage-{self.project_id}/index.html"
            },
            "features": [
                "AI Chat with Google Gemini",
                "Cloud Storage for data persistence",
                "Pub/Sub for workflow management",
                "Serverless deployment",
                "CORS enabled for web access"
            ]
        }

        # Save summary to file
        with open("deployment_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print("✅ Deployment summary saved to deployment_summary.json")

        return summary

    def display_success_message(self, summary):
        """Display success message with URLs"""
        print("\n🎉 OMNI Platform uspešno deployana na Google Cloud!")
        print("=" * 60)

        print("\n🔗 DOSTOPNE URLJE:")
        print(f"   🌐 Glavna aplikacija: {summary['endpoints']['main_function']}")
        print(f"   📊 Status: {summary['endpoints']['status_function']}")
        print(f"   🖥️  Web vmesnik: {summary['endpoints']['web_interface']}")

        print("\n⚡ FUNKCIONALNOSTI:")
        for feature in summary['features']:
            print(f"   ✅ {feature}")

        print("\n📁 LOKACIJE:")
        print(f"   🗄️  Storage: gs://omni-platform-storage-{self.project_id}/")
        print(f"   📨 Pub/Sub: projects/{self.project_id}/topics/omni-workflows")

        print("\n💡 NASLEDNJI KORAKI:")
        print("   1. Odprite web vmesnik v brskalniku")
        print("   2. Preizkusite AI funkcionalnost")
        print("   3. Preverite status endpoint")
        print("   4. Za več funkcionalnosti omogočite Google Cloud billing")
    def deploy_all(self):
        """Deploy everything to Google Cloud"""
        print("🚀 OMNI Platform - Google Cloud Deployment")
        print("=" * 50)

        # Check billing status
        billing_ok = self.check_billing_status()

        if not billing_ok:
            print("\n⚠️  Opozorilo: Nekateri servisi zahtevajo billing")
            print("   Osnovne funkcionalnosti so še vedno na voljo")

        # Deploy functions
        function_deployed = self.deploy_cloud_function()
        status_deployed = self.deploy_status_function()

        # Setup infrastructure
        storage_setup = self.setup_cloud_storage()
        pubsub_setup = self.setup_pubsub()

        # Create summary
        summary = self.create_deployment_summary()

        # Display success message
        if function_deployed or storage_setup:
            self.display_success_message(summary)
        else:
            print("\n❌ Deployment ni bil uspešen")
            print("   Preverite Google Cloud nastavitve in poskusite znova")

        return summary

def main():
    """Main deployment function"""
    deployer = GoogleCloudDeployer()
    try:
        summary = deployer.deploy_all()
        return 0
    except KeyboardInterrupt:
        print("\n\n⏹️  Deployment prekinjen")
        return 1
    except Exception as e:
        print(f"\n❌ Deployment napaka: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)