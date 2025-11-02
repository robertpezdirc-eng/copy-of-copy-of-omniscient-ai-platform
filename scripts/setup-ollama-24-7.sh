#!/bin/bash

# Ollama Service Setup and Monitoring Script
# This script sets up Ollama as a persistent service with auto-restart capabilities

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_MODE="${1:-docker}"  # docker, systemd, or manual

echo "🚀 Ollama 24/7 Service Setup"
echo "============================"
echo "Mode: $INSTALL_MODE"
echo ""

# Function to check if Ollama is running
check_ollama() {
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama is running"
        return 0
    else
        echo "❌ Ollama is not running"
        return 1
    fi
}

# Function to setup Docker-based Ollama
setup_docker() {
    echo "📦 Setting up Ollama with Docker..."
    
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    echo "Starting Ollama service with Docker Compose..."
    docker-compose -f "$SCRIPT_DIR/docker-compose.ollama.yml" up -d
    
    echo "Waiting for Ollama to start..."
    sleep 10
    
    if check_ollama; then
        echo "✅ Ollama Docker service started successfully"
    else
        echo "⚠️  Ollama may still be starting. Check logs with: docker-compose -f docker-compose.ollama.yml logs -f"
    fi
}

# Function to setup systemd-based Ollama
setup_systemd() {
    echo "⚙️  Setting up Ollama with systemd..."
    
    if [ "$EUID" -ne 0 ]; then
        echo "❌ Please run with sudo for systemd installation"
        exit 1
    fi
    
    # Create ollama user if doesn't exist
    if ! id "ollama" &>/dev/null; then
        echo "Creating ollama user..."
        useradd -r -s /bin/false ollama
    fi
    
    # Create data directory
    mkdir -p /var/lib/ollama/models
    chown -R ollama:ollama /var/lib/ollama
    
    # Copy service file
    echo "Installing systemd service..."
    cp "$SCRIPT_DIR/ollama.service" /etc/systemd/system/ollama.service
    
    # Reload systemd and start service
    systemctl daemon-reload
    systemctl enable ollama
    systemctl start ollama
    
    echo "Waiting for Ollama to start..."
    sleep 10
    
    if check_ollama; then
        echo "✅ Ollama systemd service started successfully"
        echo ""
        echo "Useful commands:"
        echo "  sudo systemctl status ollama    # Check status"
        echo "  sudo systemctl restart ollama   # Restart service"
        echo "  sudo journalctl -u ollama -f    # View logs"
    else
        echo "⚠️  Ollama may still be starting. Check status with: sudo systemctl status ollama"
    fi
}

# Function for manual setup
setup_manual() {
    echo "📝 Manual Ollama setup instructions..."
    echo ""
    echo "1. Install Ollama:"
    echo "   curl -fsSL https://ollama.ai/install.sh | sh"
    echo ""
    echo "2. Start Ollama server:"
    echo "   ollama serve"
    echo ""
    echo "3. In another terminal, pull a model:"
    echo "   ollama pull qwen3-coder:30b"
    echo "   # or"
    echo "   ollama pull llama2"
    echo ""
    echo "4. Test the service:"
    echo "   curl http://localhost:11434/api/tags"
    echo ""
}

# Function to install monitoring cron job
setup_monitoring() {
    echo "📊 Setting up health monitoring..."
    
    cat > /tmp/ollama-monitor.sh << 'EOF'
#!/bin/bash
# Ollama Health Monitor - checks every 5 minutes

LOG_FILE="/var/log/ollama-monitor.log"

check_and_restart() {
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "[$(date)] ❌ Ollama health check failed - attempting restart" >> "$LOG_FILE"
        
        # Try to restart based on what's available
        if systemctl is-active --quiet ollama; then
            sudo systemctl restart ollama
            echo "[$(date)] Restarted via systemd" >> "$LOG_FILE"
        elif docker ps | grep -q ollama-service; then
            docker restart ollama-service
            echo "[$(date)] Restarted via docker" >> "$LOG_FILE"
        fi
    else
        echo "[$(date)] ✅ Ollama healthy" >> "$LOG_FILE"
    fi
}

check_and_restart
EOF
    
    chmod +x /tmp/ollama-monitor.sh
    
    echo "To add monitoring cron job, run:"
    echo "  crontab -e"
    echo ""
    echo "Add this line:"
    echo "  */5 * * * * /tmp/ollama-monitor.sh"
    echo ""
}

# Main execution
case "$INSTALL_MODE" in
    docker)
        setup_docker
        ;;
    systemd)
        setup_systemd
        ;;
    manual)
        setup_manual
        ;;
    *)
        echo "Usage: $0 [docker|systemd|manual]"
        echo ""
        echo "Modes:"
        echo "  docker   - Run Ollama in Docker with auto-restart (recommended)"
        echo "  systemd  - Install as systemd service (requires sudo)"
        echo "  manual   - Show manual installation instructions"
        exit 1
        ;;
esac

echo ""
setup_monitoring

echo ""
echo "✅ Ollama 24/7 setup complete!"
echo ""
echo "Next steps:"
echo "1. Pull a model: ollama pull qwen3-coder:30b"
echo "2. Set environment variables:"
echo "   export USE_OLLAMA=true"
echo "   export OLLAMA_URL=http://localhost:11434"
echo "3. Start your backend application"
echo ""
