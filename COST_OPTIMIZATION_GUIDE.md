# Google Cloud Cost Optimization Guide - DEVELOPMENT PHASE

## 🎯 ZERO COST DEVELOPMENT MODE

When you're **just building/testing** and not running in production:

### Option 1: Build Locally (100% FREE)
```bash
# Build Docker image locally - NO CLOUD COSTS
docker build -f Dockerfile.dashboard -t omni-dashboard:dev .

# Test locally - NO CLOUD COSTS
docker run -p 8080:8080 omni-dashboard:dev
```

### Option 2: Build Only in Cloud (Minimal Cost ~$0.04-0.08 per build)
```bash
# Build and push image WITHOUT deploying to Cloud Run
gcloud builds submit --config=cloudbuild.dashboard.build-only.yaml

# Result: Image in GCR, but NO Cloud Run service = NO ongoing costs
```

### Option 3: Build + Deploy (Current Setup - Near Zero Cost)
```bash
# Build and deploy with minimal configuration
gcloud builds submit --config=cloudbuild.dashboard.yaml

# Cost: Only when service is actually used (scales to zero when idle)
```

---

## 💰 COST BREAKDOWN

### BUILD COSTS (One-time per build)
| Machine Type | Cost per Build | Recommended |
|--------------|----------------|-------------|
| N1_HIGHCPU_2 | ~$0.04-0.08 | ✅ Development |
| N1_HIGHCPU_4 | ~$0.08-0.15 | Production |
| E2_HIGHCPU_8 | ~$0.15-0.30 | ❌ Too expensive |

### CLOUD RUN COSTS (Ongoing if deployed)
**Current Configuration (ABSOLUTE MINIMUM):**
- Memory: 256Mi (minimum allowed)
- Min instances: 0 (scales to zero)
- Max instances: 1 (single instance)
- Concurrency: 10 (low)

**Cost When Idle:** $0/month ✅
**Cost When Used:** ~$0.01-0.02/hour
**Realistic Dev Usage:** $1-5/month ✅

---

## 🚫 HOW TO AVOID ALL CLOUD RUN COSTS DURING DEVELOPMENT

### Method 1: Don't Deploy (Recommended for Development)
```bash
# Only build, don't deploy
gcloud builds submit --config=cloudbuild.dashboard.build-only.yaml
```

### Method 2: Delete Service After Testing
```bash
# Deploy for testing
gcloud builds submit --config=cloudbuild.dashboard.yaml

# Delete service when done (stops all costs)
gcloud run services delete omni-dashboard --region=europe-west1
```

### Method 3: Build Everything Locally
```bash
# Build locally (free)
docker build -f Dockerfile.dashboard -t omni-dashboard:dev .

# Test locally (free)
docker run -p 8080:8080 omni-dashboard:dev

# Only push to GCR when ready (no Cloud Run deployment)
docker tag omni-dashboard:dev gcr.io/PROJECT_ID/omni-dashboard:dev
docker push gcr.io/PROJECT_ID/omni-dashboard:dev
```

---

## ⚠️ COMMON COST PITFALLS TO AVOID

### 1. Services Running Idle
**Problem:** Deployed services consuming resources even when not used
**Solution:** Use min-instances=0 (done ✅) or delete service when not needed

### 2. Multiple Instances
**Problem:** Multiple instances running simultaneously
**Solution:** Set max-instances=1 (done ✅)

### 3. High Memory Allocation
**Problem:** Allocating more memory than needed
**Solution:** Use 256Mi minimum (done ✅)

### 4. Large Build Machines
**Problem:** Using expensive build machines
**Solution:** Use N1_HIGHCPU_2 (done ✅)

### 5. Not Using Free Tier
**Problem:** Not leveraging GCP free tier
**Solution:** 
- Cloud Run: 2M requests/month FREE
- Cloud Build: 120 build-minutes/day FREE
- GCR Storage: First 0.5GB FREE

---

## 📊 COST COMPARISON

### Before Optimization
- Memory: 1Gi
- Max instances: 3
- Build machine: E2_HIGHCPU_8
- **Cost:** ~$93/month + ~$0.30/build

### After First Optimization
- Memory: 512Mi
- Max instances: 1
- Build machine: N1_HIGHCPU_4
- **Cost:** ~$5-15/month + ~$0.08/build

### Current (ABSOLUTE MINIMUM)
- Memory: 256Mi
- Max instances: 1
- Min instances: 0
- Build machine: N1_HIGHCPU_2
- **Cost:** ~$1-5/month + ~$0.04/build

### Development Mode (BUILD ONLY)
- No Cloud Run deployment
- Build machine: N1_HIGHCPU_2
- **Cost:** ~$0.04-0.08 per build only

---

## 🎓 RECOMMENDATIONS FOR YOUR SITUATION

You mentioned:
- Just building/developing (not in production)
- Got charged 5000+ euros
- Want zero costs

### Immediate Actions:

1. **Check what's running:**
```bash
# List all Cloud Run services
gcloud run services list

# Check if dashboard is deployed and consuming costs
gcloud run services describe omni-dashboard --region=europe-west1
```

2. **Delete unused services:**
```bash
# Delete dashboard if not needed right now
gcloud run services delete omni-dashboard --region=europe-west1

# This stops ALL Cloud Run costs immediately
```

3. **For development, use build-only mode:**
```bash
# Only build, don't deploy
gcloud builds submit --config=cloudbuild.dashboard.build-only.yaml
```

4. **Check for OTHER services causing costs:**
```bash
# List ALL services in your project
gcloud run services list --platform=managed
gcloud compute instances list
gcloud sql instances list

# These might be the source of your $5000+ bill
```

---

## 🔍 FINDING THE $5000 COST SOURCE

Your dashboard alone wouldn't cause $5000 costs. Check:

1. **Cloud Run services:** Multiple services running 24/7
2. **Compute Engine VMs:** Expensive VM instances
3. **Cloud SQL:** Database instances
4. **Vertex AI:** AI model training/serving
5. **BigQuery:** Large data processing
6. **Cloud Storage:** Huge storage costs
7. **Networking:** High egress traffic

**Check your billing:**
```bash
# See detailed billing breakdown
gcloud billing accounts list
# Then go to: https://console.cloud.google.com/billing
```

---

## ✅ FINAL RECOMMENDATION

**For zero-cost development:**
1. Use `cloudbuild.dashboard.build-only.yaml` (no deployment)
2. Or build locally with Docker (completely free)
3. Delete any deployed Cloud Run services you don't need
4. Investigate what caused the $5000 bill (likely other services)

The dashboard configuration is now at absolute minimum. Any further reduction would make it non-functional.
