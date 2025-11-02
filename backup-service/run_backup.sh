#!/bin/bash
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_ONLY=$(date +%Y%m%d)
PROJECT_ROOT="${PROJECT_ROOT:-/workspace}"
GCS_BUCKET="${GCS_BUCKET:-gs://omni-unified-backups}"
BACKUP_NAME="${BACKUP_NAME:-omni-unified-platform}"
REGION="${REGION:-europe-west1}"
PROJECT_ID="${PROJECT_ID:-refined-graph-471712-n9}"

# Ensure bucket exists
if ! gsutil ls "$GCS_BUCKET" >/dev/null 2>&1; then
  gsutil mb -p "$PROJECT_ID" -l "$REGION" -b on "$GCS_BUCKET" || true
  gsutil uniformbucketlevelaccess set on "$GCS_BUCKET" || true
fi

# Incremental sync to latest
gsutil -m rsync -r -d \
  -x "node_modules/.*|__pycache__/.*|\\.git/.*|\\.venv/.*|venv/.*|build/.*|dist/.*|\\.next/.*|coverage/.*|\\.pytest_cache/.*|\\.mypy_cache/.*|\\.ruff_cache/.*|\\.DS_Store|\\.idea/.*|\\.vscode/settings\\.json|\\..+\\.swp|~$|\\.tmp$" \
  "$PROJECT_ROOT" "$GCS_BUCKET/$BACKUP_NAME/latest/"

# Timestamped snapshot
gsutil -m cp -r \
  "$GCS_BUCKET/$BACKUP_NAME/latest/" \
  "$GCS_BUCKET/$BACKUP_NAME/snapshots/$DATE_ONLY/$TIMESTAMP/"

echo "{\"backup_id\":\"$TIMESTAMP\",\"snapshot\":\"$GCS_BUCKET/$BACKUP_NAME/snapshots/$DATE_ONLY/$TIMESTAMP/\"}" > /tmp/backup_metadata.json

gsutil cp /tmp/backup_metadata.json "$GCS_BUCKET/$BACKUP_NAME/snapshots/$DATE_ONLY/$TIMESTAMP/backup_metadata.json"

exit 0
