#!/bin/bash
###############################################################################
# Google Cloud Storage Continuous Backup Script
# User requirement: "sproti v google cloud vsake tolk casa shranit"
# Translation: "continuously save to Google Cloud every so often"
###############################################################################

set -e

# Configuration
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_ONLY=$(date +%Y%m%d)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GCS_BUCKET="gs://omni-unified-backups"
BACKUP_NAME="omni-unified-platform"
PROJECT_ID="refined-graph-471712-n9"
REGION="europe-west1"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   OMNI UNIFIED PLATFORM - Google Cloud Storage Backup    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${GREEN}📦 Project Root:${NC} $PROJECT_ROOT"
echo -e "${GREEN}☁️  GCS Bucket:${NC} $GCS_BUCKET"
echo -e "${GREEN}🏗️  Project ID:${NC} $PROJECT_ID"
echo -e "${GREEN}🌍 Region:${NC} $REGION"
echo -e "${GREEN}⏰ Timestamp:${NC} $TIMESTAMP"
echo ""

# Check if gsutil is available
if ! command -v gsutil &> /dev/null; then
    echo -e "${RED}❌ Error: gsutil not found. Please install Google Cloud SDK${NC}"
    exit 1
fi

# Check if bucket exists, create if not
echo -e "${YELLOW}🔍 Checking if bucket exists...${NC}"
if ! gsutil ls "$GCS_BUCKET" &> /dev/null; then
    echo -e "${YELLOW}📦 Creating bucket: $GCS_BUCKET${NC}"
    gsutil mb -p "$PROJECT_ID" -l "$REGION" -b on "$GCS_BUCKET"
    gsutil uniformbucketlevelaccess set on "$GCS_BUCKET"
    echo -e "${GREEN}✅ Bucket created successfully${NC}"
else
    echo -e "${GREEN}✅ Bucket already exists${NC}"
fi
echo ""

# Sync to latest version (incremental backup with exclusions)
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📤 Step 1: Syncing to latest/ (incremental)...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

gsutil -m rsync -r -d \
  -x "node_modules/.*|__pycache__/.*|\.git/.*|\.venv/.*|venv/.*|build/.*|dist/.*|\.next/.*|coverage/.*|\.pytest_cache/.*|\.mypy_cache/.*|\.ruff_cache/.*|\.DS_Store|\.idea/.*|\.vscode/settings\.json|\..+\.swp|~$|\.tmp$" \
  "$PROJECT_ROOT" "$GCS_BUCKET/$BACKUP_NAME/latest/" | tee /tmp/gcs_sync_latest.log

echo -e "${GREEN}✅ Sync to latest/ completed${NC}"
echo ""

# Create timestamped snapshot
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}💾 Step 2: Creating timestamped snapshot...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

gsutil -m cp -r \
  "$GCS_BUCKET/$BACKUP_NAME/latest/" \
  "$GCS_BUCKET/$BACKUP_NAME/snapshots/$DATE_ONLY/$TIMESTAMP/" | tee /tmp/gcs_snapshot.log

echo -e "${GREEN}✅ Snapshot created successfully${NC}"
echo ""

# Create backup metadata
echo -e "${YELLOW}📝 Creating backup metadata...${NC}"
cat > /tmp/backup_metadata.json <<EOF
{
  "backup_id": "$TIMESTAMP",
  "backup_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "project_root": "$PROJECT_ROOT",
  "gcs_bucket": "$GCS_BUCKET",
  "backup_type": "continuous",
  "status": "completed",
  "files_synced": "$(grep -c 'Copying' /tmp/gcs_sync_latest.log || echo 'N/A')",
  "snapshot_location": "$GCS_BUCKET/$BACKUP_NAME/snapshots/$DATE_ONLY/$TIMESTAMP/"
}
EOF

gsutil cp /tmp/backup_metadata.json "$GCS_BUCKET/$BACKUP_NAME/snapshots/$DATE_ONLY/$TIMESTAMP/backup_metadata.json"
echo -e "${GREEN}✅ Metadata uploaded${NC}"
echo ""

# List recent backups
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📋 Recent Snapshots:${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
gsutil ls "$GCS_BUCKET/$BACKUP_NAME/snapshots/$DATE_ONLY/" | tail -5
echo ""

# Lifecycle management info
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ BACKUP COMPLETED SUCCESSFULLY${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}📊 Backup Summary:${NC}"
echo -e "   • Latest backup: $GCS_BUCKET/$BACKUP_NAME/latest/"
echo -e "   • Snapshot: $GCS_BUCKET/$BACKUP_NAME/snapshots/$DATE_ONLY/$TIMESTAMP/"
echo -e "   • Metadata: backup_metadata.json"
echo ""
echo -e "${YELLOW}💡 Lifecycle Recommendations:${NC}"
echo -e "   • Keep snapshots for 30 days"
echo -e "   • Archive old snapshots to Nearline storage after 90 days"
echo -e "   • Delete snapshots older than 1 year"
echo ""
echo -e "${YELLOW}🔄 Next backup will run in 30 minutes (Cloud Scheduler)${NC}"
echo ""

# Clean up temp files
rm -f /tmp/gcs_sync_latest.log /tmp/gcs_snapshot.log /tmp/backup_metadata.json

exit 0
