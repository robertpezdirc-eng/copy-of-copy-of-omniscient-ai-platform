#!/bin/bash

# OMNI Quantum Platform - Kubernetes Deployment Script
# Deploy quantum computing platform to Kubernetes cluster

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K8S_NAMESPACE="quantum-platform"
MANIFESTS_DIR="k8s/manifests"

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
check_k8s_prerequisites() {
    log_info "Checking Kubernetes prerequisites..."

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi

    # Check if cluster is accessible
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi

    # Check if namespace exists, create if not
    if ! kubectl get namespace ${K8S_NAMESPACE} &> /dev/null; then
        log_info "Creating namespace ${K8S_NAMESPACE}..."
        kubectl create namespace ${K8S_NAMESPACE}
    fi

    log_success "Kubernetes prerequisites check completed"
}

# Create ConfigMaps and Secrets
create_k8s_resources() {
    log_info "Creating ConfigMaps and Secrets..."

    # Create ConfigMap
    kubectl apply -f ${MANIFESTS_DIR}/configmap.yml -n ${K8S_NAMESPACE}

    # Create secrets for sensitive data
    if ! kubectl get secret quantum-platform-secrets -n ${K8S_NAMESPACE} &> /dev/null; then
        log_info "Creating secrets..."
        kubectl create secret generic quantum-platform-secrets \
            --from-literal=redis-password=$(openssl rand -hex 32) \
            --from-literal=grafana-password=$(openssl rand -hex 16) \
            --from-literal=jwt-secret=$(openssl rand -hex 32) \
            -n ${K8S_NAMESPACE}
    fi

    log_success "ConfigMaps and Secrets created"
}

# Deploy PersistentVolumeClaims
deploy_storage() {
    log_info "Deploying persistent storage..."

    kubectl apply -f ${MANIFESTS_DIR}/pvc.yml -n ${K8S_NAMESPACE}

    # Wait for PVCs to be bound
    log_info "Waiting for PersistentVolumeClaims to be bound..."
    kubectl wait --for=condition=Bound pvc/quantum-storage-pvc -n ${K8S_NAMESPACE} --timeout=300s
    kubectl wait --for=condition=Bound pvc/quantum-logs-pvc -n ${K8S_NAMESPACE} --timeout=300s

    log_success "Persistent storage deployed"
}

# Deploy monitoring stack (Prometheus & Grafana)
deploy_monitoring() {
    log_info "Deploying monitoring stack..."

    # Deploy Prometheus
    kubectl apply -f ${MANIFESTS_DIR}/prometheus-deployment.yml -n ${K8S_NAMESPACE}
    kubectl apply -f ${MANIFESTS_DIR}/prometheus-service.yml -n ${K8S_NAMESPACE}

    # Deploy Grafana
    kubectl apply -f ${MANIFESTS_DIR}/grafana-deployment.yml -n ${K8S_NAMESPACE}
    kubectl apply -f ${MANIFESTS_DIR}/grafana-service.yml -n ${K8S_NAMESPACE}

    # Wait for monitoring services
    kubectl wait --for=condition=Available deployment/prometheus -n ${K8S_NAMESPACE} --timeout=300s
    kubectl wait --for=condition=Available deployment/grafana -n ${K8S_NAMESPACE} --timeout=300s

    log_success "Monitoring stack deployed"
}

# Deploy main quantum platform
deploy_quantum_platform() {
    log_info "Deploying quantum platform..."

    # Apply all manifests in order
    kubectl apply -f ${MANIFESTS_DIR}/namespace.yml
    kubectl apply -f ${MANIFESTS_DIR}/deployment.yml -n ${K8S_NAMESPACE}
    kubectl apply -f ${MANIFESTS_DIR}/service.yml -n ${K8S_NAMESPACE}
    kubectl apply -f ${MANIFESTS_DIR}/ingress.yml -n ${K8S_NAMESPACE}

    # Wait for deployment to be ready
    log_info "Waiting for quantum platform deployment..."
    kubectl wait --for=condition=Available deployment/quantum-platform -n ${K8S_NAMESPACE} --timeout=600s

    # Wait for pods to be ready
    kubectl wait --for=condition=Ready pod -l app=quantum-platform -n ${K8S_NAMESPACE} --timeout=300s

    log_success "Quantum platform deployed"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."

    # Check pod status
    kubectl get pods -n ${K8S_NAMESPACE}

    # Check service status
    kubectl get services -n ${K8S_NAMESPACE}

    # Check ingress status
    kubectl get ingress -n ${K8S_NAMESPACE}

    # Test platform health
    QUANTUM_SERVICE_IP=$(kubectl get service quantum-platform-loadbalancer -n ${K8S_NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

    if [ ! -z "$QUANTUM_SERVICE_IP" ]; then
        log_info "Testing platform health at http://${QUANTUM_SERVICE_IP}/health"
        # Wait a bit for services to fully start
        sleep 30

        if curl -f http://${QUANTUM_SERVICE_IP}/health &> /dev/null; then
            log_success "Quantum platform health check passed"
        else
            log_warning "Quantum platform health check failed - services may still be starting"
        fi
    else
        log_warning "LoadBalancer IP not available yet"
    fi

    log_success "Deployment verification completed"
}

# Display deployment information
display_deployment_info() {
    log_info "Deployment Information:"
    echo ""
    echo "🚀 OMNI Quantum Platform Kubernetes Deployment:"
    echo "   Namespace:          ${K8S_NAMESPACE}"
    echo "   Pods:               kubectl get pods -n ${K8S_NAMESPACE}"
    echo "   Services:           kubectl get services -n ${K8S_NAMESPACE}"
    echo "   Ingress:            kubectl get ingress -n ${K8S_NAMESPACE}"
    echo ""
    echo "📊 Monitoring:"
    echo "   Grafana:            http://grafana.${K8S_NAMESPACE}.your-domain.com"
    echo "   Prometheus:         http://prometheus.${K8S_NAMESPACE}.your-domain.com"
    echo ""
    echo "🔗 Access URLs:"
    echo "   Platform:           http://quantum-platform.your-domain.com"
    echo "   API:                http://quantum-platform.your-domain.com/api"
    echo "   Dashboard:          http://quantum-platform.your-domain.com/dashboard"
    echo ""
    echo "🔧 Management Commands:"
    echo "   View logs:          kubectl logs -f deployment/quantum-platform -n ${K8S_NAMESPACE}"
    echo "   Scale deployment:   kubectl scale deployment quantum-platform --replicas=5 -n ${K8S_NAMESPACE}"
    echo "   Update image:       kubectl set image deployment/quantum-platform quantum-platform=omni-quantum-platform:v2.0 -n ${K8S_NAMESPACE}"
    echo "   Restart pods:       kubectl rollout restart deployment/quantum-platform -n ${K8S_NAMESPACE}"
    echo ""
    echo "🗑️  Cleanup:"
    echo "   Remove deployment:  kubectl delete namespace ${K8S_NAMESPACE}"
}

# Scale deployment
scale_deployment() {
    local replicas=${1:-3}

    log_info "Scaling deployment to ${replicas} replicas..."

    kubectl scale deployment quantum-platform --replicas=${replicas} -n ${K8S_NAMESPACE}

    # Wait for scaling to complete
    kubectl wait --for=condition=Ready pod -l app=quantum-platform -n ${K8S_NAMESPACE} --timeout=300s

    log_success "Deployment scaled to ${replicas} replicas"
}

# Main deployment function
main() {
    echo "🚀 OMNI Quantum Platform - Kubernetes Deployment"
    echo "================================================"

    # Parse command line arguments
    SCALE_REPLICAS=3

    while [[ $# -gt 0 ]]; do
        case $1 in
            --replicas)
                SCALE_REPLICAS="$2"
                shift 2
                ;;
            --skip-storage)
                SKIP_STORAGE=true
                log_info "Skipping storage deployment"
                shift
                ;;
            --help)
                echo "Usage: $0 [--replicas N] [--skip-storage] [--help]"
                echo ""
                echo "Options:"
                echo "  --replicas N      Number of replicas to deploy (default: 3)"
                echo "  --skip-storage    Skip persistent storage deployment"
                echo "  --help           Show this help message"
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
    check_k8s_prerequisites
    create_k8s_resources

    if [ "$SKIP_STORAGE" != "true" ]; then
        deploy_storage
    fi

    deploy_monitoring
    deploy_quantum_platform
    scale_deployment $SCALE_REPLICAS
    verify_deployment
    display_deployment_info

    log_success "Kubernetes deployment completed successfully!"
    echo ""
    echo "🎉 OMNI Quantum Platform is now running on Kubernetes!"
    echo ""
    echo "Next steps:"
    echo "1. Configure DNS to point to the LoadBalancer IP"
    echo "2. Set up SSL certificates for production use"
    echo "3. Configure monitoring alerts and notifications"
    echo "4. Set up backup strategies for persistent data"
}

# Run main function with all arguments
main "$@"