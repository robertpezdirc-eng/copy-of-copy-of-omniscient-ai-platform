# OMNI Platform - Deployment Guide

## 🚀 Complete Deployment Strategy

This guide covers deploying the OMNI Platform to Google Cloud (Cloud Run and GKE) for production use.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Google Cloud Deployment](#google-cloud-deployment)
4. [Cloud Run Deployment](#cloud-run-deployment)
5. [Environment Variables](#environment-variables)
6. [Monitoring & Logging](#monitoring--logging)
7. [Troubleshooting](#troubleshooting)
8. [Security Considerations](#security-considerations)

## 🚀 Quick Start

### Option 1: Cloud Run (Recommended for quick deployment)

```bash
# 1. Authenticate with Google Cloud
gcloud auth login

# 2. Set the project
gcloud config set project YOUR_PROJECT_ID

# 3. Enable required APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com

# 4. Deploy directly from source to Cloud Run
gcloud run deploy omni-dashboard --source . --region europe-west1 --allow-unauthenticated --port 8080 \
  --set-env-vars OMNI_SYSTEM_CHECKS=false,OMNI_QUIET_CLOUDRUN=true,OMNI_CLOUDRUN_LOG_LEVEL=WARNING
```

### Option 2: Google Kubernetes Engine (Advanced)

```bash
# 1. Install Google Cloud CLI and kubectl
curl https://sdk.cloud.google.com | bash
gcloud components install kubectl

# 2. Authenticate
gcloud auth login

# 3. Deploy to Google Cloud (GKE)
chmod +x deploy-to-google-cloud.sh
./deploy-to-google-cloud.sh
```

## 📋 Prerequisites

### Required Tools

- **Git** - Version control
- **Python 3.8+** - Runtime environment
- **pip** - Python package manager
- **Docker** - Containerization (for Google Cloud)

### Cloud Platform Accounts

- **Railway Account** - railway.app
- **Google Cloud Account** - console.cloud.google.com (optional)

### API Keys and Secrets

- **OpenAI API Key** - platform.openai.com
- **Google Cloud Service Account** - For GCS access (optional)
- **Custom Domain** - For production use (optional)

## 🌐 Google Cloud Deployment

### Step 1: Prepare Google Cloud

1. **Create a Google Cloud Project**
   ```bash
   gcloud projects create omni-platform-2024
   gcloud config set project omni-platform-2024
   ```

2. **Enable Required APIs**
   ```bash
   gcloud services enable container.googleapis.com
   gcloud services enable storage.googleapis.com
   gcloud services enable monitoring.googleapis.com
   gcloud services enable logging.googleapis.com
   ```

3. **Create Service Account**
   ```bash
   gcloud iam service-accounts create omni-platform-sa
   gcloud projects add-iam-policy-binding omni-platform-2024 \
       --member="serviceAccount:omni-platform-sa@omni-platform-2024.iam.gserviceaccount.com" \
       --role="roles/owner"
   ```

4. **Download Service Account Key**
   ```bash
   gcloud iam service-accounts keys create gcp-credentials.json \
       --iam-account=omni-platform-sa@omni-platform-2024.iam.gserviceaccount.com
   ```

### Step 2: Deploy Application

```bash
# Run the deployment script
./deploy-to-google-cloud.sh

# Or manually:
gcloud container clusters create omni-platform-cluster --region europe-west1 --num-nodes 3
gcloud container clusters get-credentials omni-platform-cluster --region europe-west1
kubectl apply -f google-cloud-deploy.yaml
```

### Step 3: Verify Deployment

```bash
# Check pods status
kubectl get pods -n omni-platform

# Check services
kubectl get services -n omni-platform

# View logs
kubectl logs -f deployment/omni-platform-deployment -n omni-platform

# Port forward for local testing
kubectl port-forward service/omni-platform-service 8080:80 -n omni-platform
```

## ☁️ Cloud Run Deployment

### Step 1: Prepare Google Cloud Project

1. **Set project and region**
   ```bash
   export PROJECT_ID="omni-platform-2024"
   export REGION="europe-west1"
   gcloud config set project $PROJECT_ID
   gcloud config set run/region $REGION
   ```

2. **Enable required APIs**
   ```bash
   gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com logging.googleapis.com monitoring.googleapis.com
   ```

3. **Create service account (optional)**
   ```bash
   gcloud iam service-accounts create omni-dashboard-sa --display-name "OMNI Dashboard SA"
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:omni-dashboard-sa@$PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/run.admin"
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:omni-dashboard-sa@$PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/storage.admin"
   ```

### Step 2: Build and Deploy to Cloud Run

```bash
# Build the container image
gcloud builds submit --tag gcr.io/$PROJECT_ID/omni-dashboard

# Deploy to Cloud Run (managed)
#gcloud run deploy omni-dashboard --image gcr.io/$PROJECT_ID/omni-dashboard --region $REGION --allow-unauthenticated --port 8080 \
#  --set-env-vars=OMNI_SYSTEM_CHECKS=false,OMNI_QUIET_CLOUDRUN=true,OMNI_CLOUDRUN_LOG_LEVEL=WARNING

# Alternatively deploy directly from source
gcloud run deploy omni-dashboard --source . --region $REGION --allow-unauthenticated --port 8080 \
  --set-env-vars OMNI_SYSTEM_CHECKS=false,OMNI_QUIET_CLOUDRUN=true,OMNI_CLOUDRUN_LOG_LEVEL=WARNING
```

### Step 3: Custom Domain (Optional)

```bash
# Map a custom domain
gcloud run domain-mappings create --service omni-dashboard --domain yourdomain.com --region $REGION

# Verify DNS (Cloud Run will instruct required records)
```

## 🔧 Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing secret | `omni_platform_production_secret_key_2024` |
| `GCS_BUCKET` | Google Cloud Storage bucket | `omni-singularity-storage` |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | `omni-platform-2024` |
| `DEV_MODE` | Development mode | `false` |
| `OMNI_SYSTEM_CHECKS` | System service checks | `false` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | `""` |
| `GOOGLE_API_KEY` | Google API key | `""` |
| `QUANTUM_API_KEY` | Quantum API key | `""` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `PORT` | Server port | `8080` |

### Setting Variables

**Railway:**
```bash
railway variables set VARIABLE_NAME="value"
```

**Google Cloud:**
```bash
kubectl create secret generic omni-secrets \
    --from-literal=VARIABLE_NAME="value" \
    -n omni-platform
```

## 📊 Monitoring & Logging

### Railway Monitoring

Railway provides built-in monitoring:
- **Dashboard**: railway.app/dashboard
- **Logs**: `railway logs --follow`
- **Metrics**: `railway metrics`

### Google Cloud Monitoring

1. **Enable Monitoring**
   ```bash
   kubectl apply -f - <<EOF
   apiVersion: v1
   kind: ServiceMonitor
   metadata:
     name: omni-platform-monitor
   spec:
     selector:
       matchLabels:
         app: omni-platform
     endpoints:
     - port: metrics
       path: /metrics
   EOF
   ```

2. **View Metrics**
   - Google Cloud Console → Monitoring
   - Custom dashboards available

### Application Health Checks

The application includes built-in health monitoring:
- **Health Endpoint**: `/api/health`
- **Metrics Endpoint**: `/api/metrics`
- **Service Status**: `/api/services`

## 🔍 Troubleshooting

### Common Issues

#### 1. Authentication Errors (401)
**Problem**: Invalid JWT tokens
**Solution**:
```bash
# Regenerate SECRET_KEY
railway variables set SECRET_KEY="new-secret-key"
# Restart service
railway service restart
```

#### 2. Google Cloud Storage Errors
**Problem**: GCS bucket not accessible
**Solution**:
```bash
# Check bucket permissions
gsutil ls gs://omni-singularity-storage/
# Verify service account has storage permissions
```

#### 3. OpenAI API Errors
**Problem**: Invalid API key
**Solution**:
```bash
# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

#### 4. High Memory Usage
**Problem**: Application using too much memory
**Solution**:
```bash
# Scale down
railway service scale 0
railway service scale 1
# Check for memory leaks in logs
railway logs --follow
```

### Debug Commands

**Railway:**
```bash
railway logs --follow          # Live logs
railway status                 # Service status
railway variables              # Environment variables
railway shell                  # Interactive shell
```

**Google Cloud:**
```bash
kubectl get pods -n omni-platform              # Pod status
kubectl logs -f deployment/omni-platform-deployment -n omni-platform  # Logs
kubectl describe pod <pod-name> -n omni-platform  # Pod details
kubectl exec -it <pod-name> -n omni-platform -- /bin/bash  # Shell access
```

## 🔒 Security Considerations

### Production Security Checklist

- [ ] **Secret Management**: Use Railway secrets for sensitive data
- [ ] **HTTPS Only**: Enable HTTPS in production
- [ ] **CORS Configuration**: Restrict allowed origins
- [ ] **API Rate Limiting**: Implement rate limiting
- [ ] **Input Validation**: Validate all user inputs
- [ ] **Error Handling**: Don't expose sensitive information in errors
- [ ] **Logging**: Log security events and access patterns
- [ ] **Monitoring**: Set up alerts for suspicious activities

### SSL/TLS Configuration

**Railway (Automatic)**:
- Railway provides free SSL certificates
- Automatic HTTPS redirection

**Google Cloud**:
```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create Let's Encrypt certificate
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: omni-platform-tls
spec:
  secretName: omni-platform-tls-secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - omni-platform.yourdomain.com
EOF
```

## 🚀 Performance Optimization

### Railway Performance

1. **Auto-scaling**: Configure based on CPU/memory usage
2. **Database**: Use Railway PostgreSQL for data persistence
3. **CDN**: Use Railway's built-in CDN for static assets
4. **Caching**: Implement Redis for session caching

### Google Cloud Performance

1. **Horizontal Pod Autoscaling**:
   ```bash
   kubectl autoscale deployment omni-platform-deployment \
       --cpu-percent=70 --min=3 --max=10 -n omni-platform
   ```

2. **Load Balancer Optimization**:
   - Use Google Cloud Load Balancer
   - Enable Cloud CDN
   - Configure health checks

3. **Database Optimization**:
   - Use Cloud SQL for production
   - Enable connection pooling
   - Configure read replicas

## 📞 Support

### Getting Help

1. **Railway Documentation**: https://docs.railway.app
2. **Google Cloud Documentation**: https://cloud.google.com/docs
3. **Application Logs**: Check Railway/Google Cloud dashboards
4. **Community Support**: GitHub Issues for bug reports

### Emergency Contacts

- **Railway Status**: status.railway.app
- **Google Cloud Status**: status.cloud.google.com
- **Application Health**: Monitor `/api/health` endpoint

---

## 🎯 Deployment Summary

✅ **Railway**: Quick, easy, managed platform
✅ **Google Cloud**: Full control, scalable, enterprise-ready
✅ **Both**: Production-ready, monitored, secure

Choose Railway for quick deployment or Google Cloud for maximum control and scalability.

## Recommended Gemini Models (Vertex AI / Fallback)

- Prefer Vertex AI default model: `gemini-2.5-pro` (broad access, stable)
- Prefer fallback (Google AI Studio API): `gemini-2.5-flash`
- Note: Older families (e.g., `gemini-1.5-*` or some `gemini-2.0-*`) may be deprecated or not accessible for new projects and can return 404 Not Found.

Configuration tips:
- Set `VERTEX_AI_MODEL=gemini-2.5-pro` in Dockerfiles or environment for consistent builds.
- Set `GENAI_FALLBACK_MODEL=gemini-2.5-flash` in environment when enabling AI Studio fallback.
- Ensure `vertex_ai_config.json`’s `vertex_ai.model` and `endpoints` match the chosen model ID (e.g., update `.../models/gemini-2.5-pro:generateContent`).


## Quick Vertex connectivity checks

These are simple PowerShell-friendly curl examples to verify connectivity for the recommended models.

Prerequisites:
- gcloud CLI installed and authenticated (for Vertex AI OAuth token)
- GOOGLE_API_KEY set (for Generative Language API fallback)
- Ensure your PROJECT and REGION are correct (examples use europe-west1)

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

Notes:
- If Vertex returns an auth error, ensure your gcloud account has access to the project and region.
- If GENAI returns a quota or permission error, verify the API key and Google Cloud billing status.
- Some older model families may be deprecated or unavailable; prefer gemini-2.5-pro (default) and gemini-2.5-flash (fallback).


## SSE streaming: komentari i metrike

Ovaj servis emituje Server-Sent Events (SSE) za Gemini/GCP rute sa doslednim "header-style" komentarima i metrikama.

- Endpoint: `/api/gcp/gemini/stream`
- Query parametri:
  - `prompt`: tekst upita
  - `source`: `sim` | `genai` | `vertex` (opciono; ako izostane, sistem bira na osnovu konfiguracije)
  - `model`: npr. `gemini-2.5-pro` (opciono; koristi se i za simulaciju greške)
  - `chunk_size`, `delay_ms`: kontrola dužine i kašnjenja po chunk-u
- Sekvenca događaja:
  - `event: start` – inicijalni blok sa meta informacijama
  - `event: fallback` – emituje se samo ako dođe do preusmeravanja (npr. Vertex → GENAI ili → sim)
  - `data: { ... }` – chunk-ovi odgovora (više puta)
  - `: X-Stream-Duration: <ms>` – SSE komentar, ukupno trajanje stream-a u ms
  - `: X-Stream-Chunks: <n>` – SSE komentar, broj emitovanih chunk-ova
  - `event: metrics` – JSON blok sa istim vrednostima kao komentari + izvor/model
  - `event: done` – završni blok sa sažetkom (chunks, duration)

Metrike i health:
- `/healthz` i `/readyz` vraćaju `sse_metrics`:
  - `started` – broj pokrenutih SSE tokova
  - `done` – broj uspešno završenih SSE tokova
  - `errors` – broj grešaka (npr. Vertex init/stream greška)
  - `fallback` – broj preusmeravanja (Vertex → GENAI/sim, ili GENAI → sim)

Primeri (Windows PowerShell / CMD):
- Duži SSE capture (simulacija):
  - `curl.exe --no-buffer "http://localhost:8082/api/gcp/gemini/stream?source=sim&prompt=Produzi%20SSE%20simulaciju%20sa%20komentarima"`
- Kontrolisana Vertex greška + fallback ka GENAI:
  - `curl.exe --no-buffer "http://localhost:8082/api/gcp/gemini/stream?prompt=Vertex%20error%20probe&model=gemini-nonexistent-model-xyz"`
- Provera metrika:
  - `curl.exe "http://localhost:8082/healthz"`

Napomene o produkcionom režimu:
- `OMNI_PROD_STRICT=true` – strogi režim (fail-fast) sa deadline-om za prvi chunk.
- `OMNI_STRICT_FIRST_CHUNK_MS=1200` – maksimalno vreme za prvi chunk pre fallback-a.
- U oba slučaja, komentari i `event: metrics` se emituju neposredno pre `event: done`.