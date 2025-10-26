#!/bin/bash
# OMNI Rollback Script
# Rolls back to previous stable version

set -e

TARGET_INSTANCE="${1:-v1}"

echo "=== OMNI Rollback ==="
echo "Rolling back to: $TARGET_INSTANCE"

# Check if target instance exists and is healthy
if systemctl is-active --quiet "omni-autolearn-$TARGET_INSTANCE"; then
    echo "Target instance $TARGET_INSTANCE is already running"

    # Switch to target instance
    python /opt/omni/omni_immortal_watchdog.py switch "$TARGET_INSTANCE"

    # Stop the other instance
    OTHER_INSTANCE=$([ "$TARGET_INSTANCE" = "v1" ] && echo "v2" || echo "v1")
    systemctl stop "omni-autolearn-$OTHER_INSTANCE"

    echo "Rollback completed successfully!"
    echo "Active instance: $TARGET_INSTANCE"

else
    echo "Target instance $TARGET_INSTANCE is not healthy"
    echo "Starting target instance..."

    systemctl start "omni-autolearn-$TARGET_INSTANCE"

    # Wait and check
    sleep 10

    if systemctl is-active --quiet "omni-autolearn-$TARGET_INSTANCE"; then
        python /opt/omni/omni_immortal_watchdog.py switch "$TARGET_INSTANCE"
        echo "Rollback completed"
    else
        echo "Failed to start target instance"
        exit 1
    fi
fi
