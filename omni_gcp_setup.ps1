# OMNI PLATFORM - COMPLETE GOOGLE CLOUD SETUP SCRIPT (PowerShell)
# This script sets up the complete Omni platform on Google Cloud

Write-Host "🚀 OMNI PLATFORM - COMPLETE GOOGLE CLOUD SETUP" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# 1. Check if SSH key exists, create if needed
Write-Status "Setting up SSH keys..."
$sshKeyPath = "$env:USERPROFILE\.ssh\id_rsa"
if (!(Test-Path $sshKeyPath)) {
    Write-Status "Generating new SSH key..."
    ssh-keygen -t rsa -f $sshKeyPath -N '""'
    Write-Success "Generated new SSH key"
} else {
    Write-Status "Using existing SSH key"
}

# 2. Add SSH key to project metadata
Write-Status "Adding SSH key to Google Cloud project..."
$publicKey = Get-Content "$env:USERPROFILE\.ssh\id_rsa.pub" -Raw
$metadata = "ssh-keys=$(whoami):$publicKey"
gcloud compute project-info add-metadata --metadata $metadata

# 3. Create deployment script for instances
Write-Status "Creating deployment script..."

$deployScript = @"
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

# Set up directories
sudo mkdir -p /opt/omni/{models,data,logs,backups}
sudo chown -R $(whoami):$(whoami) /opt/omni

# Configure environment
export OMNI_HOME=/opt/omni
export PYTHONPATH=/opt/omni

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
sudo systemctl enable nginx redis-server mongodb omni-platform
sudo systemctl start nginx redis-server mongodb

echo "✅ Omni Platform deployment completed!"
echo "🌐 Access your platform at: http://$(curl -s ifconfig.me)"
echo "🔧 Management commands:"
echo "   sudo systemctl status omni-platform"
echo "   sudo systemctl restart omni-platform"
echo "   sudo journalctl -u omni-platform -f"
"@

Set-Content -Path "omni_deploy.sh" -Value $deployScript

# 4. Deploy to instances
Write-Status "Deploying to omni-cpu-optimized instance..."
gcloud compute scp omni_deploy.sh omni-cpu-optimized:/tmp/ --zone=us-central1-c
gcloud compute ssh omni-cpu-optimized --zone=us-central1-c --command="chmod +x /tmp/omni_deploy.sh && /tmp/omni_deploy.sh"

Write-Status "Deploying to omni-storage-node instance..."
gcloud compute scp omni_deploy.sh omni-storage-node:/tmp/ --zone=us-central1-c
gcloud compute ssh omni-storage-node --zone=us-central1-c --command="chmod +x /tmp/omni_deploy.sh && /tmp/omni_deploy.sh"

# 5. Copy Omni platform files to instances
Write-Status "Copying Omni platform files..."
gcloud compute scp requirements.txt omni-cpu-optimized:/tmp/ --zone=us-central1-c
gcloud compute scp requirements-gpu.txt omni-cpu-optimized:/tmp/ --zone=us-central1-c
gcloud compute scp package.json omni-cpu-optimized:/tmp/ --zone=us-central1-c

# 6. Display final status
Write-Status "Final instance status:"
gcloud compute instances list --format="table(name,zone,status,external_ip)"

Write-Success "🎉 OMNI PLATFORM SETUP COMPLETED!"
Write-Host ""
Write-Host "📋 Your instances:" -ForegroundColor Yellow
$cpuIP = gcloud compute instances describe omni-cpu-optimized --zone=us-central1-c --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
$storageIP = gcloud compute instances describe omni-storage-node --zone=us-central1-c --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
Write-Host "   omni-cpu-optimized: $cpuIP" -ForegroundColor Green
Write-Host "   omni-storage-node: $storageIP" -ForegroundColor Green
Write-Host ""
Write-Host "🔧 Next steps:" -ForegroundColor Yellow
Write-Host "   1. Wait 2-3 minutes for services to start"
Write-Host "   2. Access your platform via web browser at http://$cpuIP"
Write-Host "   3. Check service status: gcloud compute ssh omni-cpu-optimized --zone=us-central1-c --command='sudo systemctl status omni-platform'"
Write-Host ""
Write-Host "💡 Tips:" -ForegroundColor Yellow
Write-Host "   - Monitor costs: gcloud billing accounts projects list"
Write-Host "   - View logs: gcloud compute ssh omni-cpu-optimized --zone=us-central1-c --command='sudo journalctl -u omni-platform -f'"
Write-Host "   - Restart services: gcloud compute ssh omni-cpu-optimized --zone=us-central1-c --command='sudo systemctl restart omni-platform'"