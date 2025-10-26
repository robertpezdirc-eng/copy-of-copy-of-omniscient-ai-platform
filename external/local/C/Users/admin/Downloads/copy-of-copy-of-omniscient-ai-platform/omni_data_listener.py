import os
import json

try:
    import requests
except ImportError:
    requests = None

try:
    from google.cloud import storage
except Exception:
    storage = None


def parse_gcs_uri(uri: str):
    if not uri or not uri.startswith("gs://"):
        return None, None
    path = uri[5:]
    parts = path.split("/", 1)
    bucket = parts[0]
    prefix = parts[1] if len(parts) > 1 else ""
    return bucket, prefix


class DataCollector:
    def __init__(self, config, logger=None):
        self.config = config or {}
        self.logger = logger
        sysconf = self.config.get("system", {})
        self.integrations = self.config.get("integrations", {})
        self.data_sources = self.config.get("data_sources", [])
        self.use_gcloud = bool(sysconf.get("use_google_cloud"))
        self.openai_enabled = bool(self.integrations.get("openai_enabled"))
        self.max_items = 500
        self.session = requests.Session() if requests else None
        self.gcs_client = None
        if self.use_gcloud and storage is not None:
            try:
                self.gcs_client = storage.Client()
            except Exception as e:
                if self.logger:
                    self.logger.warn(f"GCS client init failed: {e}")
                self.gcs_client = None
        else:
            if self.use_gcloud and self.logger:
                self.logger.warn("google-cloud-storage not installed; skipping GCS data collection.")

    def _collect_local_file(self, path: str):
        data = []
        if not os.path.exists(path):
            if self.logger:
                self.logger.warn(f"Local source not found: {path}")
            return data
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for _ in range(self.max_items):
                    line = f.readline()
                    if not line:
                        break
                    data.append(line.strip())
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed reading {path}: {e}")
        return data

    def _collect_http(self, url: str):
        items = []
        if self.session is None:
            if self.logger:
                self.logger.warn("requests not available; skipping HTTP source: " + url)
            return items
        headers = {}
        if "api.openai.com" in url:
            key = os.getenv("OPENAI_API_KEY")
            if not key or not self.openai_enabled:
                if self.logger:
                    self.logger.warn("OpenAI API not configured; skipping " + url)
                return items
            headers["Authorization"] = f"Bearer {key}"
        try:
            resp = self.session.get(url, timeout=10, headers=headers)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    items.append(json.dumps(data)[:1000])
                except Exception:
                    items.append(resp.text[:1000])
            else:
                if self.logger:
                    self.logger.warn(f"HTTP source {url} returned {resp.status_code}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"HTTP error from {url}: {e}")
        return items

    def _collect_gcs(self, uri: str):
        items = []
        if self.gcs_client is None:
            return items
        bucket_name, prefix = parse_gcs_uri(uri)
        if not bucket_name:
            return items
        try:
            bucket = self.gcs_client.bucket(bucket_name)
            blobs_iter = self.gcs_client.list_blobs(bucket, prefix=prefix)
            count = 0
            for blob in blobs_iter:
                if blob.size and blob.size > 0:
                    if blob.size < 1024 * 256:
                        try:
                            content = blob.download_as_text(encoding="utf-8", errors="ignore")
                            items.append(content[:1000])
                        except Exception as e:
                            if self.logger:
                                self.logger.warn(f"GCS blob read failed {blob.name}: {e}")
                    else:
                        items.append(f"[GCS file: {blob.name}, size={blob.size}]")
                else:
                    items.append(f"[GCS blob: {blob.name}]")
                count += 1
                if len(items) >= self.max_items or count >= 50:
                    break
        except Exception as e:
            if self.logger:
                self.logger.error(f"GCS list/read failed for {uri}: {e}")
        return items

    def collect(self):
        batch = []
        for src in self.data_sources:
            s = src.strip().strip("`").strip('"').strip() if isinstance(src, str) else str(src)
            if s.startswith("gs://"):
                chunk = self._collect_gcs(s)
            elif s.startswith("http://") or s.startswith("https://"):
                chunk = self._collect_http(s)
            else:
                chunk = self._collect_local_file(s)
            batch.extend(chunk)
            if len(batch) >= self.max_items:
                break
        if self.logger:
            self.logger.log(f"Collected {len(batch)} items from {len(self.data_sources)} sources.")
        return batch