#!/bin/bash
# OMNI Hot Upgrade Script
# Performs zero-downtime upgrades

set -e

NEW_VERSION="$1"
UPGRADE_INSTANCE="v2"

if [ -z "$NEW_VERSION" ]; then
    echo "Usage: $0 <new_version_path>"
    exit 1
fi

echo "=== OMNI Hot Upgrade ==="
echo "Upgrading to: $NEW_VERSION"

# Stop upgrade instance
echo "Stopping v2 instance for upgrade..."
systemctl stop omni-autolearn-v2

# Backup current v2 (if exists)
if [ -d "/opt/omni/releases/v2" ]; then
    BACKUP_DIR="/opt/omni/backups/v2_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    cp -r /opt/omni/releases/v2/* "$BACKUP_DIR/"
    echo "Backup created: $BACKUP_DIR"
fi

# Deploy new version to v2
echo "Deploying new version to v2..."
rm -rf /opt/omni/releases/v2/*
cp -r "$NEW_VERSION"/* /opt/omni/releases/v2/

# Update virtual environment
echo "Updating Python environment..."
cd /opt/omni/releases/v2
source /opt/omni/omni_env/bin/activate
pip install -r requirements.txt

# Test new version
echo "Testing new version..."
python -c "
import sys
sys.path.insert(0, '/opt/omni/releases/v2')
try:
    from omni_vr_connector import OmniVRConnector
    from omni_gcs_uploader import OmniGCSUploader
    from omni_autolearn_starter import main
    print('All modules imported successfully')
except Exception as e:
    print(f'Test failed: {e}')
    exit(1)
"
echo "New version test: PASSED"

# Start v2 with new version
echo "Starting v2 with new version..."
systemctl start omni-autolearn-v2

# Wait for v2 to become healthy
echo "Waiting for v2 to become healthy..."
sleep 10

# Check if v2 is healthy
if systemctl is-active --quiet omni-autolearn-v2; then
    echo "v2 is healthy - performing switch..."

    # Update configuration to use v2 as active
    python /opt/omni/omni_immortal_watchdog.py switch v2

    # Stop old v1
    systemctl stop omni-autolearn-v1

    echo "Upgrade completed successfully!"
    echo "Active instance: v2"
    echo "Old instance (v1) stopped - available for rollback"

else
    echo "v2 failed to start - rolling back..."
    systemctl stop omni-autolearn-v2

    # Restore from backup if available
    if [ -d "$BACKUP_DIR" ]; then
        cp -r "$BACKUP_DIR"/* /opt/omni/releases/v2/
        echo "Restored from backup"
    fi

    systemctl start omni-autolearn-v1
    echo "Rolled back to v1"
    exit 1
fi
