# GitHub Secrets Setup Guide

## Required Secrets for CI/CD

The GitHub Actions workflow (`.github/workflows/deploy.yml`) requires the following secrets to be configured in your repository.

---

## 1. Configure GitHub Secrets

Go to: **Repository → Settings → Secrets and variables → Actions → New repository secret**

### `GCP_PROJECT_ID`
**Value:** Your Google Cloud project ID
```
refined-graph-471712-n9
```

### `GCP_SA_KEY`
**Value:** Service account JSON key with permissions:
- Cloud Run Admin
- Service Account User
- Artifact Registry Writer
- Storage Admin (for Cloud Build logs)

**How to create:**
```bash
# Create service account
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions CI/CD"

# Grant required roles
gcloud projects add-iam-policy-binding refined-graph-471712-n9 \
  --member="serviceAccount:github-actions@refined-graph-471712-n9.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding refined-graph-471712-n9 \
  --member="serviceAccount:github-actions@refined-graph-471712-n9.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding refined-graph-471712-n9 \
  --member="serviceAccount:github-actions@refined-graph-471712-n9.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding refined-graph-471712-n9 \
  --member="serviceAccount:github-actions@refined-graph-471712-n9.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# Create and download key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions@refined-graph-471712-n9.iam.gserviceaccount.com

# Copy the entire JSON content to GitHub secret
cat github-actions-key.json
```

**⚠️ Security:** Delete the local key file after copying:
```bash
rm github-actions-key.json
```

### `GATEWAY_API_KEYS`
**Value:** Comma-separated list of API keys for gateway authentication
```
prod-key-abc123,dev-key-xyz789,test-key-quicktest
```

**Generate secure keys:**
```bash
# macOS/Linux
openssl rand -base64 32

# PowerShell
[System.Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
```

---

## 2. Verify Secrets

After adding secrets, verify they're configured:

```bash
# List secrets (GitHub CLI)
gh secret list

# Expected output:
# GCP_PROJECT_ID     Updated ...
# GCP_SA_KEY         Updated ...
# GATEWAY_API_KEYS   Updated ...
```

---

## 3. Test Workflow

### Manual Trigger
```bash
# Via GitHub CLI
gh workflow run deploy.yml

# Via UI: Actions tab → Deploy to Google Cloud Run → Run workflow
```

### Automatic Trigger
Push to `main` or `develop` branch:
```bash
git checkout main
git commit --allow-empty -m "Trigger deployment"
git push origin main
```

---

## 4. Monitor Deployment

### GitHub Actions UI
1. Go to **Actions** tab
2. Click on latest workflow run
3. Monitor jobs: test → build-and-deploy-backend → build-and-deploy-gateway → build-and-deploy-frontend → smoke-tests

### Expected Output
```
✅ Tests: success
✅ Backend: success
✅ Gateway: success
✅ Frontend: success
✅ Smoke Tests: success

Deployments:
- Backend: https://omni-ultra-backend-guzjyv6gfa-ew.a.run.app
- Gateway: https://ai-gateway-guzjyv6gfa-ew.a.run.app
- Frontend: https://omni-frontend-guzjyv6gfa-ew.a.run.app
```

---

## 5. Troubleshooting

### Issue: "Permission denied" during deployment
**Cause:** Service account lacks required roles.

**Fix:**
```bash
# Grant missing role (example)
gcloud projects add-iam-policy-binding refined-graph-471712-n9 \
  --member="serviceAccount:github-actions@refined-graph-471712-n9.iam.gserviceaccount.com" \
  --role="roles/run.admin"
```

### Issue: "Invalid credentials"
**Cause:** `GCP_SA_KEY` secret is malformed.

**Fix:**
1. Regenerate service account key
2. Copy **entire JSON** content (no line breaks or formatting changes)
3. Update GitHub secret

### Issue: "Service not found" during smoke tests
**Cause:** Service names don't match in workflow env vars.

**Fix:** Verify service names:
```bash
gcloud run services list --region europe-west1
```

Update `.github/workflows/deploy.yml` env vars:
```yaml
env:
  BACKEND_SERVICE: omni-ultra-backend
  GATEWAY_SERVICE: ai-gateway
  FRONTEND_SERVICE: omni-frontend
```

### Issue: "Image not found"
**Cause:** Artifact Registry repository doesn't exist.

**Fix:**
```bash
# Create Artifact Registry repository
gcloud artifacts repositories create omni \
  --repository-format=docker \
  --location=europe-west1 \
  --description="Omni Enterprise Ultra Max container images"
```

---

## 6. Security Best Practices

1. **Rotate service account keys regularly**
   ```bash
   # Delete old keys
   gcloud iam service-accounts keys list \
     --iam-account=github-actions@refined-graph-471712-n9.iam.gserviceaccount.com
   
   gcloud iam service-accounts keys delete KEY_ID \
     --iam-account=github-actions@refined-graph-471712-n9.iam.gserviceaccount.com
   
   # Create new key
   gcloud iam service-accounts keys create new-key.json \
     --iam-account=github-actions@refined-graph-471712-n9.iam.gserviceaccount.com
   ```

2. **Use environment-specific secrets**
   - `GCP_SA_KEY_PROD` for production
   - `GCP_SA_KEY_DEV` for development

3. **Limit service account permissions**
   - Only grant roles needed for deployment
   - Use separate SAs for different environments

4. **Monitor secret access**
   ```bash
   # Audit service account activity
   gcloud logging read "protoPayload.authenticationInfo.principalEmail=github-actions@refined-graph-471712-n9.iam.gserviceaccount.com" \
     --limit 50 \
     --format json
   ```

---

## 7. Additional Secrets (Optional)

### `OPENAI_API_KEY` (for backend AI features)
```bash
# Add to GitHub secrets
OPENAI_API_KEY=sk-...
```

Then update workflow to set env var:
```yaml
- name: Deploy Backend to Cloud Run
  run: |
    gcloud run deploy ${{ env.BACKEND_SERVICE }} \
      ... \
      --set-env-vars OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }}
```

### `GEMINI_API_KEY` (for Google Gemini)
```bash
GEMINI_API_KEY=...
```

### `REDIS_URL` (if using external Redis)
```bash
REDIS_URL=redis://user:pass@host:6379/0
```

---

## 8. Workflow Customization

### Change Deployment Regions
Edit `.github/workflows/deploy.yml`:
```yaml
env:
  GCP_REGION: us-central1  # Change from europe-west1
```

### Add Environment Variables
```yaml
- name: Deploy Backend to Cloud Run
  run: |
    gcloud run deploy ${{ env.BACKEND_SERVICE }} \
      ... \
      --set-env-vars KEY1=value1 \
      --set-env-vars KEY2=value2
```

### Conditional Deployments
```yaml
# Only deploy on main branch
if: github.ref == 'refs/heads/main'

# Skip PRs
if: github.event_name == 'push'
```

---

## Summary Checklist

- [ ] Create `github-actions` service account
- [ ] Grant required IAM roles
- [ ] Generate and download JSON key
- [ ] Add `GCP_PROJECT_ID` secret
- [ ] Add `GCP_SA_KEY` secret (full JSON)
- [ ] Add `GATEWAY_API_KEYS` secret
- [ ] Delete local key file
- [ ] Test workflow with manual trigger
- [ ] Verify deployment in Actions tab
- [ ] Check deployed services via URLs

---

**Next:** Push to `main` branch to trigger automatic deployment!
