# ⚡ Quick Start Upgrade Guide
## Start Upgrading the Platform Today

**Target Audience:** Developers ready to start upgrading  
**Time Required:** 2-4 hours for Phase 1A  
**Prerequisites:** Access to staging environment

---

## 🎯 Phase 1A: Safe Immediate Updates (Today)

These updates have **minimal breaking changes** and can be done immediately:

### Step 1: Prepare Environment (10 minutes)

```bash
# Clone repository if not already
cd /path/to/omni-enterprise-ultra-max

# Create feature branch
git checkout -b upgrade/phase-1a-safe-updates

# Backup current requirements
cp backend/requirements.txt backend/requirements.txt.backup
cp gateway/requirements.txt gateway/requirements.txt.backup
cp frontend/package.json frontend/package.json.backup
```

### Step 2: Update Backend Safe Dependencies (30 minutes)

```bash
cd backend

# Update requirements.txt - Safe updates only
cat > requirements_updates.txt << 'EOF'
# Safe updates (patch/minor versions, well-tested)
fastapi==0.121.0          # was 0.104.1
pydantic==2.10.0          # was 2.5.0
uvicorn[standard]==0.32.0 # was 0.24.0
sqlalchemy==2.0.36        # was 2.0.23
redis[asyncio]==5.2.0     # was 5.0.1
httpx==0.27.2             # was 0.25.2
python-dotenv==1.0.1      # was 1.0.0
requests==2.32.3          # was 2.31.0
EOF

# Apply updates to requirements.txt
# (Manual: edit backend/requirements.txt with above versions)

# Install in virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run tests to verify
pytest tests/ -v

# If tests pass, commit
git add requirements.txt
git commit -m "Update backend safe dependencies (Phase 1A)"
```

### Step 3: Update Gateway Safe Dependencies (15 minutes)

```bash
cd ../gateway

# Update gateway/requirements.txt
cat > requirements_updates.txt << 'EOF'
fastapi==0.121.0
uvicorn[standard]==0.32.0
httpx==0.27.2
pydantic==2.10.0
redis==5.2.0
python-dotenv==1.0.1
EOF

# Apply updates manually to gateway/requirements.txt

# Install and test
pip install -r requirements.txt

# Test gateway
python -m pytest ../tests/test_gateway.py -v 2>/dev/null || echo "Create basic tests"

# Commit
git add requirements.txt
git commit -m "Update gateway safe dependencies (Phase 1A)"
```

### Step 4: Update Frontend Safe Dependencies (20 minutes)

```bash
cd ../frontend

# Update package.json dependencies
npm install react@18.3.1 react-dom@18.3.1
npm install react-router-dom@6.28.0
npm install typescript@5.6.3
npm install vite@5.4.11

# Test build
npm run build

# If successful, commit
git add package.json package-lock.json
git commit -m "Update frontend safe dependencies (Phase 1A)"
```

### Step 5: Test Locally (30 minutes)

```bash
# Start services with Docker Compose
cd ..
docker-compose up --build

# In another terminal, test endpoints
# Backend health check
curl http://localhost:8080/api/health

# Gateway health check
curl http://localhost:8081/health -H "x-api-key: dev-key-123"

# Test an AI endpoint
curl -X POST http://localhost:8081/api/v1/ai/sentiment \
  -H "x-api-key: dev-key-123" \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test"}'
```

### Step 6: Deploy to Staging (30 minutes)

```bash
# Push branch
git push origin upgrade/phase-1a-safe-updates

# Deploy to staging (use your deployment method)
# Option 1: Cloud Build
gcloud builds submit --config=cloudbuild-backend.yaml \
  --substitutions=_TAG=phase-1a-test

# Option 2: GitHub Actions
# Create PR and add label "deploy-staging"

# Wait for deployment and test
curl https://your-staging-backend-url/api/health

# Monitor logs for 30 minutes
gcloud logging read "resource.type=cloud_run_revision" \
  --limit 50 \
  --format json \
  --project=refined-graph-471712-n9
```

### Step 7: Verify and Merge (15 minutes)

```bash
# If staging is healthy, create PR
gh pr create --title "Phase 1A: Safe dependency updates" \
  --body "Updates safe dependencies with minimal breaking changes"

# Get approval and merge
# After merge, monitor production for 24 hours
```

---

## 🔥 Phase 1B: Critical API Updates (Next Day)

These require more careful testing due to significant version jumps:

### OpenAI SDK Update (Critical)

```bash
# Create new branch
git checkout -b upgrade/openai-sdk

# Read migration guide
# https://github.com/openai/openai-python/blob/main/CHANGELOG.md

# Update backend/requirements.txt
# Change: openai==1.3.9
# To:     openai==1.54.0

# Key breaking changes to handle:
# 1. Client initialization changed
# 2. Streaming API updated
# 3. New models available (gpt-4o, gpt-4-turbo)

# Example code update needed:
```

**OLD CODE (v1.3.9):**
```python
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
```

**NEW CODE (v1.54.0):**
```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.chat.completions.create(
    model="gpt-4o",  # New model!
    messages=[{"role": "user", "content": "Hello"}]
)
```

**Files to Update:**
- `backend/services/ai/openai_service.py`
- `backend/routes/ai_routes.py`
- Any route using OpenAI

**Testing Checklist:**
- [ ] Chat completions work
- [ ] Streaming works
- [ ] Embeddings generation works
- [ ] Function calling works (if used)
- [ ] Error handling works

```bash
# Test thoroughly
pytest tests/test_openai_integration.py -v

# Commit and deploy to staging
git add .
git commit -m "Upgrade OpenAI SDK to 1.54.0 with gpt-4o support"
git push origin upgrade/openai-sdk
```

### Anthropic SDK Update (Critical)

```bash
# Create branch
git checkout -b upgrade/anthropic-sdk

# Update backend/requirements.txt
# Change: anthropic==0.7.8
# To:     anthropic==0.39.0

# Key changes:
# 1. Client API changed
# 2. Claude 3.5 Sonnet available
# 3. Message API updated
```

**OLD CODE (v0.7.8):**
```python
import anthropic

client = anthropic.Client(api_key=os.getenv("ANTHROPIC_API_KEY"))
response = client.completion(
    prompt=f"{anthropic.HUMAN_PROMPT} Hello {anthropic.AI_PROMPT}",
    model="claude-2",
    max_tokens_to_sample=100
)
```

**NEW CODE (v0.39.0):**
```python
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",  # Latest model!
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
)
```

**Files to Update:**
- `backend/services/ai/anthropic_service.py`
- `backend/routes/ai_routes.py`

**Testing:**
```bash
pytest tests/test_anthropic_integration.py -v

git add .
git commit -m "Upgrade Anthropic SDK to 0.39.0 with Claude 3.5 Sonnet"
git push origin upgrade/anthropic-sdk
```

---

## 🧪 Testing Strategy

### Local Testing

```bash
# Run all tests
cd backend
pytest tests/ -v --cov=. --cov-report=html

# Test specific modules
pytest tests/test_ai_routes.py -v
pytest tests/test_openai_service.py -v
pytest tests/test_anthropic_service.py -v

# Check for deprecation warnings
pytest -W default tests/

# Manual API testing
python -m tests.manual_smoke_test
```

### Create Manual Smoke Test

```python
# backend/tests/manual_smoke_test.py
import asyncio
import httpx
import os

async def test_endpoints():
    base_url = os.getenv("API_URL", "http://localhost:8080")
    api_key = os.getenv("API_KEY", "dev-key-123")
    
    headers = {"x-api-key": api_key}
    
    async with httpx.AsyncClient() as client:
        # Test health
        r = await client.get(f"{base_url}/api/health")
        assert r.status_code == 200
        print("✅ Health check passed")
        
        # Test OpenAI
        r = await client.post(
            f"{base_url}/api/v1/ai/chat",
            headers=headers,
            json={
                "messages": [{"role": "user", "content": "Hello"}],
                "model": "gpt-4o"
            }
        )
        assert r.status_code == 200
        print("✅ OpenAI endpoint passed")
        
        # Test Anthropic
        r = await client.post(
            f"{base_url}/api/v1/ai/anthropic-chat",
            headers=headers,
            json={
                "messages": [{"role": "user", "content": "Hello"}],
                "model": "claude-3-5-sonnet-20241022"
            }
        )
        assert r.status_code == 200
        print("✅ Anthropic endpoint passed")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
```

Run with:
```bash
cd backend
python -m tests.manual_smoke_test
```

---

## 🚨 Rollback Procedure

If something goes wrong:

### Docker Rollback

```bash
# Stop current containers
docker-compose down

# Checkout previous version
git checkout HEAD~1

# Rebuild with old dependencies
docker-compose up --build
```

### Cloud Run Rollback

```bash
# List revisions
gcloud run revisions list \
  --service=omni-ultra-backend-prod \
  --region=europe-west1

# Roll back to previous revision
gcloud run services update-traffic omni-ultra-backend-prod \
  --region=europe-west1 \
  --to-revisions=PREVIOUS_REVISION=100
```

### Database Rollback (if needed)

```bash
# Rollback migrations
cd backend
alembic downgrade -1

# Or restore from backup
# psql -U user -d database < backup.sql
```

---

## 📊 Monitoring After Updates

### Check These Metrics

```bash
# Error rate
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_count" AND metric.status="5xx"'

# Latency
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_latencies"'

# Memory usage
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/container/memory/utilizations"'
```

### Check Sentry for Errors

```bash
# Visit Sentry dashboard
# https://sentry.io/organizations/your-org/issues/

# Look for:
# - New error types
# - Increased error rate
# - Specific to updated dependencies
```

### Check Logs

```bash
# Recent errors
gcloud logging read "severity>=ERROR" \
  --limit 50 \
  --project=refined-graph-471712-n9

# Search for specific issues
gcloud logging read 'jsonPayload.message=~"OpenAI|Anthropic"' \
  --limit 50
```

---

## ✅ Success Criteria

Before considering Phase 1 complete:

- [ ] All tests passing (backend, gateway, frontend)
- [ ] Zero new errors in Sentry
- [ ] API response times within 10% of baseline
- [ ] No increase in 5xx error rate
- [ ] Staging stable for 24 hours
- [ ] Production stable for 24 hours after deployment
- [ ] New AI models (gpt-4o, claude-3.5) accessible
- [ ] Team notified of changes
- [ ] Documentation updated

---

## 🆘 Getting Help

### If Tests Fail

1. Check error messages carefully
2. Review migration guides for breaking changes
3. Test individual components in isolation
4. Ask for help in team channel

### If Deployment Fails

1. Check Cloud Build logs
2. Verify secrets are configured
3. Check IAM permissions
4. Roll back and investigate

### If Production Has Issues

1. **ROLLBACK IMMEDIATELY** (see above)
2. Check monitoring dashboards
3. Review error logs
4. Document the issue
5. Fix in staging first
6. Redeploy after verification

---

## 📞 Contact

- **Technical Lead:** ___________
- **DevOps:** ___________
- **On-Call:** ___________
- **Slack Channel:** #omni-platform-upgrades

---

## 🎯 Next Steps After Phase 1

Once Phase 1A and 1B are complete and stable:

1. Review `UPGRADE_CHECKLIST.md` for Phase 2
2. Plan Stripe major version upgrade (needs business approval)
3. Schedule ML framework updates
4. Implement new features from roadmap

---

**Good luck with the upgrades! 🚀**

Remember: **Test thoroughly, deploy gradually, monitor closely.**
