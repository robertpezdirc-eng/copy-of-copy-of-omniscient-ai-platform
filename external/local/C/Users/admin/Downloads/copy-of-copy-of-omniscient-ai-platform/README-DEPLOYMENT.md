# OMNI Quantum Platform - Deployment Guide

## 🚀 Quick Start

### Using Docker Compose (Recommended for Development)

```bash
# 1. Clone the repository
git clone <repository-url>
cd omni-quantum-platform

# 2. Make deployment script executable
chmod +x deploy-quantum-platform.sh

# 3. Deploy with Docker Compose
./deploy-quantum-platform.sh

# 4. Deploy with GPU support (if available)
./deploy-quantum-platform.sh --gpu

# 5. View service status
docker-compose -f docker-compose.quantum.yml ps
```

### Using Kubernetes (Recommended for Production)

```bash
# 1. Ensure kubectl is configured for your cluster

# 2. Make deployment script executable
chmod +x deploy-to-kubernetes.sh

# 3. Deploy to Kubernetes
./deploy-to-kubernetes.sh --replicas 3

# 4. Check deployment status
kubectl get pods -n quantum-platform
kubectl get services -n quantum-platform
```

## 📋 Prerequisites

### Docker Deployment
- Docker Engine 20.10+
- Docker Compose 2.0+ (or docker-compose 1.29+)
- 16GB+ RAM recommended
- 100GB+ free disk space

### Kubernetes Deployment
- Kubernetes cluster (1.24+)
- kubectl configured
- 32GB+ RAM per node recommended
- GPU nodes (optional, for acceleration)
- Storage class for persistent volumes

### GPU Support (Optional)
- NVIDIA GPU with CUDA 11.8+
- nvidia-docker 2.0+
- NVIDIA Container Toolkit

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    OMNI Quantum Platform                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Quantum   │  │   Quantum   │  │   Quantum   │              │
│  │    Cores    │  │   Storage   │  │ Entanglement│              │
│  │  (Multi-)   │  │ (Persistent)│  │    Layer    │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Industry  │  │   Security  │  │ Monitoring  │              │
│  │   Modules   │  │   (QKD &    │  │   System    │              │
│  │ (Logistics, │  │ Post-Quantum│  │             │              │
│  │  Pharma,    │  │   Crypto)   │  │             │              │
│  │   Energy)   │  └─────────────┘  └─────────────┘              │
│  └─────────────┘                                             │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Auto-     │  │   Load      │  │   Industrial│              │
│  │   Scaling   │  │  Balancing  │  │  Integration│              │
│  │   System    │  │   System    │  │   (Real Data│              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Integrations                        │
├─────────────────────────────────────────────────────────────────┤
│  Healthcare APIs │ Manufacturing │ Financial Data │ IoT Sensors │
│     (FHIR)       │     (MES)     │    Feeds       │  Networks   │
│                  │               │                │             │
│  Energy Grids    │   Weather     │   Traffic      │ Government  │
│                  │     APIs      │     Data       │    Data     │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Configuration

### Environment Variables

#### Core Platform Settings
```bash
QUANTUM_PLATFORM_MODE=production          # development|staging|production
QUANTUM_CORES_MAX=8                       # Maximum quantum cores
QUANTUM_CORES_MIN=2                       # Minimum quantum cores
MONITORING_LEVEL=standard                 # basic|standard|detailed|debug
LOG_LEVEL=INFO                           # DEBUG|INFO|WARNING|ERROR
```

#### Storage Settings
```bash
QUANTUM_STORAGE_TYPE=sqlite              # sqlite|postgresql|redis
QUANTUM_STORAGE_PATH=/app/quantum_storage
STORAGE_COMPRESSION=true                 # Enable data compression
STORAGE_ENCRYPTION=false                 # Enable data encryption
```

#### Security Settings
```bash
ENABLE_QKD=true                         # Enable Quantum Key Distribution
ENABLE_POST_QUANTUM_CRYPTO=true         # Enable post-quantum cryptography
SECURITY_SCAN_INTERVAL=3600             # Security scan interval (seconds)
```

#### Performance Settings
```bash
ENABLE_AUTO_SCALING=true                # Enable automatic scaling
SCALING_CHECK_INTERVAL=30               # Scaling check interval (seconds)
MAX_SCALE_UP_RATE=2                     # Maximum scale-up rate
MAX_SCALE_DOWN_RATE=1                   # Maximum scale-down rate
```

## 🚀 Deployment Options

### 1. Local Development (Docker Compose)

```bash
# Start all services
./deploy-quantum-platform.sh

# Start with GPU support
./deploy-quantum-platform.sh --gpu

# Skip Docker image building (use existing images)
./deploy-quantum-platform.sh --skip-build

# View logs
docker-compose -f docker-compose.quantum.yml logs -f

# Stop services
docker-compose -f docker-compose.quantum.yml down

# Scale specific services
docker-compose -f docker-compose.quantum.yml up -d --scale quantum-worker-1=5
```

### 2. Production Kubernetes Deployment

```bash
# Deploy to Kubernetes
./deploy-to-kubernetes.sh --replicas 5

# Scale deployment
kubectl scale deployment quantum-platform --replicas=10 -n quantum-platform

# Update platform image
kubectl set image deployment/quantum-platform quantum-platform=omni-quantum-platform:v2.0 -n quantum-platform

# View logs
kubectl logs -f deployment/quantum-platform -n quantum-platform

# Restart deployment
kubectl rollout restart deployment/quantum-platform -n quantum-platform
```

### 3. Hybrid Cloud Deployment

```bash
# Deploy core services on-premises
./deploy-quantum-platform.sh

# Deploy worker nodes in cloud
kubectl apply -f k8s/cloud-workers.yml

# Configure hybrid networking
kubectl apply -f k8s/hybrid-network.yml
```

## 📊 Monitoring and Observability

### Access Points
- **Main Platform**: http://localhost:8080 (Docker) / http://quantum-platform.your-domain.com (K8s)
- **Dashboard**: http://localhost:8081 (Docker) / http://quantum-platform.your-domain.com/dashboard (K8s)
- **Grafana**: http://localhost:3000 (admin/quantum_grafana_admin)
- **Prometheus**: http://localhost:9090

### Key Metrics to Monitor
- Quantum circuit execution success rate
- Entanglement fidelity and uptime
- Storage utilization and performance
- Auto-scaling events and triggers
- Security events and alerts
- Industrial data integration status

#### SSE Streaming Counters (OMNI Unified Platform)
- Endpoint: `/metrics` (Prometheus plaintext)
- Counters:
  - `omni_sse_streams_started`
  - `omni_sse_streams_done`
  - `omni_sse_streams_fallback`
  - `omni_sse_streams_errors`
- Reference: see `docs/omni_prometheus.md` for scrape configuration and Grafana tips

#### Alerting and Dashboard

- Prometheus alert rules: `alerts/omni_sse_rules.yml` (include via `rule_files` in `prometheus.yml`).
  - OmniSSEErrorsSpike — triggers on elevated error rate.
  - OmniSSEFallbackSustained — triggers on sustained fallback rate.
- Grafana dashboard: `docs/grafana_sse_dashboard.json` (import into Grafana and set Prometheus datasource UID).
  - Panels include total counters and rates for started, errors, and fallback.

##### Alertmanager (delivery)
- Sample config: `alerts/alertmanager.yml` with email and Slack receivers.
- Run Alertmanager (example):
  - Docker: `docker run -d -p 9093:9093 -v $(pwd)/alerts:/etc/alertmanager prom/alertmanager \
    --config.file=/etc/alertmanager/alertmanager.yml`
  - Binary: download from https://prometheus.io/download/ and run with `--config.file`.
- Wire Prometheus → Alertmanager:
  - In `prometheus.yml` set:
    ```
    alerting:
      alertmanagers:
        - static_configs:
            - targets: ['localhost:9093']
    ```

##### SSE metrics simulation
- Script: `scripts/simulate_sse_metrics.py`
- Purpose: exercise `/api/gcp/gemini/stream` to increment `started`, `done`, and trigger `fallback/errors` via a nonexistent model.
- Run:
  - `python scripts/simulate_sse_metrics.py`
- Verify:
  - Compare `[BEFORE]` and `[AFTER]` snapshots printed by the script and/or query Prometheus.

## 🔒 Security Considerations

### Post-Quantum Cryptography
- All communications protected with post-quantum algorithms
- Quantum key distribution for unbreakable encryption
- Regular key rotation and security audits

### Network Security
- Service mesh with mutual TLS authentication
- Network policies restricting traffic
- Ingress controllers with rate limiting

### Data Protection
- Encrypted persistent volumes
- Secure API gateways with authentication
- Audit logging for compliance

## 🚨 Troubleshooting

### Common Issues

#### Docker Deployment Issues
```bash
# Check service logs
docker-compose -f docker-compose.quantum.yml logs quantum-platform

# Restart specific service
docker-compose -f docker-compose.quantum.yml restart quantum-platform

# Clean restart
docker-compose -f docker-compose.quantum.yml down
docker-compose -f docker-compose.quantum.yml up -d
```

#### Kubernetes Issues
```bash
# Check pod status
kubectl get pods -n quantum-platform

# View pod logs
kubectl logs -f deployment/quantum-platform -n quantum-platform

# Check resource usage
kubectl top pods -n quantum-platform

# Describe pod for detailed information
kubectl describe pod -l app=quantum-platform -n quantum-platform
```

#### GPU Issues
```bash
# Check GPU availability
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi

# Verify GPU support in container
docker exec -it omni-quantum-platform python3 -c "import torch; print(torch.cuda.is_available())"
```

### Performance Tuning

#### Memory Issues
- Increase memory limits in docker-compose.yml
- Scale down concurrent operations
- Enable storage compression

#### Network Issues
- Check firewall settings
- Verify DNS resolution
- Monitor network latency

#### Storage Issues
- Monitor disk space usage
- Check storage mount permissions
- Verify backup schedules

## 🔄 Scaling and High Availability

### Horizontal Scaling
```bash
# Scale quantum workers
docker-compose -f docker-compose.quantum.yml up -d --scale quantum-worker-1=10

# Scale in Kubernetes
kubectl scale deployment quantum-platform --replicas=20 -n quantum-platform
```

### Auto-Scaling Configuration
```yaml
# Enable HPA in Kubernetes
kubectl autoscale deployment quantum-platform --cpu-percent=70 --min=3 --max=50 -n quantum-platform
```

### High Availability Setup
- Deploy across multiple availability zones
- Configure load balancer health checks
- Set up automated failover

## 🔧 Maintenance

### Regular Tasks
- Monitor system health and performance
- Update Docker images regularly
- Review and rotate security keys
- Backup quantum state data
- Update industrial data integrations

### Update Procedures
```bash
# Update Docker images
docker-compose -f docker-compose.quantum.yml build --no-cache

# Rolling update in Kubernetes
kubectl set image deployment/quantum-platform quantum-platform=omni-quantum-platform:v2.0 -n quantum-platform
kubectl rollout status deployment/quantum-platform -n quantum-platform
```

## 📞 Support

### Getting Help
- Check logs: `docker-compose -f docker-compose.quantum.yml logs -f`
- Review documentation in `/docs` directory
- Monitor Grafana dashboards for system health
- Check GitHub issues for known problems

### Emergency Procedures
1. Check system health endpoints
2. Review recent alerts in Grafana
3. Check resource utilization
4. Restart failed services
5. Contact support if issues persist

## 🎯 Best Practices

### Security
- Use strong passwords for all services
- Enable encryption for data at rest
- Regular security updates and patches
- Monitor for unusual activities

### Performance
- Right-size resource allocations
- Use monitoring to identify bottlenecks
- Implement proper caching strategies
- Regular performance testing

### Reliability
- Implement proper backup strategies
- Use health checks and readiness probes
- Monitor system metrics continuously
- Plan for disaster recovery

### Cost Optimization
- Right-size deployments based on usage
- Use auto-scaling to match demand
- Monitor resource utilization
- Clean up unused resources

---

**🎉 Congratulations! Your OMNI Quantum Platform is now deployed and ready for quantum computing workloads!**

## Quick Vertex connectivity checks

These PowerShell-friendly curl snippets help you validate connectivity for the recommended models.

Prerequisites:
- gcloud CLI installed and authenticated (for Vertex AI OAuth token)
- GOOGLE_API_KEY set (for GENAI fallback)
- Confirm your PROJECT and REGION (examples use europe-west1)

### 1) Vertex AI: gemini-2.5-pro (generateContent)

```powershell
$PROJECT = "refined-graph-471712-n9"
$REGION  = "europe-west1"
$TOKEN   = $(gcloud auth print-access-token)
$URL     = "https://$REGION-aiplatform.googleapis.com/v1/projects/$PROJECT/locations/$REGION/publishers/google/models/gemini-2.5-pro:generateContent"
$BODY    = '{"contents":[{"parts":[{"text":"Ping Vertex AI from curl"}]}]}'

curl.exe -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d $BODY $URL
```

Expected: HTTP 200 with candidates and text content.

### 2) Google Generative Language API: gemini-2.5-flash (fallback)

```powershell
$API_KEY = $env:GOOGLE_API_KEY
$URL     = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key=$API_KEY"
$BODY    = '{"contents":[{"parts":[{"text":"Ping GENAI from curl"}]}]}'

curl.exe -H "Content-Type: application/json" -d $BODY $URL
```

Expected: HTTP 200 with candidates and text content.

Tips:
- If Vertex responds with 401/403, verify your gcloud account, project access, and chosen region.
- If GENAI responds with quota/permission issues, double check the API key and billing.
- Prefer gemini-2.5-pro (default) and gemini-2.5-flash (fallback); older families may be deprecated.
- Older families (`gemini-1.5-*`, some `gemini-2.0-*`) may be deprecated or inaccessible for new projects and can return 404.

Setup hints:
- Set `VERTEX_AI_MODEL=gemini-2.5-pro` in Dockerfiles/images for consistency.
- Set `GENAI_FALLBACK_MODEL=gemini-2.5-flash` when using AI Studio fallback.
- Keep `vertex_ai_config.json` in sync (model + endpoints) with selected model IDs.

## SSE streaming checks (CLI)

Test the streaming SSE endpoint and display chunks in the terminal.

- Endpoint: `GET /api/gcp/gemini/stream?prompt=...&model=...`
- Defaults: model falls back to Vertex config (`gemini-2.5-pro`) if not provided

### Windows PowerShell

1) Raw SSE output:
```
$ProgressPreference = 'SilentlyContinue'
curl.exe --no-buffer "http://localhost:8081/api/gcp/gemini/stream?prompt=Stream%20test%20from%20CLI"
```

2) Show only chunk lines:
```
$ProgressPreference = 'SilentlyContinue'
curl.exe --no-buffer "http://localhost:8081/api/gcp/gemini/stream?prompt=Stream%20test%20from%20CLI" | Select-String -Pattern "^data: "
```

3) Extract only chunk text (requires jq):
```
$ProgressPreference = 'SilentlyContinue'
curl.exe --no-buffer "http://localhost:8081/api/gcp/gemini/stream?prompt=Stream%20test%20from%20CLI" |
  Select-String -Pattern "^data: " |
  ForEach-Object { $_.Line -replace '^data: ' } |
  jq -r '.chunk'
```

### macOS/Linux (bash)

1) Raw SSE output:
```
curl --no-buffer 'http://localhost:8081/api/gcp/gemini/stream?prompt=Stream%20test%20from%20CLI'
```

2) Extract chunk lines:
```
curl --no-buffer 'http://localhost:8081/api/gcp/gemini/stream?prompt=Stream%20test%20from%20CLI' | sed -n 's/^data: //p'
```

3) Extract chunk text (requires jq):
```
curl --no-buffer 'http://localhost:8081/api/gcp/gemini/stream?prompt=Stream%20test%20from%20CLI' | sed -n 's/^data: //p' | jq -r '.chunk'
```

Notes:
- Use `--no-buffer` to see chunks immediately.
- Add `&model=gemini-2.5-pro` to force Vertex model; otherwise defaults apply.
- Stream ends with a final `event: done`.