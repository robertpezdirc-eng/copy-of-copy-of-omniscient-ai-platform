#!/bin/bash
set -euxo pipefail

# Install base dependencies
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pip python3-venv git htop unzip curl ca-certificates gnupg lsb-release

# Add gcsfuse apt repository for Ubuntu 22.04 (jammy) and install gcsfuse
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
echo "deb https://packages.cloud.google.com/apt gcsfuse-jammy main" > /etc/apt/sources.list.d/gcsfuse.list
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y gcsfuse

# Mount GCS buckets via gcsfuse
mkdir -p /mnt/omni-assets /mnt/omni-models /mnt/omni-datasets /mnt/omni-logs
umount /mnt/omni-assets || true
umount /mnt/omni-models || true
umount /mnt/omni-datasets || true
umount /mnt/omni-logs || true

# Use instance service account for auth (ADC), scopes already set to cloud-platform
# Mounts will be re-tried on reboot via this startup script
/usr/bin/gcsfuse --implicit-dirs omni-assets-471712-n9 /mnt/omni-assets || true
/usr/bin/gcsfuse --implicit-dirs omni-models-471712-n9 /mnt/omni-models || true
/usr/bin/gcsfuse --implicit-dirs omni-datasets-471712-n9 /mnt/omni-datasets || true
/usr/bin/gcsfuse --implicit-dirs omni-logs-471712-n9 /mnt/omni-logs || true

# Install Cloud Ops Agent for metrics/logs
curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
bash add-google-cloud-ops-agent-repo.sh --also-install