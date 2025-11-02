# GitHub Actions Secrets Configuration

This repo includes GitHub Actions workflows for frontend deploys, gateway smoke tests, and Cloud Run backend deploys. Configure the secrets below in your repository.

## Required Secrets

### 1. `GCP_PROJECT_ID`
Your Google Cloud Project ID.

**Value:**
```
refined-graph-471712-n9
```

### 2. `GCP_SA_KEY`
JSON service account key with Cloud Build and Cloud Run permissions.

**How to create:**
```bash
# Create a service account
gcloud iam service-accounts create github-actions-deploy \
  --display-name="GitHub Actions Deployer" \
  --project=refined-graph-471712-n9

# Grant necessary roles
gcloud projects add-iam-policy-binding refined-graph-471712-n9 \
  --member="serviceAccount:github-actions-deploy@refined-graph-471712-n9.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding refined-graph-471712-n9 \
  --member="serviceAccount:github-actions-deploy@refined-graph-471712-n9.iam.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.editor"

gcloud projects add-iam-policy-binding refined-graph-471712-n9 \
  --member="serviceAccount:github-actions-deploy@refined-graph-471712-n9.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding refined-graph-471712-n9 \
  --member="serviceAccount:github-actions-deploy@refined-graph-471712-n9.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Create and download key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions-deploy@refined-graph-471712-n9.iam.gserviceaccount.com

# Copy the entire contents of github-actions-key.json to the GitHub secret
```

**Value:** Paste the entire JSON key file content.

### 3. `GCP_REGION`
Google Cloud region for Cloud Run.

**Value:**
```
europe-west1
```

### 4. `CLOUD_RUN_SERVICE_BACKEND`
Cloud Run service name for the backend (used by deploy workflow).

**Value:**
```
omni-ultra-backend
```

### 5. `GATEWAY_URL`
Gateway base URL used by the smoke test workflow.

**Value:**
```
https://ai-gateway-661612368188.europe-west1.run.app
```

### 6. `GATEWAY_TOKEN`
Bearer token for the gateway (must match API_KEYS configured on the gateway service).

**Value:**
```
prod-key-omni-2025
```

### 7. `CLOUD_RUN_SERVICE_GATEWAY`
Cloud Run service name for the gateway.

**Value:**
```
ai-gateway
```

### 8. `GATEWAY_UPSTREAM_URL`
Backend URL used when deploying gateway (for UPSTREAM_URL env).

**Value:**
```
https://omni-ultra-backend-661612368188.europe-west1.run.app
```

### 9. `VITE_API_URL_STAGING`
Backend API URL for the staging environment.

**Value:**
```
https://omni-ultra-backend-staging-guzjyv6gfa-ew.a.run.app
```

### 10. `VITE_API_URL_PROD`
Backend API URL for the production environment.

**Value:**
```
https://omni-ultra-backend-prod-guzjyv6gfa-ew.a.run.app
```

## How to Add Secrets to GitHub

1. Go to your repository: https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with the name and value from above

## Verification

### Frontend Deploy Workflow
Triggers on push to `master` that modifies:
- `frontend/**`
- `.github/workflows/frontend-deploy.yml`
- `cloudbuild-frontend-simple.yaml`

### Gateway Smoke Workflow
- Workflow file: `.github/workflows/smoke-gateway.yml`
- Triggers hourly and on manual dispatch.
- Produces an artifact named `smoke-openai-gateway-report`.

### Minimal Backend Deploy Workflow
- Workflow file: `.github/workflows/deploy-minimal-backend.yml`
- Trigger manually from the Actions tab.
- Builds via Cloud Build and deploys to Cloud Run using the configured secrets.

### Gateway Deploy Workflow
- Workflow file: `.github/workflows/deploy-gateway.yml`
- Triggers on push to `gateway/**` and on manual dispatch.
- Performs Cloud Run source deploy of the gateway with env vars.
