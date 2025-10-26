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
sudo chown -R pwn1sss03\admin:pwn1sss03\admin /opt/omni

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
User=pwn1sss03\admin
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
        proxy_set_header Host System.Management.Automation.Internal.Host.InternalHost;
        proxy_set_header X-Real-IP ;
        proxy_set_header X-Forwarded-For ;
        proxy_set_header X-Forwarded-Proto ;
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
echo "🌐 Access your platform at: http://"
echo "🔧 Management commands:"
echo "   sudo systemctl status omni-platform"
echo "   sudo systemctl restart omni-platform"
echo "   sudo journalctl -u omni-platform -f"
