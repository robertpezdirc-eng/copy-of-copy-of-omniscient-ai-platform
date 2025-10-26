"""
Cloud Storage Integration for OMNI Platform
- Connect to a Google Cloud Storage bucket
- List and index files (name, content_type, updated, size)
- Generate signed URLs for preview
- Upload and download files
- Background polling to keep index fresh

This module is designed to work in serverless environments (Railway, Cloud Run).
It supports credentials via:
- GOOGLE_APPLICATION_CREDENTIALS (file path)
- GCP_SERVICE_ACCOUNT_KEY_B64 (base64-encoded JSON) handled by caller
"""
from __future__ import annotations
import os
import time
import threading
from typing import List, Dict, Optional

try:
    from google.cloud import storage  # type: ignore
    GOOGLE_CLOUD_AVAILABLE = True
except Exception:
    GOOGLE_CLOUD_AVAILABLE = False

class CloudStorageManager:
    def __init__(self, bucket_name: str, prefix: str = "", polling_interval: int = 15):
        self.bucket_name = bucket_name
        self.prefix = prefix or ""
        self.polling_interval = max(5, int(polling_interval))
        self._client: Optional["storage.Client"] = None
        self._bucket: Optional["storage.Bucket"] = None
        self._index_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._indexed_files: List[Dict[str, Optional[str]]] = []
        self.connected = False
        self.error: Optional[str] = None

    def initialize_client(self) -> bool:
        """Initialize Google Cloud Storage client based on environment."""
        if not GOOGLE_CLOUD_AVAILABLE:
            self.error = "google-cloud-storage library not available"
            return False
        try:
            self._client = storage.Client()
            return True
        except Exception as e:
            self.error = f"Failed to initialize GCS client: {e}"
            return False

    def connect(self) -> bool:
        """Connect to the configured bucket and test access."""
        if not self.initialize_client():
            return False
        try:
            self._bucket = self._client.bucket(self.bucket_name)
            # Test access by listing a single blob
            _ = list(self._bucket.list_blobs(prefix=self.prefix, max_results=1))
            self.connected = True
            self.error = None
            return True
        except Exception as e:
            self.error = f"Failed to connect to bucket '{self.bucket_name}': {e}"
            self.connected = False
            return False

    def list_files(self, limit: int = 200) -> List[Dict[str, Optional[str]]]:
        """List files with basic metadata from the bucket/prefix."""
        if not self.connected or not self._bucket:
            return []
        files: List[Dict[str, Optional[str]]] = []
        try:
            for i, blob in enumerate(self._bucket.list_blobs(prefix=self.prefix)):
                if i >= limit:
                    break
                files.append({
                    "name": blob.name,
                    "content_type": getattr(blob, "content_type", None),
                    "updated": getattr(blob, "updated", None).isoformat() if getattr(blob, "updated", None) else None,
                    "size": str(getattr(blob, "size", None)) if getattr(blob, "size", None) is not None else None,
                })
        except Exception as e:
            self.error = f"Error listing files: {e}"
        return files

    def index_once(self) -> None:
        """Refresh in-memory index one time."""
        files = self.list_files(limit=2000)
        with self._lock:
            self._indexed_files = files

    def start_indexing(self) -> None:
        """Start background indexing thread."""
        if self._index_thread and self._index_thread.is_alive():
            return
        self._stop_event.clear()
        self._index_thread = threading.Thread(target=self._index_loop, daemon=True)
        self._index_thread.start()

    def stop_indexing(self) -> None:
        self._stop_event.set()
        if self._index_thread and self._index_thread.is_alive():
            self._index_thread.join(timeout=2)

    def _index_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.index_once()
            except Exception:
                pass
            time.sleep(self.polling_interval)

    def get_index(self) -> List[Dict[str, Optional[str]]]:
        with self._lock:
            return list(self._indexed_files)

    def generate_signed_url(self, blob_name: str, expiration_seconds: int = 3600) -> Optional[str]:
        """Generate a signed URL for previewing/downloading a blob."""
        if not self.connected or not self._client or not self._bucket:
            return None
        try:
            blob = self._bucket.blob(blob_name)
            url = blob.generate_signed_url(expiration=expiration_seconds)
            return url
        except Exception:
            # Signed URLs may fail if credentials are not suitable; return None gracefully
            return None

    def upload_bytes(self, blob_name: str, data: bytes, content_type: Optional[str] = None) -> bool:
        if not self.connected or not self._bucket:
            return False
        try:
            blob = self._bucket.blob(blob_name)
            blob.upload_from_string(data, content_type=content_type)
            return True
        except Exception:
            return False

    def download_bytes(self, blob_name: str) -> Optional[bytes]:
        if not self.connected or not self._bucket:
            return None
        try:
            blob = self._bucket.blob(blob_name)
            return blob.download_as_bytes()
        except Exception:
            return None