#!/bin/bash
# OMNI Immortal Watchdog Script
# Monitors dual instances and ensures zero downtime

LOG_FILE="/var/log/omni_watchdog.log"
CHECK_INTERVAL=30

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WATCHDOG] $1" >> "$LOG_FILE"
}

check_service() {
    local service=$1
    if systemctl is-active --quiet "$service"; then
        echo "active"
    else
        echo "inactive"
    fi
}

restart_service() {
    local service=$1
    log "Restarting service: $service"

    systemctl stop "$service"
    sleep 3
    systemctl start "$service"

    if systemctl is-active --quiet "$service"; then
        log "Service $service restarted successfully"
        return 0
    else
        log "Failed to restart service $service"
        return 1
    fi
}

check_vr_port() {
    local port=$1
    if ss -ln | grep -q ":$port "; then
        echo "open"
    else
        echo "closed"
    fi
}

# Main monitoring loop
while true; do
    log "Performing health checks..."

    # Check v1 instance
    V1_STATUS=$(check_service omni-autolearn-v1)
    V1_PORT=$(check_vr_port 9090)

    # Check v2 instance
    V2_STATUS=$(check_service omni-autolearn-v2)
    V2_PORT=$(check_vr_port 9091)

    log "v1: service=$V1_STATUS, port=$V1_PORT"
    log "v2: service=$V2_STATUS, port=$V2_PORT"

    # If active instance (v1) is down, try to restart
    if [ "$V1_STATUS" != "active" ]; then
        log "v1 instance is down - attempting restart"
        if ! restart_service omni-autolearn-v1; then
            # If v1 restart fails and v2 is healthy, switch to v2
            if [ "$V2_STATUS" = "active" ] && [ "$V2_PORT" = "open" ]; then
                log "Switching to v2 instance"
                # Update configuration to use v2 as active
                # This would involve updating omni config files
            fi
        fi
    fi

    # Create checkpoint every 5 minutes
    if [ $(( $(date +%s) % 300 )) -eq 0 ]; then
        log "Creating checkpoint..."
        /opt/omni/omni_env/bin/python /opt/omni/omni_immortal_watchdog.py checkpoint
    fi

    sleep $CHECK_INTERVAL
done
