from flask import Flask, jsonify
import os
import subprocess
import tempfile
import time

app = Flask(__name__)

REPO_URL = os.environ.get(
    "REPO_URL",
    "https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform.git",
)
REPO_PATH = os.environ.get("REPO_PATH", "omni-enterprise-ultra-max")
BRANCH = os.environ.get("BRANCH", "master")
GCS_BUCKET = os.environ.get("GCS_BUCKET", "gs://omni-unified-backups")
BACKUP_NAME = os.environ.get("BACKUP_NAME", "omni-unified-platform")


@app.get("/run")
def run_backup():
    start = time.time()
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            subprocess.check_call([
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                BRANCH,
                REPO_URL,
                tmpdir,
            ])
            project_root = os.path.join(tmpdir, REPO_PATH)
            env = os.environ.copy()
            env["PROJECT_ROOT"] = project_root
            env["GCS_BUCKET"] = GCS_BUCKET
            env["BACKUP_NAME"] = BACKUP_NAME
            subprocess.check_call(["/app/run_backup.sh"], env=env)
            elapsed = round(time.time() - start, 2)
            return jsonify({"status": "ok", "elapsed_s": elapsed}), 200
        except subprocess.CalledProcessError as e:
            return jsonify({"status": "error", "step": "subprocess", "code": e.returncode}), 500
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500


@app.get("/health")
def health():
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
