#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import time
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ROOT)
CONFIG_PATH = os.path.join(PROJECT_ROOT, "external_sources.json")
DEST_ROOT_DEFAULT = os.path.join(PROJECT_ROOT, "external")


def log(msg):
    print(msg, flush=True)


def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Config not found: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_dirs(dest_root):
    os.makedirs(dest_root, exist_ok=True)
    os.makedirs(os.path.join(dest_root, "github"), exist_ok=True)
    os.makedirs(os.path.join(dest_root, "gcs"), exist_ok=True)
    os.makedirs(os.path.join(dest_root, "cloudrun"), exist_ok=True)


def git_clone_or_pull(repo, dest_root):
    # repo may be in form owner/repo or full URL
    if repo.startswith("http://") or repo.startswith("https://"):
        url = repo
        name = repo.rstrip("/").split("/")[-1].replace(".git", "")
    else:
        owner, name = repo.split("/")
        url = f"https://github.com/{owner}/{name}.git"

    target_dir = os.path.join(dest_root, "github", f"{name}_from_github")
    if os.path.exists(target_dir) and os.path.isdir(os.path.join(target_dir, ".git")):
        log(f"Updating GitHub repo: {repo}")
        try:
            subprocess.run(["git", "-C", target_dir, "pull"], check=True)
        except Exception as e:
            log(f"WARN: git pull failed for {repo}: {e}")
    else:
        log(f"Cloning GitHub repo: {url} -> {target_dir}")
        try:
            subprocess.run(["git", "clone", url, target_dir], check=True)
        except Exception as e:
            log(f"WARN: git clone failed for {repo}: {e}")


def find_service_account(candidates):
    for c in candidates:
        p = os.path.join(PROJECT_ROOT, c)
        if os.path.exists(p):
            return p
    return None


def gcs_download_bucket(bucket, dest_root, sa_path):
    try:
        from google.cloud import storage  # type: ignore
    except Exception:
        log("WARN: google-cloud-storage not installed. Skipping GCS downloads.")
        return
    if not sa_path:
        log("WARN: No service account JSON found. Skipping GCS downloads.")
        return
    os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", sa_path)

    client = storage.Client()
    try:
        b = client.bucket(bucket)
        # create local dir
        local_dir = os.path.join(dest_root, "gcs", f"{bucket}")
        os.makedirs(local_dir, exist_ok=True)
        blobs = list(client.list_blobs(bucket))
        if not blobs:
            log(f"GCS: Bucket {bucket} has no objects or is inaccessible.")
            return
        count = 0
        for blob in blobs:
            # limit to avoid huge downloads
            if count >= 200:
                log(f"GCS: Stopping after 200 objects for {bucket} (safety limit)")
                break
            rel_path = blob.name.replace("/", os.sep)
            target_path = os.path.join(local_dir, rel_path)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            try:
                blob.download_to_filename(target_path)
                count += 1
            except Exception as e:
                log(f"WARN: Failed to download {blob.name}: {e}")
        log(f"GCS: Downloaded {count} objects from {bucket} into {local_dir}")
    except Exception as e:
        log(f"WARN: Could not access bucket {bucket}: {e}")


def fetch_cloudrun_url(url, dest_root):
    safe_name = url.replace("https://", "").replace("http://", "").replace("/", "_")
    base_dir = os.path.join(dest_root, "cloudrun", safe_name)
    os.makedirs(base_dir, exist_ok=True)

    def _save(endpoint, fname):
        full_url = url.rstrip("/") + endpoint
        try:
            req = Request(full_url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=20) as resp:
                content = resp.read()
            with open(os.path.join(base_dir, fname), "wb") as f:
                f.write(content)
            log(f"Cloud Run: Saved {full_url} -> {fname}")
        except (URLError, HTTPError) as e:
            log(f"Cloud Run: Could not fetch {full_url}: {e}")
        except Exception as e:
            log(f"Cloud Run: Error fetching {full_url}: {e}")

    # Try common endpoints
    _save("/", "index.html")
    _save("/readyz", "readyz.json")
    _save("/healthz", "healthz.json")
    _save("/openapi.json", "openapi.json")


if __name__ == "__main__":
    list_only = "--list-only" in sys.argv
    cfg = load_config()
    dest_root = os.path.join(PROJECT_ROOT, cfg.get("destination_root") or "external")
    ensure_dirs(dest_root)

    repos = cfg.get("github_repos", [])
    buckets = cfg.get("gcs_buckets", [])
    run_urls = cfg.get("cloud_run_urls", [])
    sa_path = find_service_account(cfg.get("service_account_candidates", []))

    log("== External Sources: Summary ==")
    log(f"GitHub repos: {repos}")
    log(f"GCS buckets: {buckets}")
    log(f"Cloud Run URLs: {run_urls}")
    log(f"Service Account: {sa_path or 'None found'}")

    if list_only:
        log("--list-only: Not performing network operations.")
        sys.exit(0)

    # GitHub
    for r in repos:
        git_clone_or_pull(r, dest_root)

    # GCS
    for b in buckets:
        gcs_download_bucket(b, dest_root, sa_path)

    # Cloud Run
    for u in run_urls:
        fetch_cloudrun_url(u, dest_root)

    log("Done.")