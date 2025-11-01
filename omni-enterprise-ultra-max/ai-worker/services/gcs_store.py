"""
Simple GCS store for per-tenant model artifacts
Env: GCS_BUCKET_AI_MODELS (required)
"""
import os
import io
from typing import Optional
from google.cloud import storage

_BUCKET = os.getenv("GCS_BUCKET_AI_MODELS")

class GCSStore:
    def __init__(self, bucket: Optional[str] = None):
        self.bucket_name = bucket or _BUCKET
        if not self.bucket_name:
            raise RuntimeError("GCS_BUCKET_AI_MODELS not configured")
        self.client = storage.Client()
        self.bucket = self.client.bucket(self.bucket_name)

    def upload_bytes(self, blob_path: str, data: bytes, content_type: str = "application/octet-stream"):
        blob = self.bucket.blob(blob_path)
        blob.upload_from_file(io.BytesIO(data), content_type=content_type)

    def download_bytes(self, blob_path: str) -> Optional[bytes]:
        blob = self.bucket.blob(blob_path)
        if not blob.exists():
            return None
        return blob.download_as_bytes()
