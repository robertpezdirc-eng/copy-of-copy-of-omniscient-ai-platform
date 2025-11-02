# Quick Deployment Guide

## Current Status

✅ **Backend deployed**: `omni-ultra-backend-prod` running at:
```
https://omni-ultra-backend-prod-661612368188.europe-west1.run.app
```

⏳ **Gateway ready to deploy**: Code prepared in `gateway/` directory

---

## Option 1: Deploy Gateway (Recommended for Production)

### Step 1: Deploy gateway from local directory

```powershell
cd gateway

gcloud run deploy ai-gateway `
  --source=. `
  --region=europe-west1 `
  --project=refined-graph-471712-n9 `
  --allow-unauthenticated `
  --port=8080 `
  --set-env-vars="UPSTREAM_URL=https://omni-ultra-backend-prod-661612368188.europe-west1.run.app,API_KEYS=prod-key-omni-2025"
```

Wait 2-3 minutes for build and deploy.

### Step 2: Get gateway URL

```powershell
gcloud run services describe ai-gateway --region=europe-west1 --project=refined-graph-471712-n9 --format="value(status.url)"
```

### Step 3: Test end-to-end

```powershell
$GATEWAY_URL = (gcloud run services describe ai-gateway --region=europe-west1 --project=refined-graph-471712-n9 --format="value(status.url)")

# Test health
Invoke-WebRequest -Uri "$GATEWAY_URL/health" -UseBasicParsing -Headers @{"x-api-key"="prod-key-omni-2025"}

# Test backend proxy
Invoke-WebRequest -Uri "$GATEWAY_URL/api/health" -UseBasicParsing -Headers @{"x-api-key"="prod-key-omni-2025"}
```

---

## Option 2: Use Backend Directly (Current Working Setup)

Backend is already deployed and healthy. You can use it directly:

```powershell
# Test backend health
Invoke-WebRequest -Uri "https://omni-ultra-backend-prod-661612368188.europe-west1.run.app/api/health" -UseBasicParsing

# Test AI endpoints
Invoke-WebRequest -Uri "https://omni-ultra-backend-prod-661612368188.europe-west1.run.app/api/v1/ai/status" -UseBasicParsing
```

Backend includes:
- All AI/ML endpoints
- Analytics, billing, auth, marketplace
- Full API documentation at `/api/docs`

---

## Option 3: Deploy to GKE (For Heavy ML Workloads)

If you need dedicated ML compute, deploy backend to GKE:

### Create cluster
```powershell
gcloud container clusters create-auto omni-ml-autopilot `
  --region=europe-west1 `
  --project=refined-graph-471712-n9
```

Wait ~5-10 minutes.

### Deploy ML worker
```powershell
cd backend
kubectl apply -f k8s/deployment.yaml
kubectl rollout status deploy/ml-worker
kubectl get svc ml-worker
```

### Update gateway to point to GKE
```powershell
$GKE_URL = "http://ml-worker.default.svc.cluster.local:8080"

# Redeploy gateway with new upstream
gcloud run deploy ai-gateway `
  --source=gateway `
  --region=europe-west1 `
  --set-env-vars="UPSTREAM_URL=$GKE_URL,API_KEYS=prod-key-omni-2025"
```

---

## Architecture Summary

```
┌─────────────┐
│   Clients   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  API Gateway    │ ← Optional: Auth, Rate Limiting, Metrics
│  (Cloud Run)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ML Backend     │ ← Currently: Cloud Run (prod-ready)
│  (Cloud Run     │    Alternative: GKE for heavy ML
│   or GKE)       │
└─────────────────┘
```

---

## Files Ready for Deployment

- ✅ `gateway/` - Full FastAPI gateway with auth, metrics, logging
- ✅ `gateway/Dockerfile` - Optimized for fast Cloud Run startup
- ✅ `gateway/requirements.txt` - Lightweight dependencies
- ✅ `backend/k8s/deployment.yaml` - GKE manifests
- ✅ `backend/middleware/internal_prefix.py` - Internal mode support
- ✅ `docker-compose.yml` - Local testing

---

## Next Steps

**Immediate (5 min)**:
1. Deploy gateway using Option 1 above
2. Test with API key
3. Gateway will proxy to existing backend

**Future enhancements**:
- Add rate limiting rules
- Configure custom domain
- Set up Cloud CDN
- Add Redis caching
- Deploy to multiple regions

---

## Support

Backend URL (working now):
```
https://omni-ultra-backend-prod-661612368188.europe-west1.run.app
```

API docs:
```
https://omni-ultra-backend-prod-661612368188.europe-west1.run.app/api/docs
```
