# OMNI Dashboard - Google Cloud Deployment Script (PowerShell)
# This script deploys the OMNI dashboard to Google Cloud

Write-Host "🚀 OMNI DASHBOARD - GOOGLE CLOUD DEPLOYMENT" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

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

# 1. Enable required Google Cloud APIs
Write-Status "Enabling required Google Cloud APIs..."
$apis = @("compute.googleapis.com", "storage.googleapis.com", "monitoring.googleapis.com")
foreach ($api in $apis) {
    Write-Status "Enabling $api..."
    gcloud services enable $api
}

# 2. Create deployment script for the dashboard instance
Write-Status "Creating dashboard deployment script..."

$deployScript = @"
#!/bin/bash
set -e

echo "🚀 Starting OMNI Dashboard Deployment..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y python3 python3-pip python3-venv nodejs npm nginx git curl wget htop

# Install Python dependencies for the dashboard
pip3 install fastapi uvicorn plotly pandas psutil passlib bcrypt jwt requests python-multipart

# Set up directories
sudo mkdir -p /opt/omni-dashboard/{logs,static,templates}
sudo chown -R $(whoami):$(whoami) /opt/omni-dashboard

# Copy dashboard files (assuming they're uploaded)
echo "📁 Dashboard files should be uploaded to /opt/omni-dashboard/"

# Create systemd service for the dashboard
sudo tee /etc/systemd/system/omni-dashboard.service > /dev/null <<EOL
[Unit]
Description=OMNI Dashboard Service
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=/opt/omni-dashboard
ExecStart=/usr/bin/python3 omni_dashboard_professional.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/omni-dashboard

[Install]
WantedBy=multi-user.target
EOL

# Set up Nginx reverse proxy for the dashboard
sudo tee /etc/nginx/sites-available/omni-dashboard > /dev/null <<EOL
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOL

sudo ln -sf /etc/nginx/sites-available/omni-dashboard /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Start services
sudo systemctl daemon-reload
sudo systemctl enable nginx omni-dashboard
sudo systemctl start nginx

echo "✅ OMNI Dashboard deployment completed!"
echo "🌐 Access your dashboard at: http://$(curl -s ifconfig.me)"
echo "🔧 Management commands:"
echo "   sudo systemctl status omni-dashboard"
echo "   sudo systemctl restart omni-dashboard"
echo "   sudo journalctl -u omni-dashboard -f"
"@

Set-Content -Path "omni_dashboard_deploy.sh" -Value $deployScript

# 3. Create a Compute Engine instance for the dashboard
Write-Status "Creating Google Cloud Compute Engine instance..."
$instanceName = "omni-dashboard-instance"
$zone = "us-central1-c"

# Check if instance already exists
$existingInstance = gcloud compute instances describe $instanceName --zone=$zone 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Warning "Instance $instanceName already exists. Deleting and recreating..."
    gcloud compute instances delete $instanceName --zone=$zone --quiet
}

# Create new instance
gcloud compute instances create $instanceName `
    --zone=$zone `
    --machine-type=e2-medium `
    --network-tier=PREMIUM `
    --maintenance-policy=MIGRATE `
    --image=ubuntu-2204-lts `
    --boot-disk-size=50GB `
    --boot-disk-type=pd-standard `
    --boot-disk-device-name=$instanceName `
    --metadata=startup-script-url=gs://cloud-init-scripts/omni-dashboard-startup.sh `
    --tags=omni-dashboard,http-server,https-server

Write-Success "Created Compute Engine instance: $instanceName"

# 4. Upload dashboard files to the instance
Write-Status "Uploading dashboard files to instance..."
gcloud compute scp omni_dashboard_professional.py $instanceName`:/tmp/ --zone=$zone
gcloud compute scp requirements.txt $instanceName`:/tmp/ --zone=$zone 2>$null
gcloud compute scp package.json $instanceName`:/tmp/ --zone=$zone 2>$null

# 5. Execute deployment script on the instance
Write-Status "Executing deployment script on instance..."
gcloud compute scp omni_dashboard_deploy.sh $instanceName`:/tmp/ --zone=$zone
gcloud compute ssh $instanceName --zone=$zone --command="chmod +x /tmp/omni_dashboard_deploy.sh && /tmp/omni_dashboard_deploy.sh"

# 6. Display final status
Write-Status "Final instance status:"
gcloud compute instances list --filter="name:$instanceName" --format="table(name,zone,status,external_ip)"

Write-Success "🎉 OMNI DASHBOARD DEPLOYMENT COMPLETED!"
Write-Host ""
Write-Host "📋 Your dashboard instance:" -ForegroundColor Yellow
$dashboardIP = gcloud compute instances describe $instanceName --zone=$zone --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
Write-Host "   Instance: $instanceName" -ForegroundColor Green
Write-Host "   External IP: $dashboardIP" -ForegroundColor Green
Write-Host "   Zone: $zone" -ForegroundColor Green
Write-Host ""
Write-Host "🔧 Next steps:" -ForegroundColor Yellow
Write-Host "   1. Wait 2-3 minutes for services to start"
Write-Host "   2. Access your dashboard via web browser at http://$dashboardIP"
Write-Host "   3. Check service status: gcloud compute ssh $instanceName --zone=$zone --command='sudo systemctl status omni-dashboard'"
Write-Host ""
Write-Host "💡 Tips:" -ForegroundColor Yellow
Write-Host "   - Monitor costs: gcloud billing accounts projects list"
Write-Host "   - View logs: gcloud compute ssh $instanceName --zone=$zone --command='sudo journalctl -u omni-dashboard -f'"
Write-Host "   - Restart services: gcloud compute ssh $instanceName --zone=$zone --command='sudo systemctl restart omni-dashboard'"