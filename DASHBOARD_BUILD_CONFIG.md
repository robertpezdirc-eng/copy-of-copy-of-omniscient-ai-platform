# Dashboard Build Configuration - GitHub Only (No Cloud Deploy)

## Current Setup

**Status:** Cloud Run deployment is **DISABLED** to avoid costs during development.

### Active Configuration
✅ **GitHub Actions** - Build-only workflow (`.github/workflows/build-dashboard-only.yml`)
- Builds Docker image on every push
- **NO deployment** to Cloud Run
- **NO costs** - only GitHub Actions minutes (free tier available)

### Disabled Configurations
❌ **Cloud Build** - Disabled to prevent Google Cloud costs
- `cloudbuild.dashboard.yaml.DISABLED` - Full build + deploy (was costing money)
- `cloudbuild.dashboard.build-only.yaml.DISABLED` - Build without deploy

❌ **GitHub Actions Cloud Run Deploy** - Disabled to prevent deployment
- `.github/workflows/deploy-cloudrun-dashboard.yml.DISABLED` - Deployed to Cloud Run

---

## How It Works Now

### On Every Push to GitHub
1. GitHub Actions automatically builds the Docker image
2. Image is built locally in GitHub runners
3. **NO push to container registry**
4. **NO deployment to Cloud Run**
5. **Result: $0 cost** (only uses free GitHub Actions minutes)

### Workflow File
Location: `.github/workflows/build-dashboard-only.yml`

Triggers on:
- Push to `main`, `develop`, or `copilot/*` branches
- Changes to dashboard files
- Manual trigger via workflow_dispatch

---

## Cost Comparison

| Method | Monthly Cost | When to Use |
|--------|-------------|-------------|
| **Current (GitHub build-only)** | **$0** | ✅ Development, testing |
| Cloud Build (disabled) | ~$0.04-0.08 per build | When you need GCR image |
| Cloud Run (disabled) | ~$1-5/month | Only when deploying to production |

---

## Re-enabling Cloud Deployment (When Ready for Production)

### Option 1: Re-enable GitHub Actions Cloud Run Deploy
```bash
# Rename to remove .DISABLED suffix
mv .github/workflows/deploy-cloudrun-dashboard.yml.DISABLED \
   .github/workflows/deploy-cloudrun-dashboard.yml
```

### Option 2: Re-enable Cloud Build
```bash
# For full build + deploy
mv cloudbuild.dashboard.yaml.DISABLED cloudbuild.dashboard.yaml

# Or for build-only (no deploy)
mv cloudbuild.dashboard.build-only.yaml.DISABLED \
   cloudbuild.dashboard.build-only.yaml
```

### Option 3: Use Cloud Build Manually (One-time)
```bash
# Build and deploy once
gcloud builds submit --config=cloudbuild.dashboard.yaml.DISABLED

# Or just build
gcloud builds submit --config=cloudbuild.dashboard.build-only.yaml.DISABLED
```

---

## Local Development

You can also build and test completely locally (100% free):

```bash
# Build locally
docker build -f Dockerfile.dashboard -t omni-dashboard:dev .

# Run locally
docker run -p 8080:8080 \
  -e USE_OLLAMA=true \
  -e OLLAMA_URL=https://ollama-661612368188.europe-west1.run.app \
  -e OLLAMA_MODEL=llama3.2 \
  omni-dashboard:dev

# Test
curl http://localhost:8080/health
```

---

## What Was Disabled and Why

### Files Disabled
1. `cloudbuild.dashboard.yaml.DISABLED` 
   - Previously: Built and deployed to Cloud Run automatically
   - Cost: ~$0.04-0.08 per build + Cloud Run runtime costs
   - Disabled because: User requested no Cloud Run deployment during development

2. `cloudbuild.dashboard.build-only.yaml.DISABLED`
   - Previously: Built image and pushed to GCR (no deploy)
   - Cost: ~$0.04-0.08 per build
   - Disabled because: GitHub Actions provides free alternative

3. `.github/workflows/deploy-cloudrun-dashboard.yml.DISABLED`
   - Previously: Built and deployed to Cloud Run via GitHub Actions
   - Cost: Cloud Run runtime costs (~$1-5/month)
   - Disabled because: User wants zero Cloud Run costs

### Files Active
1. `.github/workflows/build-dashboard-only.yml` ✅
   - Builds Docker image in GitHub Actions
   - NO deployment, NO registry push
   - Cost: $0 (uses free GitHub Actions minutes)

---

## Monitoring Costs

Even with everything disabled, check for:
- **Existing Cloud Run services** - Delete them to stop costs
- **Container images in GCR** - Delete old images to save storage costs
- **Other services** - Check Compute Engine, Cloud SQL, etc.

```bash
# Check what's running
gcloud run services list
gcloud compute instances list
gcloud sql instances list

# Delete dashboard if deployed
gcloud run services delete omni-dashboard --region=europe-west1
```

---

## Summary

✅ **GitHub Actions build-only** is active (no costs)
❌ **All Cloud Run deployment** is disabled (no costs)
📝 **Configuration files preserved** (can re-enable when needed)

**Current cost: $0/month for dashboard building** 🎉
