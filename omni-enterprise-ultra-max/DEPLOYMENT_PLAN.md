# 📦 Dashboard Builder Deployment Plan

## Priprava (5 min)

### 1. Commit Nove Kode

```powershell
cd C:\Users\admin\Downloads\copy-of-copy-of-omniscient-ai-platform\omni-enterprise-ultra-max

git status
git add backend/services/ai/dashboard_builder_service.py
git add backend/routes/dashboard_builder_routes.py
git add backend/main.py
git add build-dashboards.ps1
git add dashboard.env.example
git add DASHBOARD_BUILDER_README.md
git add QUICK_TEST_GUIDE.md
git add .github/workflows/build-dashboards.yml

git commit -m "feat: Add Ollama-powered Dashboard Builder with 20 dashboard types

- DashboardBuilderService for AI-generated React dashboards
- REST API endpoints for dashboard generation
- PowerShell CLI tool (build-dashboards.ps1)
- GitHub Actions workflow for automated builds
- Support for 3 priority levels (high/medium/low)
- Template fallback when Ollama unavailable
- Comprehensive documentation"

git push origin master
```

---

## Deploy Backend (10 min)

### Option A: Quick Deploy (Existing Image)

```powershell
# Update environment variables only
gcloud run services update omni-ultra-backend `
  --region=europe-west1 `
  --update-env-vars="USE_OLLAMA=true,OLLAMA_URL=https://ollama-661612368188.europe-west1.run.app,OLLAMA_MODEL=llama3,OLLAMA_TIMEOUT=90"
```

### Option B: Full Rebuild

```powershell
# Build new image with dashboard builder
gcloud builds submit --config=cloudbuild-backend.yaml `
  --substitutions="_PROJECT_ID=refined-graph-471712-n9,_TAG=dashboard-builder"

# Deploy new image
gcloud run deploy omni-ultra-backend `
  --image=europe-west1-docker.pkg.dev/refined-graph-471712-n9/omni/omni-ultra-backend:dashboard-builder `
  --region=europe-west1 `
  --platform=managed `
  --allow-unauthenticated `
  --memory=2Gi `
  --cpu=2 `
  --timeout=300 `
  --set-env-vars="USE_OLLAMA=true,OLLAMA_URL=https://ollama-661612368188.europe-west1.run.app,OLLAMA_MODEL=llama3,OLLAMA_TIMEOUT=90,RUN_AS_INTERNAL=0,OMNI_MINIMAL=true"
```

---

## Verify Deployment (2 min)

### 1. Health Check

```powershell
curl https://omni-ultra-backend-661612368188.europe-west1.run.app/api/health
```

**Expected:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:00:00"
}
```

### 2. Dashboard Builder Status

```powershell
curl https://omni-ultra-backend-661612368188.europe-west1.run.app/api/v1/dashboards/build/status
```

**Expected:**
```json
{
  "backend_url": "https://omni-ultra-backend-661612368188.europe-west1.run.app",
  "github_repo": "robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform",
  "total_dashboards": 20,
  "ollama_enabled": true,
  "ollama_url": "https://ollama-661612368188.europe-west1.run.app",
  "ollama_model": "llama3",
  "ollama_healthy": true
}
```

### 3. List Dashboard Types

```powershell
.\build-dashboards.ps1 -Action list `
  -Url "https://omni-ultra-backend-661612368188.europe-west1.run.app"
```

**Expected:** Liste vseh 20 dashboard tipov

---

## Generate Dashboards (15-30 min)

### Phase 1: High Priority (6 dashboards)

```powershell
.\build-dashboards.ps1 -Action build-priority -Priority 1 `
  -Url "https://omni-ultra-backend-661612368188.europe-west1.run.app"
```

**Dashboards:**
- Revenue Analytics
- User Analytics & Engagement
- AI Performance & Model Insights
- Subscription Metrics
- System Health Monitoring
- Security & Authentication

**Estimated Time:** ~6-10 minutes

### Phase 2: Medium Priority (11 dashboards)

```powershell
.\build-dashboards.ps1 -Action build-priority -Priority 2 `
  -Url "https://omni-ultra-backend-661612368188.europe-west1.run.app"
```

**Dashboards:**
- Affiliate Tracking
- Marketplace Overview
- Churn Prediction
- Forecast Dashboard
- Sentiment Analysis
- Anomaly Detection
- Payment Gateway Monitoring
- API Usage Dashboard
- Growth Engine Metrics
- Gamification Dashboard
- Recommendation Engine

**Estimated Time:** ~12-18 minutes

### Phase 3: Low Priority (4 dashboards)

```powershell
.\build-dashboards.ps1 -Action build-priority -Priority 3 `
  -Url "https://omni-ultra-backend-661612368188.europe-west1.run.app"
```

**Dashboards:**
- Neo4j Graph Insights
- Swarm Intelligence
- AGI Dashboard
- (one more priority 3)

**Estimated Time:** ~4-6 minutes

### All at Once (20 dashboards)

```powershell
# WARNING: This will take 20-30 minutes
.\build-dashboards.ps1 -Action build-all `
  -Url "https://omni-ultra-backend-661612368188.europe-west1.run.app"
```

---

## Download Generated Dashboards (5 min)

### Option A: Via API

```powershell
# List generated files
$response = Invoke-RestMethod -Uri "https://omni-ultra-backend-661612368188.europe-west1.run.app/api/v1/dashboards/generated"

# Download each dashboard
foreach ($dashboard in $response.dashboards) {
    $url = "https://omni-ultra-backend-661612368188.europe-west1.run.app/api/v1/dashboards/download/$($dashboard.file)"
    $output = "frontend/src/pages/dashboards/$($dashboard.file)"
    
    Invoke-WebRequest -Uri $url -OutFile $output
    Write-Host "✅ Downloaded: $($dashboard.name)"
}
```

### Option B: Manual Copy from Container

```powershell
# Get container instance
$container = gcloud run services describe omni-ultra-backend `
  --region=europe-west1 `
  --format="value(status.latestReadyRevisionName)"

# Access container (if possible)
# Note: Cloud Run is stateless, files may not persist
# Better approach: Use Cloud Storage bucket
```

### Option C: Save to Cloud Storage (Recommended)

**Update `dashboard_builder_service.py`:**

```python
from google.cloud import storage

def save_to_gcs(self, dashboards: List[Dict[str, Any]], bucket_name: str):
    """Save dashboards to Google Cloud Storage"""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    
    for dashboard in dashboards:
        blob = bucket.blob(f"dashboards/{dashboard['file']}")
        blob.upload_from_string(dashboard['code'])
        logger.info(f"Uploaded {dashboard['name']} to GCS")
```

**Then download:**

```powershell
gsutil -m cp -r gs://omni-dashboards-bucket/dashboards/*.tsx frontend/src/pages/dashboards/
```

---

## Integrate into Frontend (15 min)

### 1. Install Dependencies (if needed)

```powershell
cd frontend
npm install recharts @types/recharts
```

### 2. Create Dashboard Routes

**`frontend/src/routes/dashboardRoutes.tsx`:**

```typescript
import { RevenueAnalytics } from '@/pages/dashboards/revenue_analytics';
import { UserAnalytics } from '@/pages/dashboards/user_analytics';
import { AIPerformance } from '@/pages/dashboards/ai_performance';
// Import all dashboards...

export const dashboardRoutes = [
  { path: '/dashboard/revenue', element: <RevenueAnalytics />, label: 'Revenue Analytics', icon: '💰' },
  { path: '/dashboard/users', element: <UserAnalytics />, label: 'User Analytics', icon: '👥' },
  { path: '/dashboard/ai', element: <AIPerformance />, label: 'AI Performance', icon: '🤖' },
  // Add all dashboards...
];
```

### 3. Update App.tsx

```typescript
import { dashboardRoutes } from './routes/dashboardRoutes';

function App() {
  return (
    <Router>
      <Routes>
        {/* Existing routes */}
        
        {/* Dashboard routes */}
        {dashboardRoutes.map(route => (
          <Route key={route.path} path={route.path} element={route.element} />
        ))}
      </Routes>
    </Router>
  );
}
```

### 4. Add Navigation Menu

**`frontend/src/components/DashboardMenu.tsx`:**

```typescript
import { dashboardRoutes } from '@/routes/dashboardRoutes';
import { Link } from 'react-router-dom';

export function DashboardMenu() {
  return (
    <nav className="dashboard-menu">
      <h3>Dashboards</h3>
      <ul>
        {dashboardRoutes.map(route => (
          <li key={route.path}>
            <Link to={route.path}>
              <span>{route.icon}</span>
              <span>{route.label}</span>
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
```

### 5. Build & Deploy Frontend

```powershell
cd frontend
npm run build

# Deploy to Cloud Run
gcloud run deploy omni-frontend `
  --source . `
  --region=europe-west1 `
  --platform=managed `
  --allow-unauthenticated
```

---

## Setup GitHub Actions (5 min)

### 1. Enable Workflow

The workflow is already in `.github/workflows/build-dashboards.yml`

### 2. Add Required Secrets (if needed)

Go to: https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform/settings/secrets/actions

Add:
- `GCP_PROJECT_ID`: `refined-graph-471712-n9`
- `GCP_REGION`: `europe-west1`
- `BACKEND_URL`: `https://omni-ultra-backend-661612368188.europe-west1.run.app`

### 3. Manual Trigger Test

1. Go to: https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform/actions
2. Select "Build AI Dashboards"
3. Click "Run workflow"
4. Select priority: `1`
5. Click "Run workflow"

### 4. Verify Workflow

Check logs and ensure:
- ✅ Builder health check passes
- ✅ Dashboards are generated
- ✅ Files are saved successfully

---

## Post-Deployment Checklist

### Backend

- [ ] Backend deployed successfully
- [ ] `/api/v1/dashboards/build/status` returns healthy
- [ ] `/api/v1/dashboards/types` lists all 20 types
- [ ] Ollama service is reachable
- [ ] Environment variables configured correctly

### Dashboard Generation

- [ ] High-priority dashboards generated (6)
- [ ] Medium-priority dashboards generated (11)
- [ ] Low-priority dashboards generated (4)
- [ ] All dashboards saved to disk/GCS
- [ ] Manifest.json created successfully

### Frontend

- [ ] Dashboard files copied to frontend
- [ ] Routes configured for all dashboards
- [ ] Navigation menu shows all dashboards
- [ ] Dashboards load without errors
- [ ] Charts render correctly
- [ ] WebSocket connections work
- [ ] Mobile responsive design works
- [ ] Export functionality works

### CI/CD

- [ ] GitHub Actions workflow enabled
- [ ] Manual trigger works
- [ ] Scheduled builds configured (weekly)
- [ ] Notifications configured

### Documentation

- [ ] README updated with dashboard links
- [ ] API documentation includes new endpoints
- [ ] Team trained on dashboard usage

---

## Rollback Plan

If deployment fails:

### Rollback Backend

```powershell
# Get previous revision
gcloud run revisions list --service=omni-ultra-backend --region=europe-west1

# Rollback to previous version
gcloud run services update-traffic omni-ultra-backend `
  --to-revisions=omni-ultra-backend-PREVIOUS-REVISION=100 `
  --region=europe-west1
```

### Remove Dashboard Routes

```typescript
// Comment out dashboard routes in App.tsx
// {dashboardRoutes.map(route => ( ... ))}
```

---

## Monitoring

### Check Logs

```powershell
# Backend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=omni-ultra-backend" --limit 50 --format json

# Filter dashboard-related logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=omni-ultra-backend AND textPayload:dashboard" --limit 20
```

### Metrics

```powershell
# Request count
gcloud monitoring time-series list `
  --filter='metric.type="run.googleapis.com/request_count" AND resource.labels.service_name="omni-ultra-backend"'

# Error rate
gcloud monitoring time-series list `
  --filter='metric.type="run.googleapis.com/request_count" AND metric.labels.response_code_class="5xx"'
```

---

## Cost Estimate

### Ollama Requests (20 dashboards)
- **Requests:** 20 dashboards × 1 request = 20 requests
- **Duration:** ~60 seconds per dashboard = 1,200 seconds total
- **Cost:** Depends on Ollama Cloud Run pricing (~$0.0001/sec) = ~$0.12

### Backend Cloud Run
- **CPU:** 2 vCPU × 300s × 20 dashboards = 12,000 vCPU-seconds
- **Memory:** 2GB × 300s × 20 dashboards = 12,000 GB-seconds
- **Estimated:** ~$0.50/build

### Storage (GCS)
- **Files:** 20 × 10KB = 200KB
- **Cost:** Negligible (~$0.001/month)

### Total Monthly Cost (Weekly Builds)
- **4 builds/month:** ~$2.50/month

---

## Success Criteria

✅ **Backend deployed** with dashboard builder routes  
✅ **20 dashboards generated** via Ollama AI  
✅ **Frontend integrated** with all dashboards  
✅ **CI/CD working** with automated builds  
✅ **Documentation complete** for team usage  
✅ **Monitoring active** for errors and performance  

---

## Next Steps After Deployment

1. **User Testing** - Get feedback from team on dashboards
2. **Refinement** - Adjust prompts for better code generation
3. **Customization** - Add team-specific dashboard types
4. **Scaling** - Optimize Ollama timeout and concurrency
5. **Analytics** - Track dashboard usage and performance

---

**Ready to deploy! 🚀**

**Estimated Total Time:** 60-90 minutes
