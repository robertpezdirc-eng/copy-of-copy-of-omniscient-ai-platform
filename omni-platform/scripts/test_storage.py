from google.cloud import storage
import os

creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
print("GOOGLE_APPLICATION_CREDENTIALS:", creds)

client = storage.Client()
print("Projekt:", client.project)

buckets = list(client.list_buckets())
print("Buckets:", [b.name for b in buckets])