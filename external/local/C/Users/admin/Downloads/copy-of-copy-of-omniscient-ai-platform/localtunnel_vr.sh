#!/bin/bash

# LocalTunnel VR Gateway Setup Script
# Provides HTTPS tunneling for VR glasses compatibility during development

set -e

echo "🚀 Setting up LocalTunnel for VR Gateway..."
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Check if LocalTunnel is installed
if ! command -v lt &> /dev/null; then
    print_status "Installing LocalTunnel..."
    npm install -g localtunnel
fi

# Default configuration
PORT=${1:-8080}
SUBDOMAIN=${2:-"omni-vr-$(date +%s)"}
VR_CONFIG_FILE="vr_gateway.json"

print_status "Starting LocalTunnel for VR Gateway..."
print_status "Port: $PORT"
print_status "Subdomain: $subdomain"
print_status "VR Config: $VR_CONFIG_FILE"

# Check if VR config exists
if [ ! -f "$VR_CONFIG_FILE" ]; then
    print_warning "VR config file not found. Creating default config..."
    cat > "$VR_CONFIG_FILE" << 'EOF'
{
  "vr_config": {
    "version": "1.0.0",
    "name": "Omni VR Gateway - LocalTunnel",
    "description": "Local development VR gateway with HTTPS tunneling",
    "enabled": true,
    "localtunnel": true,
    "https_enforced": true
  },
  "tunnel": {
    "provider": "localtunnel",
    "auto_start": true,
    "restart_on_failure": true
  }
}
EOF
    print_success "Created default VR config file"
fi

# Start LocalTunnel
print_status "Starting HTTPS tunnel for VR glasses..."
print_status "This will provide a secure HTTPS URL for VR devices"
echo ""
print_warning "Make sure your local server is running on port $PORT"
echo ""

# Start LocalTunnel in background
lt --port $PORT --subdomain $SUBDOMAIN &
TUNNEL_PID=$!

print_success "LocalTunnel started with PID: $TUNNEL_PID"
print_success "Your HTTPS URL for VR glasses: https://$SUBDOMAIN.loca.lt"

# Wait for tunnel to be ready
sleep 3

# Display connection info
echo ""
echo "🌐 VR Gateway Information:"
echo "=========================="
echo "HTTPS URL: https://$SUBDOMAIN.loca.lt"
echo "Local Port: $PORT"
echo "Process ID: $TUNNEL_PID"
echo ""
echo "📱 For VR Glasses:"
echo "   - Open Oculus Browser on Quest"
echo "   - Navigate to: https://$SUBDOMAIN.loca.lt/vr/trampoline"
echo "   - Click 'Enter VR' button"
echo ""
echo "💡 Tips:"
echo "   - Keep this terminal window open"
echo "   - Use Ctrl+C to stop the tunnel"
echo "   - Restart if connection drops"
echo ""

# Monitor the tunnel process
wait $TUNNEL_PID