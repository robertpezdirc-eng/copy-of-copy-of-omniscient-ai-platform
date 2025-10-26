import os
import json
import time

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


class OmniLearner:
    def __init__(self, config, logger=None):
        self.config = config or {}
        self.logger = logger
        le = self.config.get("learning_engine", {})
        self.cache_dir = le.get("cache_dir", "./cache/")
        self.interval_seconds = int(le.get("interval_seconds", 30))
        self.max_memory_gb = float(le.get("max_memory_gb", 2))
        self.model_storage = le.get("model_storage")
        out = self.config.get("output", {})
        self.save_results = bool(out.get("save_results", True))
        self.export_csv = bool(out.get("export_csv", True))
        self.upload_to_google_cloud = bool(out.get("upload_to_google_cloud", False))
        self.local_summary_file = out.get("local_summary_file", "./learn_summary.json")
        os.makedirs(self.cache_dir, exist_ok=True)
        # Optional GCS client
        self.gcs_client = None
        if self.upload_to_google_cloud and storage is not None:
            try:
                self.gcs_client = storage.Client()
            except Exception as e:
                if self.logger:
                    self.logger.warn(f"GCS client init failed: {e}")
        elif self.upload_to_google_cloud:
            if self.logger:
                self.logger.warn("google-cloud-storage not installed; skipping cloud uploads.")

    def train(self, data):
        metrics = {
            "timestamp": int(time.time()),
            "records": len(data),
            "cache_dir": self.cache_dir,
            "max_memory_gb": self.max_memory_gb,
        }
        # Save JSON summary
        if self.save_results:
            try:
                prev = {}
                if os.path.exists(self.local_summary_file):
                    with open(self.local_summary_file, "r", encoding="utf-8") as f:
                        prev = json.load(f)
                prev["last_run"] = metrics["timestamp"]
                prev["total_records"] = prev.get("total_records", 0) + metrics["records"]
                prev["runs"] = prev.get("runs", 0) + 1
                with open(self.local_summary_file, "w", encoding="utf-8") as f:
                    json.dump(prev, f, indent=2)
                if self.logger:
                    self.logger.log(f"Saved summary to {self.local_summary_file}")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed saving summary: {e}")
        # Export CSV if requested
        if self.export_csv:
            try:
                csv_path = os.path.splitext(self.local_summary_file)[0] + ".csv"
                line = f'{metrics["timestamp"]},{metrics["records"]}\n'
                with open(csv_path, "a", encoding="utf-8") as cf:
                    cf.write(line)
                if self.logger:
                    self.logger.log(f"Appended metrics to {csv_path}")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed writing CSV: {e}")
        # Upload to GCS
        if self.upload_to_google_cloud and self.gcs_client and self.model_storage:
            bucket_name, prefix = parse_gcs_uri(self.model_storage)
            if bucket_name:
                try:
                    bucket = self.gcs_client.bucket(bucket_name)
                    dest_name = os.path.join(prefix or "", "learn_summary.json")
                    blob = bucket.blob(dest_name)
                    blob.upload_from_filename(self.local_summary_file)
                    if self.logger:
                        self.logger.log(f"Uploaded summary to gs://{bucket_name}/{dest_name}")
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"GCS upload failed: {e}")