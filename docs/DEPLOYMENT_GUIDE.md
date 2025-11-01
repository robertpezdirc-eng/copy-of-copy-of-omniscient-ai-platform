# 🚀 OMNI Platform - Deployment Guide

Complete guide for deploying the OMNI Intelligence Platform to various environments.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Deployment Options](#deployment-options)
- [Environment Configuration](#environment-configuration)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Docker & Docker Compose** (v20.10+)
- **Python** 3.9+ 
- **Node.js** 14+ (optional)
- **Git**

### For Cloud Run Deployment

- **Google Cloud SDK** (`gcloud` CLI)
- **GCP Project** with billing enabled
- **Container Registry API** enabled

### For GitHub Pages Deployment

- **GitHub Account** with repository access
- **SSH Key** configured for GitHub

## 🎯 Quick Start

### Local Development (Docker)

```bash
# Clone repository
git clone https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform.git
cd copy-of-copy-of-omniscient-ai-platform

# Deploy with Docker
./scripts/deploy/deploy-docker.sh

# Access the platform
open http://localhost:8000/omni-dashboard.html
```

### Using Master Deployment Script

```bash
cd scripts/deploy
./deploy-all.sh
```

This opens an interactive menu with all deployment options.

## 🌐 Deployment Options

### 1. Docker Deployment (Local/Development)

**Use Case**: Local development, testing, demos

```bash
./scripts/deploy/deploy-docker.sh
```

**Services Started**:
- Frontend: http://localhost:8000
- Backend: http://localhost:8080
- API Docs: http://localhost:8080/docs

**Configuration**: `docker-compose.yml`

**Logs**:
```bash
docker-compose logs -f
```

**Stop**:
```bash
docker-compose down
```

### 2. Google Cloud Run (Production)

**Use Case**: Production deployment with auto-scaling

```bash
./scripts/deploy/deploy-cloud-run.sh
```

**Prerequisites**:
```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash

# Authenticate
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

**Environment Variables**:
- `GCP_PROJECT_ID`: Your GCP project ID
- `GCP_REGION`: Deployment region (default: `europe-west1`)

**Services Deployed**:
- `omni-frontend`: Static frontend
- `omni-backend`: FastAPI backend

**Monitoring**:
```bash
# View services
gcloud run services list --region europe-west1

# View logs
gcloud run services logs read omni-frontend --region europe-west1
gcloud run services logs read omni-backend --region europe-west1

# Check metrics
gcloud run services describe omni-frontend --region europe-west1
```

### 3. GitHub Pages (Static Hosting)

**Use Case**: Static frontend hosting, documentation

```bash
./scripts/deploy/deploy-github-pages.sh
```

**Prerequisites**:
- Repository write access
- SSH key configured

**Setup**:
1. Run deployment script
2. Go to repository Settings → Pages
3. Select `gh-pages` branch as source
4. Save

**URL**: `https://robertpezdirc-eng.github.io/copy-of-copy-of-omniscient-ai-platform/`

**Note**: Backend must be deployed separately (Cloud Run recommended)

## ⚙️ Environment Configuration

### Frontend Configuration (`frontend/env.js`)

```javascript
window.ENV = {
    API_BASE_URL: 'http://localhost:8080',  // Backend URL
    AI_GATEWAY_URL: 'https://ai-gateway-661612368188.europe-west1.run.app'
};
```

### Backend Configuration (`.env`)

```bash
# AI Gateway
AI_GATEWAY_URL=https://ai-gateway-661612368188.europe-west1.run.app

# CORS
CORS_ORIGINS=http://localhost:8000,https://yourdomain.com

# Database (optional)
DATABASE_URL=postgresql://user:pass@host:5432/omni

# Redis (optional)
REDIS_URL=redis://localhost:6379/0
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
services:
  frontend:
    build: ./frontend
    ports:
      - "8000:8000"
    environment:
      - API_BASE_URL=http://backend:8080
  
  backend:
    build: ./backend
    ports:
      - "8080:8080"
    environment:
      - AI_GATEWAY_URL=${AI_GATEWAY_URL}
```

## 🔍 Health Checks

### Manual Health Check

```bash
# Backend health
curl http://localhost:8080/health

# Modules API
curl http://localhost:8080/api/modules

# Frontend
curl http://localhost:8000
```

### Automated Health Check

```bash
./scripts/deploy/health-check.sh
```

Output:
```
🏥 OMNI Platform - Health Check
===============================

🐳 Docker Services:
Checking Frontend         ✅ OK (200)
Checking Backend Health   ✅ OK (200)
Checking Backend API      ✅ OK (200)

☁️  Cloud Run Services:
Checking Frontend         ✅ OK (200)
Checking Backend Health   ✅ OK (200)
```

## 🔄 Rollback

### Automatic Rollback

```bash
./scripts/deploy/rollback.sh
```

Options:
1. **Docker**: Restarts previous container versions
2. **Cloud Run**: Reverts to previous revision (100% traffic)

### Manual Rollback

**Docker**:
```bash
docker-compose down
docker-compose up -d
```

**Cloud Run**:
```bash
# List revisions
gcloud run revisions list --service omni-backend --region europe-west1

# Rollback to specific revision
gcloud run services update-traffic omni-backend \
  --to-revisions=omni-backend-00002-abc=100 \
  --region europe-west1
```

## 📊 Monitoring & Logs

### Docker Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f frontend
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Cloud Run Logs

```bash
# Real-time logs
gcloud run services logs tail omni-backend --region europe-west1

# Last hour
gcloud run services logs read omni-backend \
  --region europe-west1 \
  --limit=100 \
  --format="table(timestamp,severity,textPayload)"

# Filter by severity
gcloud run services logs read omni-backend \
  --region europe-west1 \
  --log-filter="severity>=ERROR"
```

### Metrics

**Cloud Run Console**:
- Go to: https://console.cloud.google.com/run
- Select service
- View: Request count, latency, errors, CPU, memory

**Custom Metrics**:
```bash
# Backend metrics endpoint
curl http://localhost:8080/metrics
```

## 🔒 Security

### HTTPS/SSL

**Cloud Run**: Automatic HTTPS with Google-managed certificates

**Custom Domain**:
```bash
gcloud run domain-mappings create \
  --service omni-frontend \
  --domain omni.yourdomain.com \
  --region europe-west1
```

### Secrets Management

**Cloud Run**:
```bash
# Create secret
echo -n "your-secret-value" | gcloud secrets create omni-api-key --data-file=-

# Use in deployment
gcloud run services update omni-backend \
  --update-secrets=API_KEY=omni-api-key:latest \
  --region europe-west1
```

### Authentication

**Backend API**:
- Implement API keys in `backend/auth.py`
- Add middleware to FastAPI

**Frontend**:
- Configure in `frontend/auth.js`
- Store tokens in localStorage

## 🧪 Testing Deployment

### Pre-Deployment Tests

```bash
# Run smoke tests
./test_omni_platform.sh

# Check all services
./scripts/deploy/health-check.sh
```

### Post-Deployment Validation

```bash
# Frontend accessibility
curl -I https://your-frontend-url.run.app

# Backend API
curl https://your-backend-url.run.app/api/modules

# Module pages
curl https://your-frontend-url.run.app/modules/sales.html
```

## 📝 Deployment Checklist

### Pre-Deployment

- [ ] Update version in `package.json`
- [ ] Run tests (`./test_omni_platform.sh`)
- [ ] Update environment variables
- [ ] Review configuration files
- [ ] Backup database (if applicable)
- [ ] Create git tag for release

### Deployment

- [ ] Run deployment script
- [ ] Monitor deployment logs
- [ ] Verify health checks pass
- [ ] Test critical paths
- [ ] Check all module pages load

### Post-Deployment

- [ ] Update documentation
- [ ] Notify team/users
- [ ] Monitor error rates
- [ ] Check performance metrics
- [ ] Document any issues

## 🆘 Troubleshooting

### Common Issues

**Problem**: Docker containers won't start
```bash
# Solution: Clean up and rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

**Problem**: Cloud Run deployment fails
```bash
# Solution: Check quotas and permissions
gcloud projects describe YOUR_PROJECT_ID
gcloud run services list --region europe-west1

# Increase memory if needed
gcloud run services update omni-backend \
  --memory 1Gi \
  --region europe-west1
```

**Problem**: Module pages 404 error
```bash
# Solution: Verify files exist
ls -la frontend/modules/
python3 scripts/generate_module_pages.py
```

**Problem**: Backend can't connect to AI Gateway
```bash
# Solution: Check environment variable
echo $AI_GATEWAY_URL

# Test connectivity
curl https://ai-gateway-661612368188.europe-west1.run.app/health
```

### Debug Mode

**Enable verbose logging**:

Backend:
```python
# backend/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

Frontend:
```javascript
// frontend/env.js
window.ENV = {
    DEBUG: true,
    // ...
};
```

### Getting Help

- **GitHub Issues**: https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform/issues
- **Documentation**: See `docs/` directory
- **Logs**: Check deployment logs for specific errors

## 📚 Additional Resources

- [MODULE_REFERENCE.md](MODULE_REFERENCE.md) - Complete module documentation
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - API endpoints reference
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture overview
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Detailed troubleshooting guide

## 🎯 Best Practices

1. **Always test locally first** using Docker deployment
2. **Use environment variables** for configuration
3. **Monitor logs** after deployment
4. **Keep rollback script** ready
5. **Document changes** in git commits
6. **Use semantic versioning** for releases
7. **Automate** with CI/CD when possible

## 📈 Performance Optimization

### Frontend

- Enable gzip compression
- Minimize CSS/JS files
- Use CDN for static assets
- Implement lazy loading

### Backend

- Enable response caching
- Use connection pooling
- Optimize database queries
- Implement rate limiting

### Cloud Run

```bash
# Optimize Cold Starts
gcloud run services update omni-backend \
  --min-instances 1 \
  --region europe-west1

# Increase Resources
gcloud run services update omni-backend \
  --memory 2Gi \
  --cpu 2 \
  --region europe-west1
```

## 🔧 Maintenance

### Regular Tasks

- **Weekly**: Review logs for errors
- **Monthly**: Update dependencies
- **Quarterly**: Performance review
- **Yearly**: Architecture assessment

### Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild and redeploy
./scripts/deploy/deploy-docker.sh
```

---

**Version**: 1.0.0  
**Last Updated**: 2025-11-01  
**Maintained by**: OMNI Platform Team
