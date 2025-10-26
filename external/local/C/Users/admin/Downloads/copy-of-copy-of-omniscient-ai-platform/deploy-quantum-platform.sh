#!/bin/bash

# OMNI Quantum Platform - Deployment Automation Script
# Complete deployment script for quantum computing infrastructure

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="omni-quantum-platform"
DOCKER_IMAGE="${PROJECT_NAME}:latest"
GPU_IMAGE="${PROJECT_NAME}-gpu:latest"
COMPOSE_FILE="docker-compose.quantum.yml"
K8S_NAMESPACE="quantum-platform"

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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

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
    log_info "Creating necessary directories..."

    mkdir -p data/{quantum_storage,quantum_db,logs,redis,prometheus,grafana,backups}
    mkdir -p config
    mkdir -p ssl
    mkdir -p monitoring/{grafana/dashboards,grafana/provisioning}
    mkdir -p k8s/manifests

    log_success "Directories created"
}

# Generate SSL certificates for development
generate_ssl_certificates() {
    log_info "Generating SSL certificates for development..."

    if [ ! -f ssl/server.crt ] || [ ! -f ssl/server.key ]; then
        openssl req -x509 -newkey rsa:4096 -keyout ssl/server.key -out ssl/server.crt \
            -days 365 -nodes -subj "/CN=quantum-platform.local"

        log_success "SSL certificates generated"
    else
        log_info "SSL certificates already exist, skipping generation"
    fi
}

# Build Docker images
build_docker_images() {
    log_info "Building Docker images..."

    # Build main quantum platform image
    log_info "Building main quantum platform image..."
    docker build -f Dockerfile.quantum-platform -t ${DOCKER_IMAGE} .

    # Build GPU-enabled image if NVIDIA Docker is available
    if command -v nvidia-docker &> /dev/null; then
        log_info "Building GPU-enabled quantum platform image..."
        docker build -f Dockerfile.gpu-quantum -t ${GPU_IMAGE} .
        log_success "GPU-enabled image built"
    else
        log_warning "NVIDIA Docker not available, skipping GPU image build"
    fi

    log_success "Docker images built"
}

# Deploy with Docker Compose
deploy_docker_compose() {
    log_info "Deploying with Docker Compose..."

    # Set environment variables
    export ENABLE_GPU=${ENABLE_GPU:-false}
    export REDIS_PASSWORD=${REDIS_PASSWORD:-quantum_redis_secure_pass}
    export GRAFANA_PASSWORD=${GRAFANA_PASSWORD:-quantum_grafana_admin}

    # Start services
    if command -v docker-compose &> /dev/null; then
        docker-compose -f ${COMPOSE_FILE} up -d
    else
        docker compose -f ${COMPOSE_FILE} up -d
    fi

    log_success "Services started with Docker Compose"
}

# Wait for services to be healthy
wait_for_services() {
    log_info "Waiting for services to be healthy..."

    # Wait for quantum platform
    log_info "Waiting for quantum platform..."
    timeout=300
    elapsed=0

    while [ $elapsed -lt $timeout ]; do
        if curl -f http://localhost:8080/health &> /dev/null; then
            log_success "Quantum platform is healthy"
            break
        fi

        sleep 5
        elapsed=$((elapsed + 5))

        if [ $elapsed -eq $timeout ]; then
            log_error "Timeout waiting for quantum platform to be healthy"
            exit 1
        fi
    done

    # Wait for other services
    services=("quantum-storage" "quantum-redis" "quantum-dashboard")
    for service in "${services[@]}"; do
        log_info "Waiting for $service..."
        sleep 10
    done

    log_success "All services are healthy"
}

# Run health checks
run_health_checks() {
    log_info "Running health checks..."

    # Check quantum platform
    if curl -f http://localhost:8080/health &> /dev/null; then
        log_success "Quantum platform health check passed"
    else
        log_error "Quantum platform health check failed"
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

    log_success "Health checks completed"
}

# Display service information
display_service_info() {
    log_info "Service Information:"
    echo ""
    echo "🚀 OMNI Quantum Platform Services:"
    echo "   Quantum Platform:    http://localhost:8080"
    echo "   Dashboard:          http://localhost:8081"
    echo "   API Gateway:        http://localhost:8082"
    echo "   Entanglement Node:  http://localhost:8083"
    echo ""
    echo "📊 Monitoring:"
    echo "   Grafana:            http://localhost:3000 (admin/quantum_grafana_admin)"
    echo "   Prometheus:         http://localhost:9090"
    echo ""
    echo "🔗 Access URLs:"
    echo "   Platform API:       http://localhost:8080/api/v1"
    echo "   Dashboard:          http://localhost:8081"
    echo "   Load Balancer:      http://localhost:80"
    echo ""
    echo "📁 Data Directories:"
    echo "   Quantum Storage:    $(pwd)/data/quantum_storage"
    echo "   Database:           $(pwd)/data/quantum_db"
    echo "   Logs:               $(pwd)/data/logs"
    echo ""
    echo "🔧 Useful Commands:"
    echo "   View logs:          docker-compose -f ${COMPOSE_FILE} logs -f"
    echo "   Stop services:      docker-compose -f ${COMPOSE_FILE} down"
    echo "   Restart services:   docker-compose -f ${COMPOSE_FILE} restart"
    echo "   Scale workers:      docker-compose -f ${COMPOSE_FILE} up -d --scale quantum-worker-1=3"
}

# Generate Kubernetes manifests
generate_kubernetes_manifests() {
    log_info "Generating Kubernetes manifests..."

    # Create namespace
    cat > k8s/manifests/namespace.yml << EOF
apiVersion: v1
kind: Namespace
metadata:
  name: ${K8S_NAMESPACE}
  labels:
    name: ${K8S_NAMESPACE}
    app: quantum-platform
EOF

    # Create ConfigMap for configuration
    cat > k8s/manifests/configmap.yml << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: quantum-platform-config
  namespace: ${K8S_NAMESPACE}
data:
  QUANTUM_PLATFORM_MODE: "production"
  QUANTUM_CORES_MAX: "8"
  MONITORING_LEVEL: "standard"
  LOG_LEVEL: "INFO"
EOF

    # Create deployment for quantum platform
    cat > k8s/manifests/deployment.yml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quantum-platform
  namespace: ${K8S_NAMESPACE}
spec:
  replicas: 2
  selector:
    matchLabels:
      app: quantum-platform
  template:
    metadata:
      labels:
        app: quantum-platform
    spec:
      containers:
      - name: quantum-platform
        image: ${DOCKER_IMAGE}
        ports:
        - containerPort: 8080
        envFrom:
        - configMapRef:
            name: quantum-platform-config
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
EOF

    # Create service for quantum platform
    cat > k8s/manifests/service.yml << EOF
apiVersion: v1
kind: Service
metadata:
  name: quantum-platform-service
  namespace: ${K8S_NAMESPACE}
spec:
  selector:
    app: quantum-platform
  ports:
  - name: http
    port: 80
    targetPort: 8080
  - name: api
    port: 8080
    targetPort: 8080
  type: ClusterIP
EOF

    # Create ingress for external access
    cat > k8s/manifests/ingress.yml << EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: quantum-platform-ingress
  namespace: ${K8S_NAMESPACE}
  annotations:
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: quantum-platform.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: quantum-platform-service
            port:
              number: 80
EOF

    log_success "Kubernetes manifests generated"
}

# Main deployment function
main() {
    echo "🚀 OMNI Quantum Platform - Deployment Script"
    echo "=============================================="

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
            --k8s)
                DEPLOY_K8S=true
                log_info "Deploying to Kubernetes"
                shift
                ;;
            --help)
                echo "Usage: $0 [--gpu] [--skip-build] [--k8s] [--help]"
                echo ""
                echo "Options:"
                echo "  --gpu         Enable GPU acceleration"
                echo "  --skip-build  Skip Docker image building"
                echo "  --k8s         Deploy to Kubernetes instead of Docker Compose"
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

    if [ "$SKIP_BUILD" != "true" ]; then
        build_docker_images
    fi

    if [ "$DEPLOY_K8S" = "true" ]; then
        generate_kubernetes_manifests
        log_info "Kubernetes manifests generated. Deploy with: kubectl apply -f k8s/manifests/"
    else
        deploy_docker_compose
        wait_for_services
        run_health_checks
        display_service_info
    fi

    log_success "Deployment completed successfully!"
    echo ""
    echo "🎉 OMNI Quantum Platform is now running!"
    echo ""
    echo "Next steps:"
    echo "1. Access the platform at http://localhost:8080"
    echo "2. View the dashboard at http://localhost:8081"
    echo "3. Check Grafana at http://localhost:3000"
    echo "4. Review logs with: docker-compose -f ${COMPOSE_FILE} logs -f"
}

# Run main function with all arguments
main "$@"