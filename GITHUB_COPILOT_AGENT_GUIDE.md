# 🤖 GitHub Copilot Agent & CI/CD Pipeline Vodič

## 📋 Kaj mora biti pripravljen na projektu za GitHub Actions

### ✅ Trenutno stanje projekta:

#### 1. **Repository Struktura** ✅
```
omni-enterprise-ultra-max/
├── .github/
│   └── workflows/
│       └── ci-cd.yaml ✅ (7-job pipeline)
├── backend/
│   ├── main.py ✅
│   ├── routes/ ✅ (28+ modules)
│   ├── middleware/ ✅
│   ├── adapters/ ✅ (9 adapters)
│   └── requirements.txt ✅
├── frontend/
├── scripts/
│   └── gcs-backup.sh ✅
├── Dockerfile ✅
├── .dockerignore ✅
└── .env ✅
```

#### 2. **GitHub Actions CI/CD Pipeline** ✅
**Location:** `.github/workflows/ci-cd.yaml`

**7 Jobs konfiguriranih:**
1. ✅ **code-quality** - Black, Flake8, Pylint, MyPy, Bandit, SonarCloud
2. ✅ **frontend-build** - Node.js 18, ESLint, tests, build
3. ✅ **backend-test** - pytest with MongoDB, MySQL, Redis
4. ✅ **build-and-push** - Docker images to GCR
5. ✅ **deploy-staging** - Cloud Run staging deployment
6. ✅ **deploy-production** - Cloud Run production deployment
7. ✅ **continuous-backup** - GCS backup (NEW!)

### 🔐 GitHub Secrets Potrebni:

Za delovanje CI/CD pipeline potrebuješ naslednje GitHub Secrets:

```bash
# Obišči: https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform/settings/secrets/actions

1. GCP_SA_KEY             - Google Cloud Service Account Key (JSON)
2. SONAR_TOKEN            - SonarCloud authentication token
3. CODECOV_TOKEN          - Codecov upload token
4. SLACK_WEBHOOK          - Slack notification webhook URL
5. OPENAI_API_KEY         - OpenAI API key (for production)
6. STRIPE_SECRET_KEY      - Stripe payment gateway key
7. PAYPAL_CLIENT_SECRET   - PayPal payment gateway secret
```

### 📝 Kako dodati GitHub Secrets:

#### 1. **GCP Service Account Key** (najpomembnejši!)
```bash
# 1. Ustvari Service Account v GCP Console
gcloud iam service-accounts create omni-ci-cd \
  --display-name="Omni CI/CD Pipeline" \
  --project=refined-graph-471712-n9

# 2. Dodeli pravice
gcloud projects add-iam-policy-binding refined-graph-471712-n9 \
  --member="serviceAccount:omni-ci-cd@refined-graph-471712-n9.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding refined-graph-471712-n9 \
  --member="serviceAccount:omni-ci-cd@refined-graph-471712-n9.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding refined-graph-471712-n9 \
  --member="serviceAccount:omni-ci-cd@refined-graph-471712-n9.iam.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.editor"

# 3. Ustvari JSON key
gcloud iam service-accounts keys create ~/omni-ci-cd-key.json \
  --iam-account=omni-ci-cd@refined-graph-471712-n9.iam.gserviceaccount.com

# 4. Vsebino ~/omni-ci-cd-key.json kopiraj kot GCP_SA_KEY secret v GitHub
```

#### 2. **Dodajanje Secrets v GitHub:**
```bash
# Način 1: Preko GitHub CLI (če je avtenticiran)
gh secret set GCP_SA_KEY < ~/omni-ci-cd-key.json
gh secret set STRIPE_SECRET_KEY --body "sk_live_xxx..."

# Način 2: Preko GitHub Web UI
# 1. Pojdi na: https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform/settings/secrets/actions
# 2. Click "New repository secret"
# 3. Name: GCP_SA_KEY
# 4. Value: Paste JSON content
# 5. Click "Add secret"
```

### 🚀 GitHub Copilot Coding Agent Uporaba

#### Kdaj uporabiti GitHub Copilot Coding Agent:

✅ **Uporabi za:**
- Kompleksne merge operacije
- Multi-file refactoring
- Feature implementation across multiple files
- Bug fixes ki zahtevajo spremembe v več datotekah
- Automated PR creation z testing

❌ **Ne uporabi za:**
- Enostavne single-file spremembe
- Quick fixes
- Dokumentacija updates
- Simple debugging

#### Kako uporabiti GitHub Copilot Coding Agent:

**Način 1: Direktna uporaba**
```bash
# Omeni #github-pull-request_copilot-coding-agent v chatu
"Implementiraj nova payment gateway integracija z GitHub Copilot agent #github-pull-request_copilot-coding-agent"
```

**Način 2: Issue-based**
```bash
# 1. Ustvari GitHub Issue
# 2. V chatu povej: "Uporabi GitHub Copilot agent za implementacijo Issue #123"
```

**Značilnosti:**
- ✅ Ustvari nov branch
- ✅ Implementira spremembe
- ✅ Testira kod
- ✅ Ustvari Pull Request
- ✅ Doda dokumentacijo

### 🔄 CI/CD Pipeline Workflow

#### Avtomatski trigger:
```yaml
on:
  push:
    branches: [main, master, develop]
  pull_request:
    branches: [main, master]
  workflow_dispatch:  # Manual trigger
```

#### Flow:
```
1. Push to master/main
   ↓
2. code-quality (linting, security checks)
   ↓
3. frontend-build + backend-test (parallel)
   ↓
4. build-and-push (Docker images to GCR)
   ↓
5. deploy-staging (test environment)
   ↓
6. deploy-production (requires approval if main branch)
   ↓
7. continuous-backup (GCS backup)
```

### 📊 Preverjanje Pipeline Status

#### Preko GitHub Web:
```
https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform/actions
```

#### Preko GitHub CLI:
```bash
# Login first
gh auth login

# Check workflow runs
gh run list --workflow=ci-cd.yaml

# View specific run
gh run view <run-id>

# Watch live
gh run watch
```

#### Preko git commit status:
```bash
git log --oneline | head -5
# Green checkmark ✓ = pipeline passed
# Red X ✗ = pipeline failed
```

### 🔧 Debugging Failed Pipelines

#### 1. **Check GitHub Actions logs:**
```
GitHub repo → Actions tab → Click failed workflow → View logs
```

#### 2. **Common issues:**

**Build failures:**
```bash
# Missing dependencies
Solution: Update backend/requirements.txt or frontend/package.json

# Docker build fails
Solution: Fix Dockerfile syntax or add missing files to .dockerignore
```

**Deployment failures:**
```bash
# GCP authentication failed
Solution: Check GCP_SA_KEY secret is correct

# Cloud Run quota exceeded
Solution: Increase quota in GCP Console or reduce resources

# Image not found
Solution: Check GCR image was pushed successfully in build-and-push job
```

**Test failures:**
```bash
# Unit tests fail
Solution: Fix code or update tests

# Integration tests fail
Solution: Check service dependencies (MongoDB, Redis, MySQL)
```

### 🎯 Best Practices

#### 1. **Branch Strategy:**
```bash
main/master     → Production (requires approval)
develop         → Staging (auto-deploy)
feature/*       → Pull requests only
```

#### 2. **Commit Messages:**
```bash
✨ feat: Add new payment gateway
🐛 fix: Fix authentication bug
📝 docs: Update README
🔧 chore: Update dependencies
♻️ refactor: Restructure routes
🚀 deploy: Update deployment config
```

#### 3. **PR Guidelines:**
- Vedno ustvari PR za feature branches
- Počakaj da pipeline mine (zeleno ✓)
- Code review od vsaj 1 člana tima
- Merge s "Squash and merge" za clean history

### 🛠️ Manual Deployment (Bypass CI/CD)

Če želiš deployati ročno brez GitHub Actions:

```bash
# 1. Build locally
docker build -t omni-unified-backend -f Dockerfile .

# 2. Tag for GCR
docker tag omni-unified-backend gcr.io/refined-graph-471712-n9/omni-unified-backend:latest

# 3. Push to GCR
docker push gcr.io/refined-graph-471712-n9/omni-unified-backend:latest

# 4. Deploy to Cloud Run
gcloud run deploy omni-unified-backend \
  --image gcr.io/refined-graph-471712-n9/omni-unified-backend:latest \
  --platform managed \
  --region europe-west1 \
  --project refined-graph-471712-n9
```

### 📱 Monitoring & Notifications

#### Setup Slack Notifications:
```bash
# 1. Create Slack Incoming Webhook
# 2. Add to GitHub Secrets as SLACK_WEBHOOK
# 3. Pipeline bo poslal notifikacije za:
#    - ✅ Successful deployments
#    - ❌ Failed deployments
#    - ⚠️ Manual approval needed
```

#### Cloud Monitoring:
```bash
# View Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision" \
  --limit 50 \
  --project refined-graph-471712-n9

# View metrics
gcloud monitoring dashboards list --project refined-graph-471712-n9
```

### 🎓 Quick Reference

#### Enable CI/CD:
```bash
# 1. Ensure .github/workflows/ci-cd.yaml exists ✅
# 2. Add required GitHub Secrets ⚠️ (MISSING)
# 3. Push to master/main
# 4. Check Actions tab

# Current status:
✅ Pipeline configured
✅ Dockerfile ready
✅ Requirements defined
⚠️ GitHub Secrets need to be added
⚠️ Service Account needs proper permissions
```

#### Next Steps:
1. **Add GCP_SA_KEY secret** (kritično!)
2. **Add other secrets** (STRIPE, PAYPAL, etc.)
3. **Test pipeline** with manual trigger
4. **Monitor first deployment**
5. **Setup Cloud Scheduler** for GCS backups

---

**Repository:** https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform  
**CI/CD Pipeline:** `.github/workflows/ci-cd.yaml`  
**Status:** ✅ Configured, ⚠️ Secrets needed  
**Last Updated:** October 31, 2025
