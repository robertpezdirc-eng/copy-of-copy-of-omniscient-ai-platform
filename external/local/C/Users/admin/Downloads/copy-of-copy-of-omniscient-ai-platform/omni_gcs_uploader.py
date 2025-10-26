#!/usr/bin/env python3
"""
OMNI GCS Uploader - Auto-upload learning summaries to Google Cloud Storage
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
from omni_event_logger import EventLogger

class OmniGCSUploader:
    def __init__(self, config=None):
        self.logger = EventLogger()
        self.config = config or self.load_config()
        self.bucket_name = self.config.get("learning_engine", {}).get("model_storage", "gs://omni-meta-data/models/").replace("gs://", "").replace("/models/", "")
        self.local_summary_file = self.config.get("output", {}).get("local_summary_file", "./learn_summary.json")
        self.uploaded_files = set()

    def load_config(self):
        """Load configuration from file"""
        try:
            with open("omni_autolearn_config.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.logger.log(f"Config load error: {e}")
            return {}

    def setup_gcp_credentials(self):
        """Set up Google Cloud credentials"""
        # Method 1: Check for service account key file
        credential_paths = [
            "service-account.json",
            "/opt/omni/service-account.json",
            os.path.expanduser("~/service-account.json"),
            "credentials/service-account.json"
        ]

        for cred_path in credential_paths:
            if os.path.exists(cred_path):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
                self.logger.log(f"GCP credentials set from: {cred_path}")
                return True

        # Method 2: Check for existing gcloud auth
        try:
            import subprocess
            result = subprocess.run(["gcloud", "auth", "list", "--filter=status:ACTIVE"],
                                  capture_output=True, text=True, timeout=10)

            if result.returncode == 0 and "ACTIVE" in result.stdout:
                self.logger.log("Using existing gcloud authentication")
                return True
        except Exception as e:
            self.logger.log(f"gcloud auth check failed: {e}")

        # Method 3: Try to use default credentials (GCE, etc.)
        try:
            import google.auth
            creds, project = google.auth.default()
            self.logger.log("Using default Google Cloud credentials")
            return True
        except Exception as e:
            self.logger.log(f"Default credentials not available: {e}")

        self.logger.log("No GCP credentials found - please set up authentication")
        return False

    def ensure_bucket_exists(self):
        """Ensure the GCS bucket exists"""
        try:
            from google.cloud import storage

            # Initialize GCS client
            client = storage.Client()
            bucket = client.bucket(self.bucket_name)

            # Check if bucket exists
            if not bucket.exists():
                self.logger.log(f"Creating bucket: {self.bucket_name}")
                bucket.create()
                self.logger.log(f"Bucket created: {self.bucket_name}")
            else:
                self.logger.log(f"Bucket exists: {self.bucket_name}")

            return True

        except Exception as e:
            self.logger.log(f"Bucket check/creation failed: {e}")
            return False

    def upload_to_gcs(self, local_file, gcs_path=None):
        """Upload file to Google Cloud Storage"""
        try:
            from google.cloud import storage

            if not gcs_path:
                file_name = os.path.basename(local_file)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                gcs_path = f"models/learn_summary_{timestamp}_{file_name}"

            # Initialize GCS client
            client = storage.Client()
            bucket = client.bucket(self.bucket_name)

            # Upload file
            blob = bucket.blob(gcs_path)
            blob.upload_from_filename(local_file)

            self.logger.log(f"Uploaded to GCS: {local_file} -> gs://{self.bucket_name}/{gcs_path}")

            # Track uploaded files
            self.uploaded_files.add(local_file)

            return True

        except Exception as e:
            self.logger.log(f"GCS upload failed: {e}")
            return False

    def check_and_upload(self):
        """Check for new learning summary files and upload them"""
        try:
            # Check if local summary file exists and has content
            if not os.path.exists(self.local_summary_file):
                return False

            # Get file modification time
            file_mtime = os.path.getmtime(self.local_summary_file)
            current_time = time.time()

            # Only upload if file was modified recently (within last hour)
            if current_time - file_mtime > 3600:
                return False

            # Check if we already uploaded this file
            if self.local_summary_file in self.uploaded_files:
                return False

            # Load and check if there's actual data
            try:
                with open(self.local_summary_file, 'r') as f:
                    data = json.load(f)

                # Only upload if there are records or recent runs
                if data.get("total_records", 0) > 0 or data.get("runs", 0) > 0:
                    return self.upload_to_gcs(self.local_summary_file)

            except json.JSONDecodeError:
                # Try to upload CSV file as well
                csv_file = self.local_summary_file.replace('.json', '.csv')
                if os.path.exists(csv_file):
                    return self.upload_to_gcs(csv_file)

            return False

        except Exception as e:
            self.logger.log(f"Upload check failed: {e}")
            return False

    def start_auto_upload(self, interval=60):
        """Start automatic upload service"""
        self.logger.log(f"Starting GCS auto-upload service (interval: {interval}s)")

        if not self.setup_gcp_credentials():
            self.logger.log("Cannot start auto-upload - no GCP credentials")
            return

        if not self.ensure_bucket_exists():
            self.logger.log("Cannot start auto-upload - bucket setup failed")
            return

        self.running = True

        while self.running:
            try:
                self.check_and_upload()
                time.sleep(interval)
            except KeyboardInterrupt:
                self.logger.log("Auto-upload interrupted by user")
                break
            except Exception as e:
                self.logger.log(f"Auto-upload error: {e}")
                time.sleep(interval)

    def stop(self):
        """Stop the auto-upload service"""
        self.running = False
        self.logger.log("GCS auto-upload service stopped")

def main():
    """Main function"""
    print("OMNI GCS Uploader")
    print("=" * 50)

    uploader = OmniGCSUploader()

    print("Choose an option:")
    print("1. Setup GCP credentials")
    print("2. Test GCS upload")
    print("3. Start auto-upload service")
    print("4. Exit")

    choice = input("Enter choice (1-4): ").strip()

    if choice == "1":
        print("Setting up GCP credentials...")
        if uploader.setup_gcp_credentials():
            print("Credentials configured successfully!")
        else:
            print("Failed to configure credentials")
            print("Please:")
            print("1. Create a service account in Google Cloud Console")
            print("2. Download the JSON key file")
            print("3. Place it as 'service-account.json' in the project root")
            print("4. Or run: gcloud auth application-default login")

    elif choice == "2":
        print("Testing GCS upload...")
        if uploader.setup_gcp_credentials() and uploader.ensure_bucket_exists():
            # Create a test file
            test_data = {
                "test": True,
                "timestamp": time.time(),
                "message": "OMNI VR Learning Test"
            }

            test_file = "test_upload.json"
            with open(test_file, 'w') as f:
                json.dump(test_data, f, indent=2)

            if uploader.upload_to_gcs(test_file, "test/test_upload.json"):
                print("Test upload successful!")
                os.remove(test_file)
            else:
                print("Test upload failed")
        else:
            print("Cannot test - credentials or bucket setup failed")

    elif choice == "3":
        print("Starting auto-upload service...")
        print("This will monitor for new learning summaries and upload them to GCS")
        print("Press Ctrl+C to stop")

        try:
            uploader.start_auto_upload()
        except KeyboardInterrupt:
            print("Stopping auto-upload service...")
        finally:
            uploader.stop()

    else:
        print("Exiting...")

if __name__ == "__main__":
    main()