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
sudo chown -R pwn1sss03\admin:pwn1sss03\admin /opt/omni-dashboard

# Copy dashboard files (assuming they're uploaded)
echo "📁 Dashboard files should be uploaded to /opt/omni-dashboard/"

# Create systemd service for the dashboard
sudo tee /etc/systemd/system/omni-dashboard.service > /dev/null <<EOL
[Unit]
Description=OMNI Dashboard Service
After=network.target

[Service]
Type=simple
User=pwn1sss03\admin
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
        proxy_set_header Host System.Management.Automation.Internal.Host.InternalHost;
        proxy_set_header X-Real-IP ;
        proxy_set_header X-Forwarded-For ;
        proxy_set_header X-Forwarded-Proto ;
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
echo "🌐 Access your dashboard at: http://"
echo "🔧 Management commands:"
echo "   sudo systemctl status omni-dashboard"
echo "   sudo systemctl restart omni-dashboard"
echo "   sudo journalctl -u omni-dashboard -f"
