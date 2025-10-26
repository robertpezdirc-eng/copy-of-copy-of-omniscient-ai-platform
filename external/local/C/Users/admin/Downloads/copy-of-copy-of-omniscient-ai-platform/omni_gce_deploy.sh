#!/bin/bash
# OMNI GCE Deployment Script - Immortal Mode
# Deploys dual-instance zero-downtime OMNI platform

set -e

PROJECT_ID="${1:-omni-meta-platform}"
ZONE="${2:-europe-west1-b}"
INSTANCE_NAME="${3:-omni-immortal-instance}"

echo "=== OMNI GCE Immortal Deployment ==="
echo "Project: $PROJECT_ID"
echo "Zone: $ZONE"
echo "Instance: $INSTANCE_NAME"

# Check if instance exists
if gcloud compute instances describe "$INSTANCE_NAME" --zone="$ZONE" --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo "Instance exists - upgrading..."
    UPGRADE=true
else
    echo "Creating new instance..."
    UPGRADE=false
fi

# Create instance with immortal configuration
if [ "$UPGRADE" = false ]; then
    gcloud compute instances create "$INSTANCE_NAME" \
        --zone="$ZONE" \
        --project="$PROJECT_ID" \
        --machine-type=e2-standard-16 \
        --network-tier=PREMIUM \
        --maintenance-policy=MIGRATE \
        --image-family=cos-stable \
        --image-project=cos-cloud \
        --boot-disk-size=200GB \
        --boot-disk-type=pd-standard \
        --boot-disk-device-name="$INSTANCE_NAME" \
        --metadata-from-file startup-script=<(cat <<EOF
#!/bin/bash
# GCE Startup Script for OMNI Immortal Platform

# Install Python and dependencies
apt-get update
apt-get install -y python3 python3-pip python3-venv git

# Create omni user
useradd -m -s /bin/bash omni
usermod -aG sudo omni

# Create directory structure
mkdir -p /opt/omni/releases/{v1,v2}
mkdir -p /opt/omni/checkpoints
mkdir -p /opt/omni/logs
mkdir -p /opt/omni/credentials

# Set ownership
chown -R omni:omni /opt/omni

# Switch to omni user for OMNI installation
su - omni -c "
cd /opt/omni

# Clone or copy OMNI platform files
# This would be your deployment method (git clone, gcs copy, etc.)
echo 'Copy OMNI platform files to /opt/omni/releases/v1/'

# Create Python virtual environment
python3 -m venv /opt/omni/omni_env
source /opt/omni/omni_env/bin/activate

# Install Python dependencies
pip install requests google-cloud-storage

# Set up systemd services
sudo cp /opt/omni/gce_services/omni-autolearn-v1.service /etc/systemd/system/
sudo cp /opt/omni/gce_services/omni-autolearn-v2.service /etc/systemd/system/
sudo cp /opt/omni/gce_services/omni-immortal-watchdog.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start v1 instance
sudo systemctl enable omni-autolearn-v1
sudo systemctl start omni-autolearn-v1

# Enable watchdog
sudo systemctl enable omni-immortal-watchdog
sudo systemctl start omni-immortal-watchdog

# Set up cron job for watchdog script
echo '*/1 * * * * /opt/omni/omni_watchdog.sh' | crontab -

echo 'OMNI Immortal Platform setup complete!'
"
EOF
)
fi

echo "Deployment script generated. Run this script to deploy:"
echo "bash omni_gce_deploy.sh [PROJECT_ID] [ZONE] [INSTANCE_NAME]"
