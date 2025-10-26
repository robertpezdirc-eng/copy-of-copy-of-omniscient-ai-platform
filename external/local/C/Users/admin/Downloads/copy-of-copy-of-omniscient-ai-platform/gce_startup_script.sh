#!/bin/bash
# GCE Startup Script for OMNI Immortal Platform

# Install dependencies
apt-get update
apt-get install -y python3 python3-pip python3-venv git supervisor

# Create omni user
useradd -m -s /bin/bash omni
usermod -aG sudo omni

# Create directory structure
mkdir -p /opt/omni/releases/{v1,v2}
mkdir -p /opt/omni/checkpoints
mkdir -p /opt/omni/logs
mkdir -p /opt/omni/backups

# Set ownership
chown -R omni:omni /opt/omni

# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
echo "source /root/google-cloud-sdk/path.bash.inc" >> ~/.bashrc
echo "source /root/google-cloud-sdk/completion.bash.inc" >> ~/.bashrc

# Switch to omni user for OMNI setup
su - omni << 'EOF'

# Create Python virtual environment
cd /opt/omni
python3 -m venv omni_env
source omni_env/bin/activate

# Install Python dependencies
pip install requests google-cloud-storage

# Create symbolic link for current release
ln -sf /opt/omni/releases/v1 /opt/omni/current

echo "OMNI platform setup complete!"
EOF

# Set up systemd services (as root)
# Copy service files and enable them
# This would be done via deployment script

echo "GCE startup script completed"
