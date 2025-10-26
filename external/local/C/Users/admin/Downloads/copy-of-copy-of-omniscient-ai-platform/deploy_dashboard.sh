#!/bin/bash

# OMNI Platform Professional Dashboard Deployment Script
echo "🚀 OMNI Platform Professional Dashboard Deployment"
echo "================================================"

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

# 1. Check requirements
print_status "Checking system requirements..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Please install pip3."
    exit 1
fi

# Check if Docker is available (optional)
if command -v docker &> /dev/null; then
    print_success "Docker is available for containerized deployment"
    DOCKER_AVAILABLE=true
else
    print_warning "Docker not available. Will use direct Python deployment."
    DOCKER_AVAILABLE=false
fi

print_success "System requirements check completed"

# 2. Create necessary directories
print_status "Creating necessary directories..."
mkdir -p omni_platform/static
mkdir -p omni_platform/templates
mkdir -p omni_platform/logs
mkdir -p grafana/dashboards
mkdir -p grafana/datasources
print_success "Directories created"

# 3. Install Python dependencies
print_status "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
    print_success "Python dependencies installed"
else
    print_warning "requirements.txt not found. Installing basic dependencies..."
    pip3 install fastapi uvicorn plotly pandas psutil python-multipart python-jose[cryptography] passlib[bcrypt]
fi

# 4. Install Google Cloud dependencies if credentials exist
if [ -f "gcp-credentials.json" ]; then
    print_status "Installing Google Cloud dependencies..."
    pip3 install google-cloud-storage google-cloud-monitoring google-cloud-pubsub google-cloud-aiplatform
    print_success "Google Cloud dependencies installed"
else
    print_warning "GCP credentials not found. Google Cloud integration will be limited."
fi

# 5. Create sample GCP credentials template
if [ ! -f "gcp-credentials.json" ]; then
    print_status "Creating GCP credentials template..."
    cat > gcp-credentials.json << 'EOF'
{
  "type": "service_account",
  "project_id": "your-gcp-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
}
EOF
    print_warning "Created GCP credentials template. Please update with your actual credentials."
fi

# 6. Set environment variables
print_status "Setting up environment..."
export GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT:-"omni-platform-2024"}
export OMNI_ENV=${OMNI_ENV:-"production"}

# 7. Create systemd service file
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/omni-dashboard.service > /dev/null << EOF
[Unit]
Description=OMNI Platform Professional Dashboard
After=network.target
Wants=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(pwd)
Environment=GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}
Environment=OMNI_ENV=${OMNI_ENV}
ExecStart=$(which python3) omni_dashboard_professional.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 8. Create log rotation
print_status "Setting up log rotation..."
sudo tee /etc/logrotate.d/omni-dashboard > /dev/null << EOF
$(pwd)/omni_platform/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 $(whoami) $(whoami)
}
EOF

# 9. Enable and start service
print_status "Enabling and starting OMNI dashboard service..."
sudo systemctl daemon-reload
sudo systemctl enable omni-dashboard.service
sudo systemctl start omni-dashboard.service

# 10. Wait for service to start
print_status "Waiting for dashboard to start..."
sleep 5

# 11. Check service status
if sudo systemctl is-active --quiet omni-dashboard; then
    print_success "OMNI Dashboard service is running"

    # Get the IP address
    IP_ADDRESS=$(hostname -I | awk '{print $1}')

    echo ""
    echo "🎉 OMNI Platform Professional Dashboard is now running!"
    echo "================================================"
    echo "🌐 Dashboard: http://${IP_ADDRESS}:8080"
    echo "🔐 Login: http://${IP_ADDRESS}:8080/login"
    echo "💡 Health Check: http://${IP_ADDRESS}:8080/api/health"
    echo "📚 API Documentation: http://${IP_ADDRESS}:8080/api/docs"
    echo ""
    echo "🔑 Default Login Credentials:"
    echo "   Username: admin"
    echo "   Password: omni_admin_2024"
    echo ""
    echo "📊 Monitoring Commands:"
    echo "   sudo systemctl status omni-dashboard"
    echo "   sudo systemctl restart omni-dashboard"
    echo "   sudo journalctl -u omni-dashboard -f"
    echo "   sudo tail -f omni_platform/logs/omni_dashboard.log"
    echo ""
    echo "☁️ Google Cloud Integration:"
    echo "   - Update gcp-credentials.json with your service account key"
    echo "   - Set GOOGLE_CLOUD_PROJECT environment variable"
    echo "   - Restart service to apply changes"
    echo ""

else
    print_error "Failed to start OMNI Dashboard service"
    echo ""
    echo "🔍 Troubleshooting:"
    echo "   sudo systemctl status omni-dashboard"
    echo "   sudo journalctl -u omni-dashboard --no-pager -l"
    echo ""
    exit 1
fi

# 12. Optional: Start monitoring stack with Docker
if [ "$DOCKER_AVAILABLE" = true ] && [ "$1" = "--with-docker" ]; then
    print_status "Starting monitoring stack with Docker..."

    # Start Prometheus and Grafana
    docker-compose up -d prometheus grafana

    if [ $? -eq 0 ]; then
        print_success "Monitoring stack started"
        echo "📊 Grafana: http://${IP_ADDRESS}:3000 (admin/omni_admin_2024)"
        echo "📈 Prometheus: http://${IP_ADDRESS}:9090"
    else
        print_warning "Failed to start monitoring stack"
    fi
fi

print_success "OMNI Platform Professional Dashboard deployment completed!"