# GitHub Actions Setup Guide

This guide explains how to configure GitHub Secrets and Variables for the CI/CD pipeline that deploys the Omni Platform to Google Cloud Run.

## 📋 Prerequisites

1. **Google Cloud Project** with Cloud Run API enabled
2. **Service Account** with appropriate permissions
3. **GitHub repository** with admin access to configure secrets

---

## 🔐 Required GitHub Secrets

GitHub Secrets are encrypted environment variables used for sensitive data like credentials. Configure these in your repository settings.

### 1. Navigate to GitHub Secrets

1. Go to your repository: https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

### 2. Configure Required Secrets

#### `GCP_PROJECT_ID`
- **Description**: Your Google Cloud Project ID
- **Value**: `refined-graph-471712-n9`
- **How to get it**:
  ```bash
  gcloud config get-value project
  ```

#### `GCP_SA_KEY`
- **Description**: Service Account JSON key for authentication
- **Value**: Complete JSON content of your service account key file
- **How to create**:
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
    --role="roles/storage.admin"
  
  gcloud projects add-iam-policy-binding refined-graph-471712-n9 \
    --member="serviceAccount:github-actions@refined-graph-471712-n9.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"
  
  # Create and download key
  gcloud iam service-accounts keys create github-actions-key.json \
    --iam-account=github-actions@refined-graph-471712-n9.iam.gserviceaccount.com
  
  # Copy entire content of github-actions-key.json and paste as secret
  cat github-actions-key.json
  ```

#### `GATEWAY_API_KEYS` (Optional)
- **Description**: API keys for AI Gateway integration (if using external AI services)
- **Value**: Comma-separated list of API keys or JSON object
- **Example**: 
  ```json
  {
    "openai": "sk-...",
    "anthropic": "sk-ant-...",
    "vertexai": "..."
  }
  ```

---

## ⚙️ Optional GitHub Variables

GitHub Variables are non-sensitive configuration values. Configure these in the same location as secrets.

### Navigate to Variables
1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click the **Variables** tab
3. Click **New repository variable**

### Available Variables

#### `GCP_REGION`
- **Description**: Google Cloud region for deployment
- **Default**: `europe-west1`
- **Options**: Any valid GCP region (e.g., `us-central1`, `asia-east1`)

#### `SERVICE_NAME`
- **Description**: Cloud Run service name
- **Default**: `omni-backend`
- **Recommendation**: Use default unless you need multiple deployments

#### `USE_OLLAMA`
- **Description**: Enable local Ollama as AI provider
- **Default**: `false`
- **Values**: `true` or `false`
- **Note**: Set to `true` if you have an Ollama instance accessible from Cloud Run

#### `OLLAMA_URL`
- **Description**: Ollama server URL
- **Default**: `http://localhost:11434`
- **Example**: `http://your-ollama-server.example.com:11434`

---

## 🚀 Testing the Setup

### Method 1: Automatic Trigger (Push to main/master)

```bash
# Make a small change and push to main
git checkout main
echo "# Test" >> README.md
git add README.md
git commit -m "test: trigger CI/CD"
git push origin main
```

### Method 2: Manual Trigger (Workflow Dispatch)

Using GitHub CLI:
```bash
gh workflow run deploy.yml
```

Or via GitHub UI:
1. Go to **Actions** tab: https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform/actions
2. Click **Deploy to Cloud Run** workflow
3. Click **Run workflow** button
4. Select branch and click **Run workflow**

---

## 🔍 Monitoring the Deployment

### 1. GitHub Actions UI

Visit: https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform/actions

You'll see:
- ✅ Green checkmark: Deployment successful
- ❌ Red X: Deployment failed (click for logs)
- 🟡 Yellow dot: Deployment in progress

### 2. Deployment Steps

The workflow performs these steps:
1. **Checkout code** - Gets latest code from repository
2. **Set up Cloud SDK** - Configures gcloud CLI
3. **Authenticate** - Uses service account credentials
4. **Deploy to Cloud Run** - Builds and deploys Docker image
5. **Run smoke tests** - Validates deployment with health checks

### 3. View Detailed Logs

Click on any workflow run to see:
- Console output for each step
- Build logs
- Deployment status
- Test results

---

## 📊 Verification Checklist

After setting up secrets, verify:

- [ ] `GCP_PROJECT_ID` is set to `refined-graph-471712-n9`
- [ ] `GCP_SA_KEY` contains valid JSON service account key
- [ ] Service account has required IAM roles:
  - `roles/run.admin`
  - `roles/storage.admin`
  - `roles/iam.serviceAccountUser`
- [ ] Cloud Run API is enabled in GCP project
- [ ] Container Registry API is enabled in GCP project

### Quick Verification Script

```bash
# Check if APIs are enabled
gcloud services list --enabled --project=refined-graph-471712-n9 | grep -E "run.googleapis.com|containerregistry.googleapis.com"

# Check service account permissions
gcloud projects get-iam-policy refined-graph-471712-n9 \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:github-actions@refined-graph-471712-n9.iam.gserviceaccount.com"
```

---

## 🐛 Troubleshooting

### Error: "Permission denied"
**Solution**: Ensure service account has all required roles listed above.

### Error: "Project not found"
**Solution**: Verify `GCP_PROJECT_ID` secret is set correctly.

### Error: "Invalid credentials"
**Solution**: Regenerate service account key and update `GCP_SA_KEY` secret.

### Error: "API not enabled"
**Solution**: Enable required APIs:
```bash
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com \
  --project=refined-graph-471712-n9
```

### Workflow doesn't trigger
**Solution**: 
- Ensure workflow file is on main/master branch
- Check branch protection rules don't block pushes
- Verify workflow file syntax is valid YAML

### Build fails with "No such file or directory"
**Solution**: Check Dockerfile.backend exists and all referenced files are in the repository.

---

## 🔗 Related Documentation

- [OLLAMA_CICD_GUIDE.md](./OLLAMA_CICD_GUIDE.md) - Complete guide for Ollama integration and CI/CD
- [.env.example](./.env.example) - Environment variable reference
- [Google Cloud IAM Roles](https://cloud.google.com/iam/docs/understanding-roles)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

---

## 📝 Quick Reference

### Secrets Summary
| Secret | Required | Example Value |
|--------|----------|---------------|
| `GCP_PROJECT_ID` | ✅ Yes | `refined-graph-471712-n9` |
| `GCP_SA_KEY` | ✅ Yes | `{"type": "service_account",...}` |
| `GATEWAY_API_KEYS` | ⚪ Optional | `{"openai": "sk-..."}` |

### Variables Summary
| Variable | Default | Options |
|----------|---------|---------|
| `GCP_REGION` | `europe-west1` | Any GCP region |
| `SERVICE_NAME` | `omni-backend` | Custom service name |
| `USE_OLLAMA` | `false` | `true`, `false` |
| `OLLAMA_URL` | `http://localhost:11434` | Custom Ollama URL |

---

## ✅ Next Steps

1. Configure all required secrets
2. (Optional) Configure variables if you need custom settings
3. Test deployment using one of the methods above
4. Monitor deployment in GitHub Actions UI
5. Verify service is running: Check Cloud Run console or run smoke tests

**All code is ready and pushed! 🚀**

To trigger the first deployment:
```bash
gh workflow run deploy.yml
```

Or simply push to main/master branch.
