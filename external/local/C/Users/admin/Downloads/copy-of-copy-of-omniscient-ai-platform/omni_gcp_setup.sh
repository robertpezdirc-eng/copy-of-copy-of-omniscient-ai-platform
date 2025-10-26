#!/bin/bash

# OMNI PLATFORM - COMPLETE GOOGLE CLOUD SETUP SCRIPT
# This script sets up the complete Omni platform on Google Cloud

set -e

echo "🚀 OMNI PLATFORM - COMPLETE GOOGLE CLOUD SETUP"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. Generate SSH key if it doesn't exist
print_status "Setting up SSH keys..."
if [ ! -f ~/.ssh/id_rsa ]; then
    ssh-keygen -t rsa -f ~/.ssh/id_rsa -N ""
    print_success "Generated new SSH key"
else
    print_status "Using existing SSH key"
fi

# 2. Add SSH key to project metadata
print_status "Adding SSH key to Google Cloud project..."
PUBLIC_KEY=$(cat ~/.ssh/id_rsa.pub)
gcloud compute project-info add-metadata --metadata "ssh-keys=$(whoami):$PUBLIC_KEY"

# 3. Create deployment script for instances
print_status "Creating deployment script..."

cat > omni_deploy.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting Omni Platform Deployment..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y python3 python3-pip python3-venv nodejs npm nginx redis-server mongodb git curl wget htop

# Install Python dependencies
pip3 install -r requirements.txt
pip3 install -r requirements-gpu.txt

# Install Node.js dependencies
npm install

# Set up Python virtual environment
python3 -m venv omni_env
source omni_env/bin/activate

# Clone Omni platform if not exists
if [ ! -d "omni-platform" ]; then
    git clone https://github.com/your-repo/omni-platform.git
fi

cd omni-platform

# Sync repository before each run
git pull origin main

# Install additional AI/ML packages
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install transformers diffusers accelerate

# Set up directories
sudo mkdir -p /opt/omni/{models,data,logs,backups}
sudo chown -R $(whoami):$(whoami) /opt/omni

# Configure environment
export OMNI_HOME=/opt/omni
export PYTHONPATH=$OMNI_HOME:$PYTHONPATH

# Set up systemd services
sudo tee /etc/systemd/system/omni-platform.service > /dev/null <<EOL
[Unit]
Description=Omni Platform Main Service
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=/opt/omni
ExecStart=/opt/omni/omni_env/bin/python main.py
Restart=always
RestartSec=10
Environment=OMNI_HOME=/opt/omni
Environment=PYTHONPATH=/opt/omni

[Install]
WantedBy=multi-user.target
EOL

# Auto-learning worker service
sudo tee /etc/systemd/system/omni-autolearn.service > /dev/null <<EOL
[Unit]
Description=Omni Auto-Learning Service
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=/opt/omni
ExecStart=/opt/omni/omni_env/bin/python omni_autolearn_starter.py
Restart=always
RestartSec=10
Environment=OMNI_HOME=/opt/omni
Environment=PYTHONPATH=/opt/omni

[Install]
WantedBy=multi-user.target
EOL

# Set up Nginx reverse proxy
sudo tee /etc/nginx/sites-available/omni-platform > /dev/null <<EOL
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOL

sudo ln -sf /etc/nginx/sites-available/omni-platform /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Start services
sudo systemctl daemon-reload
sudo systemctl enable nginx redis-server mongodb omni-platform omni-autolearn
sudo systemctl start nginx redis-server mongodb omni-autolearn

echo "✅ Omni Platform deployment completed!"
echo "🌐 Access your platform at: http://$(curl -s ifconfig.me)"
echo "🔧 Management commands:"
echo "   sudo systemctl status omni-platform"
echo "   sudo systemctl restart omni-platform"
echo "   sudo journalctl -u omni-platform -f"
EOF

chmod +x omni_deploy.sh

# 4. Deploy to instances
print_status "Deploying to omni-cpu-optimized instance..."
gcloud compute scp omni_deploy.sh omni-cpu-optimized:/tmp/ --zone=us-central1-c
gcloud compute ssh omni-cpu-optimized --zone=us-central1-c --command="chmod +x /tmp/omni_deploy.sh && /tmp/omni_deploy.sh"

print_status "Deploying to omni-storage-node instance..."
gcloud compute scp omni_deploy.sh omni-storage-node:/tmp/ --zone=us-central1-c
gcloud compute ssh omni-storage-node --zone=us-central1-c --command="chmod +x /tmp/omni_deploy.sh && /tmp/omni_deploy.sh"

# 5. Copy Omni platform files to instances
print_status "Copying Omni platform files..."
gcloud compute scp requirements.txt omni-cpu-optimized:/tmp/ --zone=us-central1-c
gcloud compute scp requirements-gpu.txt omni-cpu-optimized:/tmp/ --zone=us-central1-c
gcloud compute scp package.json omni-cpu-optimized:/tmp/ --zone=us-central1-c

# 6. Create startup script for instances
print_status "Creating startup scripts..."

cat > startup_script.sh << 'EOF'
#!/bin/bash

# Resize disk if needed
if [ -b /dev/sdb ]; then
    sudo resize2fs /dev/sdb
fi

# Mount additional storage
sudo mkdir -p /mnt/omni-data
echo '/dev/sdb /mnt/omni-data ext4 defaults 0 0' | sudo tee -a /etc/fstab

# Set up cron jobs for monitoring
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/bin/python /opt/omni/monitor.py") | crontab -

echo "Startup script completed"
EOF

gcloud compute scp startup_script.sh omni-cpu-optimized:/tmp/ --zone=us-central1-c
gcloud compute scp startup_script.sh omni-storage-node:/tmp/ --zone=us-central1-c

# 7. Display final status
print_status "Final instance status:"
gcloud compute instances list --format="table(name,zone,status,external_ip)"

print_success "🎉 OMNI PLATFORM SETUP COMPLETED!"
echo ""
echo "📋 Your instances:"
echo "   omni-cpu-optimized: $(gcloud compute instances describe omni-cpu-optimized --zone=us-central1-c --format='get(networkInterfaces[0].accessConfigs[0].natIP')"
echo "   omni-storage-node: $(gcloud compute instances describe omni-storage-node --zone=us-central1-c --format='get(networkInterfaces[0].accessConfigs[0].natIP')"
echo ""
echo "🔧 Next steps:"
echo "   1. Wait 2-3 minutes for services to start"
echo "   2. Access your platform via web browser"
echo "   3. Check service status: gcloud compute ssh omni-cpu-optimized --zone=us-central1-c --command='sudo systemctl status omni-platform'"
echo ""
echo "💡 Tips:"
echo "   - Monitor costs: gcloud billing accounts projects list"
echo "   - View logs: gcloud compute ssh omni-cpu-optimized --zone=us-central1-c --command='sudo journalctl -u omni-platform -f'"
echo "   - Restart services: gcloud compute ssh omni-cpu-optimized --zone=us-central1-c --command='sudo systemctl restart omni-platform'"