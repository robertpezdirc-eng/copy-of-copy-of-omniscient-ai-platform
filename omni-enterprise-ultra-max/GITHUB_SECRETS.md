# GitHub Actions Secrets Configuration

To enable the frontend CI/CD pipeline (`.github/workflows/frontend-deploy.yml`), add these secrets to your GitHub repository:

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

### 3. `VITE_API_URL_STAGING`
Backend API URL for the staging environment.

**Value:**
```
https://omni-ultra-backend-staging-guzjyv6gfa-ew.a.run.app
```

### 4. `VITE_API_URL_PROD`
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

After adding secrets, the workflow will automatically trigger on the next push to `master` that modifies:
- `frontend/**`
- `.github/workflows/frontend-deploy.yml`
- `cloudbuild-frontend-simple.yaml`

You can also manually trigger it from the Actions tab.
