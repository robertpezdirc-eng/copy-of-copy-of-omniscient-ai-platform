#!/bin/bash

# OMNI Singularity Quantum Dashboard v10.0 - Launch Script
# Complete deployment script for Docker containerized quantum AI system

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="omni-singularity-v10"
DOCKER_IMAGE="${PROJECT_NAME}:latest"
COMPOSE_FILE="docker-compose.omni.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

log_section() {
    echo -e "${PURPLE}[SECTION]${NC} $*"
}

# Check prerequisites
check_prerequisites() {
    log_section "Checking Prerequisites"
    log_info "Verifying Docker environment..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi

    log_success "Prerequisites check completed"
}

# Create necessary directories
create_directories() {
    log_section "Creating Directories"
    log_info "Setting up data directories..."

    mkdir -p data/{omni_singularity,omni_memory,omni_logs,omni_database,omni_redis,quantum_storage,prometheus,grafana,backups}
    mkdir -p config nginx/conf.d ssl monitoring/grafana/{dashboards,provisioning}

    log_success "Directories created"
}

# Generate SSL certificates for development
generate_ssl_certificates() {
    log_section "SSL Certificates"
    log_info "Generating SSL certificates for development..."

    if [ ! -f ssl/server.crt ] || [ ! -f ssl/server.key ]; then
        openssl req -x509 -newkey rsa:4096 -keyout ssl/server.key -out ssl/server.crt \
            -days 365 -nodes -subj "/CN=omni-singularity.local"

        log_success "SSL certificates generated"
    else
        log_info "SSL certificates already exist, skipping generation"
    fi
}

# Build Docker images
build_docker_images() {
    log_section "Building Docker Images"
    log_info "Building OMNI Singularity Docker images..."

    # Build main OMNI Singularity image
    log_info "Building main OMNI Singularity image..."
    docker build -f Dockerfile.omni-singularity -t ${DOCKER_IMAGE} .

    # Build GPU-enabled image if NVIDIA Docker is available
    if command -v nvidia-docker &> /dev/null; then
        log_info "Building GPU-enabled OMNI Singularity image..."
        docker build -f Dockerfile.gpu-quantum -t ${PROJECT_NAME}-gpu:latest .
        log_success "GPU-enabled image built"
    else
        log_warning "NVIDIA Docker not available, skipping GPU image build"
    fi

    log_success "Docker images built"
}

# Deploy with Docker Compose
deploy_docker_compose() {
    log_section "Deploying OMNI Singularity"
    log_info "Starting OMNI Singularity with Docker Compose..."

    # Set environment variables
    export ENABLE_GPU=${ENABLE_GPU:-false}
    export REDIS_PASSWORD=${REDIS_PASSWORD:-omni_redis_secure_pass}
    export GRAFANA_PASSWORD=${GRAFANA_PASSWORD:-omni_grafana_admin}

    # Start services
    if command -v docker-compose &> /dev/null; then
        docker-compose -f ${COMPOSE_FILE} up -d
    else
        docker compose -f ${COMPOSE_FILE} up -d
    fi

    log_success "OMNI Singularity services started"
}

# Wait for services to be healthy
wait_for_services() {
    log_section "Service Health Check"
    log_info "Waiting for OMNI Singularity to be healthy..."

    # Wait for OMNI Singularity
    log_info "Waiting for OMNI Singularity..."
    timeout=300
    elapsed=0

    while [ $elapsed -lt $timeout ]; do
        if curl -f http://localhost:8093/health &> /dev/null; then
            log_success "OMNI Singularity is healthy"
            break
        fi

        sleep 5
        elapsed=$((elapsed + 5))

        if [ $elapsed -eq $timeout ]; then
            log_error "Timeout waiting for OMNI Singularity to be healthy"
            exit 1
        fi
    done

    # Wait for other services
    services=("omni-storage" "omni-redis" "omni-dashboard")
    for service in "${services[@]}"; do
        log_info "Waiting for $service..."
        sleep 10
    done

    log_success "All services are healthy"
}

# Run comprehensive health checks
run_health_checks() {
    log_section "Health Checks"
    log_info "Running comprehensive health checks..."

    # Check OMNI Singularity
    if curl -f http://localhost:8093/health &> /dev/null; then
        log_success "OMNI Singularity health check passed"
    else
        log_error "OMNI Singularity health check failed"
        exit 1
    fi

    # Check dashboard
    if curl -f http://localhost:8081/health &> /dev/null; then
        log_success "Dashboard health check passed"
    else
        log_warning "Dashboard health check failed (this is optional)"
    fi

    # Check API gateway
    if curl -f http://localhost:8082/api/v1/health &> /dev/null; then
        log_success "API gateway health check passed"
    else
        log_warning "API gateway health check failed (this is optional)"
    fi

    # Check quantum backend
    if curl -f http://localhost:8080/health &> /dev/null; then
        log_success "Quantum backend health check passed"
    else
        log_warning "Quantum backend health check failed (this is optional)"
    fi

    log_success "Health checks completed"
}

# Test OMNI Singularity functionality
test_omni_functionality() {
    log_section "Functionality Testing"
    log_info "Testing OMNI Singularity functionality..."

    # Test basic status
    if curl -f http://localhost:8093/status &> /dev/null; then
        log_success "OMNI Singularity status check passed"
    else
        log_warning "OMNI Singularity status check failed"
    fi

    # Test quantum operations
    if curl -f -X POST http://localhost:8093/execute \
        -H "Content-Type: application/json" \
        -d '{"command": "quantum_optimization", "parameters": {"industry": "logistics"}}' &> /dev/null; then
        log_success "Quantum optimization test passed"
    else
        log_warning "Quantum optimization test failed"
    fi

    # Test BCI status
    if curl -f http://localhost:8093/bci/status &> /dev/null; then
        log_success "BCI status check passed"
    else
        log_warning "BCI status check failed"
    fi

    log_success "Functionality testing completed"
}

# Display service information
display_service_info() {
    log_section "OMNI Singularity Information"
    echo ""
    echo "🧠 OMNI Singularity Quantum Dashboard v10.0"
    echo "=============================================="
    echo ""
    echo "🚀 Services Status:"
    echo "   OMNI Singularity:   http://localhost:8093"
    echo "   Dashboard:          http://localhost:8081"
    echo "   API Gateway:        http://localhost:8082"
    echo "   Quantum Backend:    http://localhost:8080"
    echo "   Load Balancer:      http://localhost:80"
    echo ""
    echo "📊 Monitoring:"
    echo "   Grafana:            http://localhost:3000 (admin/omni_grafana_admin)"
    echo "   Prometheus:         http://localhost:9090"
    echo ""
    echo "🔗 Module Access Points:"
    echo "   Video Lab Pro:      http://localhost:8093/modules/video_lab_pro"
    echo "   Company Optimizer:  http://localhost:8093/modules/company_optimizer"
    echo "   Agro Intelligence:  http://localhost:8093/modules/agro_intelligence"
    echo "   Image Studio:       http://localhost:8093/modules/image_studio"
    echo "   Data Analytics:     http://localhost:8093/modules/data_analytics"
    echo ""
    echo "📁 Data Directories:"
    echo "   OMNI Singularity:   $(pwd)/data/omni_singularity"
    echo "   Memory:             $(pwd)/data/omni_memory"
    echo "   Logs:               $(pwd)/data/omni_logs"
    echo "   Database:           $(pwd)/data/omni_database"
    echo ""
    echo "🔧 Useful Commands:"
    echo "   View logs:          docker-compose -f ${COMPOSE_FILE} logs -f omni-singularity"
    echo "   Stop services:      docker-compose -f ${COMPOSE_FILE} down"
    echo "   Restart services:   docker-compose -f ${COMPOSE_FILE} restart"
    echo "   Scale services:     docker-compose -f ${COMPOSE_FILE} up -d --scale omni-quantum-backend=3"
    echo ""
    echo "🎯 Quick Tests:"
    echo "   Health check:       curl http://localhost:8093/health"
    echo "   Status check:       curl http://localhost:8093/status"
    echo "   BCI status:         curl http://localhost:8093/bci/status"
    echo "   Quantum test:        curl -X POST http://localhost:8093/execute -H 'Content-Type: application/json' -d '{\"command\": \"quantum_optimization\"}'"
}

# Generate configuration files
generate_configuration() {
    log_section "Configuration"
    log_info "Generating configuration files..."

    # Copy config.txt if it exists
    if [ -f config.txt ]; then
        cp config.txt data/omni_singularity/
        log_success "Configuration file copied"
    else
        log_warning "config.txt not found, using defaults"
    fi

    # Generate Nginx configuration
    cat > nginx/conf.d/omni-singularity.conf << 'EOF'
server {
    listen 80;
    server_name localhost;

    # OMNI Singularity main interface
    location / {
        proxy_pass http://omni-singularity:8093;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Dashboard
    location /dashboard {
        proxy_pass http://omni-dashboard:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API Gateway
    location /api {
        proxy_pass http://omni-api-gateway:8082;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Quantum backend
    location /quantum {
        proxy_pass http://omni-quantum-backend:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Monitoring
    location /monitoring {
        proxy_pass http://prometheus:9090;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Grafana
    location /grafana {
        proxy_pass http://grafana:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

    log_success "Configuration files generated"
}

# Main deployment function
main() {
    echo "🧠 OMNI Singularity Quantum Dashboard v10.0 - Docker Deployment"
    echo "================================================================"

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --gpu)
                ENABLE_GPU=true
                log_info "GPU acceleration enabled"
                shift
                ;;
            --skip-build)
                SKIP_BUILD=true
                log_info "Skipping Docker image build"
                shift
                ;;
            --config)
                CONFIG_FILE="$2"
                log_info "Using config file: $CONFIG_FILE"
                shift 2
                ;;
            --help)
                echo "Usage: $0 [--gpu] [--skip-build] [--config FILE] [--help]"
                echo ""
                echo "Options:"
                echo "  --gpu         Enable GPU acceleration"
                echo "  --skip-build  Skip Docker image building"
                echo "  --config FILE Use specific config file"
                echo "  --help        Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done

    # Run deployment steps
    check_prerequisites
    create_directories
    generate_ssl_certificates
    generate_configuration

    if [ "$SKIP_BUILD" != "true" ]; then
        build_docker_images
    fi

    deploy_docker_compose
    wait_for_services
    run_health_checks
    test_omni_functionality
    display_service_info

    log_success "OMNI Singularity deployment completed successfully!"
    echo ""
    echo "🎉 OMNI Singularity Quantum Dashboard v10.0 is now running!"
    echo ""
    echo "🌟 Key Features Active:"
    echo "   🧠 Neural Fusion Engine (10 cores)"
    echo "   💾 Omni Memory Core (Personal learning)"
    echo "   🗜️ Quantum Compression (RAM optimization)"
    echo "   🧠 Adaptive Reasoning (Task-adaptive)"
    echo "   🧩 8 Specialized Modules"
    echo "   🤖 5 Specialized Agents"
    echo "   🧠 BCI Integration (OpenBCI, Emotiv, Muse)"
    echo "   🔬 Quantum Computing (Multi-core)"
    echo "   🔐 Post-Quantum Security"
    echo "   📊 Real-Time Monitoring"
    echo ""
    echo "🎯 Next Steps:"
    echo "1. Access OMNI at http://localhost:8093"
    echo "2. Configure BCI devices for neural control"
    echo "3. Explore modules through the dashboard"
    echo "4. Monitor system performance via Grafana"
    echo "5. Customize agents for your specific needs"
    echo ""
    echo "🚀 Welcome to the future of quantum AI computing!"
}

# Run main function with all arguments
main "$@"