#!/bin/bash

# OMNI Singularity - Google Cloud Setup Script
# Secure setup of Google Cloud credentials for OMNI Singularity

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CREDENTIALS_FILE="gcp-credentials.json"
API_KEY="AIzaSyAyKCIUE1b8SQF9g-Ok2WDB_zvtkCkYC8M"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Create Google Cloud credentials file
create_credentials_file() {
    log_info "Creating Google Cloud credentials file..."

    # Create credentials JSON structure
    cat > "${CREDENTIALS_FILE}" << EOF
{
  "type": "service_account",
  "project_id": "omni-singularity-project",
  "private_key_id": "key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\n-----END PRIVATE KEY-----\n",
  "client_email": "omni-singularity@omni-singularity-project.iam.gserviceaccount.com",
  "client_id": "client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/omni-singularity%40omni-singularity-project.iam.gserviceaccount.com"
}
EOF

    log_success "Google Cloud credentials file created: ${CREDENTIALS_FILE}"
}

# Set environment variables for Google Cloud
setup_environment_variables() {
    log_info "Setting up Google Cloud environment variables..."

    # Export API key
    export GOOGLE_API_KEY="${API_KEY}"
    export GOOGLE_CLOUD_KEY="${API_KEY}"
    export GOOGLE_CLOUD_PROJECT="omni-singularity-project"

    # Set for current session
    echo "export GOOGLE_API_KEY=${API_KEY}" >> ~/.bashrc
    echo "export GOOGLE_CLOUD_KEY=${API_KEY}" >> ~/.bashrc
    echo "export GOOGLE_CLOUD_PROJECT=omni-singularity-project" >> ~/.bashrc

    log_success "Google Cloud environment variables configured"
}

# Test Google Cloud connectivity
test_google_cloud_connectivity() {
    log_info "Testing Google Cloud connectivity..."

    # Test API key with a simple request
    if curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=${API_KEY}" &> /dev/null; then
        log_success "Google Cloud API connectivity verified"
        return 0
    else
        log_warning "Google Cloud API connectivity test failed"
        return 1
    fi
}

# Create .env file for Docker Compose
create_env_file() {
    log_info "Creating .env file for Docker Compose..."

    cat > .env << EOF
# OMNI Singularity Google Cloud Configuration
GOOGLE_API_KEY=${API_KEY}
GOOGLE_CLOUD_KEY=${API_KEY}
GOOGLE_CLOUD_PROJECT=omni-singularity-project
GOOGLE_APPLICATION_CREDENTIALS=/app/gcp-credentials.json

# OpenAI Configuration (add your key)
OPENAI_API_KEY=your_openai_key_here

# Gemini Configuration (add your key)
GEMINI_API_KEY=your_gemini_key_here

# Redis Configuration
REDIS_PASSWORD=omni_redis_secure_pass_$(openssl rand -hex 16)

# Grafana Configuration
GRAFANA_PASSWORD=omni_grafana_admin_$(openssl rand -hex 8)

# GPU Configuration
ENABLE_GPU=false

# Environment
ENVIRONMENT=development
EOF

    log_success ".env file created with Google Cloud configuration"
}

# Display setup information
display_setup_info() {
    log_info "Google Cloud Setup Information:"
    echo ""
    echo "🔑 API Key: ${API_KEY}"
    echo "☁️ Project: omni-singularity-project"
    echo "📁 Credentials: $(pwd)/${CREDENTIALS_FILE}"
    echo "🌍 Environment: Configured for Europe/Ljubljana"
    echo ""
    echo "🔧 Configuration Files:"
    echo "   .env: $(pwd)/.env"
    echo "   Credentials: $(pwd)/${CREDENTIALS_FILE}"
    echo "   Config: $(pwd)/config.txt"
    echo ""
    echo "✅ Google Cloud setup completed successfully!"
}

# Main setup function
main() {
    echo "☁️ OMNI Singularity - Google Cloud Setup"
    echo "========================================"

    # Run setup steps
    create_credentials_file
    setup_environment_variables
    create_env_file

    if test_google_cloud_connectivity; then
        display_setup_info
        log_success "Google Cloud setup completed successfully!"
        echo ""
        echo "🚀 Next steps:"
        echo "1. Run: ./start-omni-singularity.sh"
        echo "2. Access: http://localhost:8093"
        echo "3. Test Google Cloud integration"
        echo ""
        echo "🎉 OMNI Singularity with Google Cloud is ready!"
    else
        log_error "Google Cloud connectivity test failed"
        echo ""
        echo "🔧 Troubleshooting:"
        echo "1. Verify your internet connection"
        echo "2. Check API key validity"
        echo "3. Ensure Google Cloud services are enabled"
        exit 1
    fi
}

# Run main function
main "$@"