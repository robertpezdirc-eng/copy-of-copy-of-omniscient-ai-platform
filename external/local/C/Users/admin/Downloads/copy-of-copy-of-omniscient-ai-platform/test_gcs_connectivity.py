#!/usr/bin/env python3
"""
Test Google Cloud Storage connectivity
"""

import os
import json
import sys

def test_gcs_connectivity():
    """Test GCS connectivity with current credentials"""
    print("Testing Google Cloud Storage connectivity...")

    # Set credentials environment variable
    if os.path.exists("service_account.json"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"
        print("Using service account credentials")
    else:
        print("No service account file found")

    try:
        from google.cloud import storage
        print("Google Cloud Storage library imported successfully")

        # Initialize GCS client
        client = storage.Client()
        print(f"GCS client initialized for project: {client.project}")

        # List buckets (this will test permissions)
        buckets = list(client.list_buckets(max_results=5))
        print(f"Found {len(buckets)} buckets:")

        for bucket in buckets:
            print(f"  - {bucket.name}")

        # Try to create/access a test bucket
        test_bucket_name = "omni-test-bucket-12345"
        try:
            bucket = client.bucket(test_bucket_name)
            if not bucket.exists():
                print(f"Creating test bucket: {test_bucket_name}")
                bucket.create()
                print("Test bucket created successfully")

                # Upload a test file
                test_blob = bucket.blob("test_connection.txt")
                test_blob.upload_from_string("OMNI Platform GCS Test - " + str(os.times()))
                print("Test file uploaded successfully")

                # Clean up
                test_blob.delete()
                bucket.delete()
                print("Test completed and cleaned up")

            else:
                print(f"Test bucket {test_bucket_name} already exists")

        except Exception as e:
            print(f"Bucket operation failed: {e}")

        return True

    except Exception as e:
        print(f"GCS connectivity test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_gcs_connectivity()
    sys.exit(0 if success else 1)