#!/bin/bash

# OMNI Platform MQTT Broker Setup Script
# Sets up Mosquitto MQTT broker with TLS for secure device communications

set -e

echo "🔧 Setting up OMNI MQTT Broker..."

# Install Mosquitto if not present
if ! command -v mosquitto &> /dev/null; then
    echo "📦 Installing Mosquitto MQTT broker..."
    sudo apt update
    sudo apt install -y mosquitto mosquitto-clients
fi

# Create directories
echo "📁 Creating directories..."
sudo mkdir -p /etc/mosquitto/certs
sudo mkdir -p /etc/mosquitto/ca_certificates
sudo mkdir -p /var/lib/mosquitto
sudo mkdir -p /var/log/mosquitto

# Generate CA certificate (self-signed for development)
if [ ! -f /etc/mosquitto/ca_certificates/ca.crt ]; then
    echo "🔐 Generating CA certificate..."
    sudo openssl req -new -x509 -days 365 -extensions v3_ca -keyout /etc/mosquitto/ca_certificates/ca.key -out /etc/mosquitto/ca_certificates/ca.crt -subj "/C=SI/ST=Ljubljana/L=Ljubljana/O=OMNI/CN=OMNI-CA"
fi

# Generate server certificate
if [ ! -f /etc/mosquitto/certs/server.crt ]; then
    echo "🔐 Generating server certificate..."
    sudo openssl genrsa -out /etc/mosquitto/certs/server.key 2048
    sudo openssl req -out /etc/mosquitto/certs/server.csr -key /etc/mosquitto/certs/server.key -new -subj "/C=SI/ST=Ljubljana/L=Ljubljana/O=OMNI/CN=localhost"
    sudo openssl x509 -req -in /etc/mosquitto/certs/server.csr -CA /etc/mosquitto/ca_certificates/ca.crt -CAkey /etc/mosquitto/ca_certificates/ca.key -CAcreateserial -out /etc/mosquitto/certs/server.crt -days 365
fi

# Set proper permissions
sudo chmod 600 /etc/mosquitto/certs/server.key
sudo chmod 644 /etc/mosquitto/certs/server.crt
sudo chmod 644 /etc/mosquitto/ca_certificates/ca.crt

# Copy configuration files
echo "📋 Installing configuration files..."
sudo cp mosquitto.conf /etc/mosquitto/mosquitto.conf
sudo cp mosquitto_acl.conf /etc/mosquitto/acl

# Create password file for authentication
if [ ! -f /etc/mosquitto/passwd ]; then
    echo "🔑 Setting up default users..."

    # Create password file
    sudo touch /etc/mosquitto/passwd
    sudo chown mosquitto:mosquitto /etc/mosquitto/passwd

    # Add default users (these should be changed in production)
    sudo mosquitto_passwd -b /etc/mosquitto/passwd omni_gateway secure_gateway_password
    sudo mosquitto_passwd -b /etc/mosquitto/passwd omni_admin admin_secure_password

    # Set proper permissions
    sudo chmod 600 /etc/mosquitto/passwd
fi

# Set ownership for Mosquitto directories
sudo chown -R mosquitto:mosquitto /var/lib/mosquitto
sudo chown -R mosquitto:mosquitto /var/log/mosquitto

# Enable and start Mosquitto service
echo "🚀 Starting MQTT broker service..."
sudo systemctl enable mosquitto
sudo systemctl restart mosquitto

# Wait for service to start
sleep 3

# Test MQTT broker
echo "🧪 Testing MQTT broker..."
if mosquitto_sub -h localhost -t "test" -C 1 -W 5; then
    echo "✅ MQTT broker is working correctly"
else
    echo "⚠️ MQTT broker test failed, but continuing setup"
fi

# Create systemd service for OMNI Gateway
cat > omni-mqtt-gateway.service << EOF
[Unit]
Description=OMNI MQTT Gateway Service
After=network.target mosquitto.service
Requires=mosquitto.service

[Service]
Type=simple
User=omni
Group=omni
WorkingDirectory=/opt/omni-platform
ExecStart=/usr/bin/python3 /opt/omni-platform/omni_gateway.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=PYTHONPATH=/opt/omni-platform

[Install]
WantedBy=multi-user.target
EOF

# Install service file
sudo cp omni-mqtt-gateway.service /etc/systemd/system/
sudo systemctl daemon-reload

echo "✅ OMNI MQTT Broker setup completed!"
echo ""
echo "📋 MQTT Broker Information:"
echo "   Host: localhost"
echo "   MQTT Port: 1883"
echo "   MQTT TLS Port: 8883"
echo "   WebSocket Port: 9001"
echo "   Configuration: /etc/mosquitto/mosquitto.conf"
echo ""
echo "🔧 Management Commands:"
echo "   sudo systemctl status mosquitto"
echo "   sudo systemctl restart mosquitto"
echo "   sudo systemctl status omni-mqtt-gateway"
echo "   sudo systemctl restart omni-mqtt-gateway"
echo ""
echo "🔒 Security Notes:"
echo "   - Change default passwords in /etc/mosquitto/passwd"
echo "   - Use proper certificates in production"
echo "   - Configure firewall rules for MQTT ports"
echo "   - Enable TLS for production deployments"