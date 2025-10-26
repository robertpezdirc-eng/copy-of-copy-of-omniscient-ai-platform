#!/bin/bash

# OMNI Platform Device Certificate Generator
# Generates client certificates for secure MQTT device connections

set -e

# Configuration
CA_CERT="/etc/mosquitto/ca_certificates/ca.crt"
CA_KEY="/etc/mosquitto/ca_certificates/ca.key"
CERT_DIR="/etc/mosquitto/client_certs"
CLIENT_CERT_DAYS=365

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔐 OMNI Device Certificate Generator${NC}"
echo "=================================="

# Check if CA exists
if [ ! -f "$CA_CERT" ] || [ ! -f "$CA_KEY" ]; then
    echo -e "${RED}❌ CA certificate not found. Please run setup_mqtt_broker.sh first.${NC}"
    exit 1
fi

# Create client certificates directory
sudo mkdir -p "$CERT_DIR"

# Function to generate client certificate
generate_client_cert() {
    local device_id="$1"
    local device_type="$2"

    echo -e "${YELLOW}📱 Generating certificate for device: $device_id${NC}"

    local cert_file="$CERT_DIR/${device_id}.crt"
    local key_file="$CERT_DIR/${device_id}.key"
    local csr_file="$CERT_DIR/${device_id}.csr"

    # Generate private key
    sudo openssl genrsa -out "$key_file" 2048

    # Generate certificate signing request
    sudo openssl req -out "$csr_file" -key "$key_file" -new \
        -subj "/C=SI/ST=Ljubljana/L=Ljubljana/O=OMNI/CN=${device_id}"

    # Sign certificate with CA
    sudo openssl x509 -req -in "$csr_file" \
        -CA "$CA_CERT" \
        -CAkey "$CA_KEY" \
        -CAcreateserial \
        -out "$cert_file" \
        -days "$CLIENT_CERT_DAYS"

    # Set proper permissions
    sudo chmod 600 "$key_file"
    sudo chmod 644 "$cert_file"

    # Clean up CSR file
    sudo rm "$csr_file"

    echo -e "${GREEN}✅ Certificate generated for device: $device_id${NC}"
    echo "   Certificate: $cert_file"
    echo "   Private Key: $key_file"
    echo ""
}

# Function to create device password entry
create_device_password() {
    local device_id="$1"
    local password="$2"

    if [ -f "/etc/mosquitto/passwd" ]; then
        sudo mosquitto_passwd -b /etc/mosquitto/passwd "$device_id" "$password"
        echo -e "${GREEN}✅ Password set for device: $device_id${NC}"
    else
        echo -e "${RED}❌ Password file not found${NC}"
    fi
}

# Generate certificates for different device types
echo -e "${YELLOW}🔧 Generating certificates for device types...${NC}"

# VR Devices
generate_client_cert "vr_device_oculus_001" "vr_glasses"
generate_client_cert "vr_device_vive_001" "vr_glasses"
generate_client_cert "vr_device_mobile_001" "mobile_vr"

# IoT Devices
generate_client_cert "iot_sensor_temp_001" "iot_sensor"
generate_client_cert "iot_actuator_relay_001" "iot_actuator"
generate_client_cert "iot_device_raspberry_001" "iot_device"

# Camera Devices
generate_client_cert "camera_security_001" "security_camera"
generate_client_cert "camera_streaming_001" "streaming_camera"

# Car Devices
generate_client_cert "car_obd_001" "car_obd"
generate_client_cert "car_diagnostics_001" "car_diagnostics"

# Smart Devices
generate_client_cert "smart_light_001" "smart_light"
generate_client_cert "smart_thermostat_001" "smart_thermostat"

echo -e "${GREEN}✅ All device certificates generated!${NC}"
echo ""
echo -e "${YELLOW}📋 Certificate Information:${NC}"
echo "   CA Certificate: $CA_CERT"
echo "   Client Certificates: $CERT_DIR/"
echo "   MQTT TLS Port: 8883"
echo "   MQTT WebSocket TLS Port: 9001"
echo ""

# Create device configuration templates
echo -e "${YELLOW}📝 Creating device configuration templates...${NC}"

cat > device_config_template.json << EOF
{
  "device_id": "DEVICE_ID",
  "device_type": "DEVICE_TYPE",
  "omni_gateway": {
    "mqtt": {
      "host": "localhost",
      "port": 8883,
      "tls": true,
      "ca_cert": "/path/to/ca.crt",
      "client_cert": "/path/to/device.crt",
      "client_key": "/path/to/device.key"
    },
    "websocket": {
      "url": "wss://localhost:9001",
      "tls": true
    },
    "http": {
      "url": "https://localhost:3090",
      "api_key": "YOUR_API_KEY"
    }
  },
  "telemetry": {
    "enabled": true,
    "interval": 30,
    "topics": [
      "omni/telemetry/DEVICE_ID"
    ]
  },
  "commands": {
    "subscribe_topics": [
      "omni/commands/DEVICE_ID"
    ]
  }
}
EOF

echo -e "${GREEN}✅ Device configuration template created: device_config_template.json${NC}"
echo ""
echo -e "${YELLOW}🔧 Next Steps:${NC}"
echo "1. Copy certificates to devices"
echo "2. Update device configurations with actual paths"
echo "3. Set up firewall rules for MQTT ports (1883, 8883, 9001)"
echo "4. Configure reverse proxy for external access"
echo "5. Test device connections"
echo ""
echo -e "${GREEN}🎉 Device certificate generation completed!${NC}"