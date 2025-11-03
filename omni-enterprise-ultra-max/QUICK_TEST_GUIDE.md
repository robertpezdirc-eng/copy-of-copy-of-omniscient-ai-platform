# 🚀 Quick Test Guide

## Trenutno Stanje

✅ **Dashboard Builder Service** - Uspešno inicializiran s 20 dashboard tipi  
✅ **REST API Endpoints** - Registriran v main.py  
✅ **PowerShell CLI Tool** - `build-dashboards.ps1` pripravljen  
✅ **GitHub Actions Workflow** - Avtomatska gradnja dashboardov  
✅ **Dokumentacija** - Celotna navodila v `DASHBOARD_BUILDER_README.md`

---

## Testiranje Lokalno

### 1. Poženi Backend

```powershell
cd backend
python main.py
```

Backend bi moral biti na `http://localhost:8080`

### 2. Testiraj Status

```powershell
# PowerShell
.\build-dashboards.ps1 -Action status

# Ali curl
curl http://localhost:8080/api/v1/dashboards/build/status
```

**Pričakovani output:**
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

### 3. Seznam Dashboard Tipov

```powershell
.\build-dashboards.ps1 -Action list
```

**Pričakovano:** Seznam vseh 20 dashboard tipov, razdeljenih po prioritetah

### 4. Build Prvi Dashboard (Test)

```powershell
# Build Revenue Analytics dashboard
.\build-dashboards.ps1 -Action build-single -Dashboard "Revenue Analytics"
```

**Pričakovano:**
- Ollama generira React TypeScript kodo
- Dashboard vsebuje Recharts komponente
- Koda se shrani v `backend/dashboards/generated/revenue_analytics.tsx`

### 5. Build Visoko-Prioritetne Dashboarde

```powershell
# Build vseh 6 high-priority dashboards
.\build-dashboards.ps1 -Action build-priority -Priority 1
```

**High Priority Dashboards (6 total):**
1. Revenue Analytics
2. User Analytics & Engagement  
3. AI Performance & Model Insights
4. Subscription Metrics
5. System Health Monitoring
6. Security & Authentication

**Trajanje:** ~5-10 minut (odvisno od Ollama hitrosti)

### 6. Preveri Generirane Dashboarde

```powershell
.\build-dashboards.ps1 -Action generated
```

**Pričakovano:**
```
📊 Generated Dashboard Files

Total generated: 6

📊 Revenue Analytics
   File: revenue_analytics.tsx
   Generated: 2024-01-15T10:30:00
   Priority: 1

📊 User Analytics
   File: user_analytics.tsx
   Generated: 2024-01-15T10:32:00
   Priority: 1
...
```

---

## Konfiguriraj Ollama

Če Ollama ni dosegljiv, preveri:

### Lokalno

```powershell
# Preveri če Ollama teče
curl http://localhost:11434/api/tags

# Če ne teče, zaženi Ollama
ollama serve
```

### Cloud Run

Ollama servis je že deploy na:
```
https://ollama-661612368188.europe-west1.run.app
```

Preveri health:
```powershell
curl https://ollama-661612368188.europe-west1.run.app/api/tags
```

---

## Deploy na Cloud Run

### 1. Build Backend Image

```powershell
gcloud builds submit --config=cloudbuild-backend.yaml `
  --substitutions=_PROJECT_ID=refined-graph-471712-n9,_TAG=dashboard-v1
```

### 2. Deploy Backend

```powershell
gcloud run deploy omni-ultra-backend `
  --image=europe-west1-docker.pkg.dev/refined-graph-471712-n9/omni/omni-ultra-backend:dashboard-v1 `
  --region=europe-west1 `
  --platform=managed `
  --allow-unauthenticated `
  --set-env-vars="USE_OLLAMA=true,OLLAMA_URL=https://ollama-661612368188.europe-west1.run.app,OLLAMA_MODEL=llama3"
```

### 3. Testiraj na Production

```powershell
# Status check
curl https://omni-ultra-backend-661612368188.europe-west1.run.app/api/v1/dashboards/build/status

# Build high-priority dashboards
.\build-dashboards.ps1 -Action build-priority -Priority 1 `
  -Url "https://omni-ultra-backend-661612368188.europe-west1.run.app"
```

---

## GitHub Actions Workflow

### Ročno Sprožanje

1. Pojdi na: https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform/actions
2. Izberi workflow "Build AI Dashboards"
3. Klikni "Run workflow"
4. Izberi priority: `1` (high), `2` (medium), `3` (low), ali `all`

### Avtomatsko (Tedensko)

Workflow se bo avtomatično zagnal vsak **ponedeljek ob 2:00 AM UTC**.

---

## Integracija v Frontend

### 1. Kopiraj Generirane Dashboarde

```powershell
# Copy from backend to frontend
Copy-Item backend/dashboards/generated/*.tsx frontend/src/pages/dashboards/
```

### 2. Dodaj Route v Frontend

```typescript
// frontend/src/App.tsx
import { RevenueAnalyticsDashboard } from './pages/dashboards/revenue_analytics';
import { UserAnalyticsDashboard } from './pages/dashboards/user_analytics';
import { AIPerformanceDashboard } from './pages/dashboards/ai_performance';

// Add routes
<Route path="/dashboard/revenue" element={<RevenueAnalyticsDashboard />} />
<Route path="/dashboard/users" element={<UserAnalyticsDashboard />} />
<Route path="/dashboard/ai" element={<AIPerformanceDashboard />} />
```

### 3. Dodaj Navigacijo

```typescript
const dashboardMenu = [
  { path: '/dashboard/revenue', label: 'Revenue', icon: '💰' },
  { path: '/dashboard/users', label: 'Users', icon: '👥' },
  { path: '/dashboard/ai', label: 'AI Performance', icon: '🤖' },
];
```

---

## Troubleshooting

### Problem: Ollama ni dosegljiv

**Rešitev:**
```powershell
# Preveri status
curl https://ollama-661612368188.europe-west1.run.app/api/tags

# Če ni dosegljiv, preveri Cloud Run service
gcloud run services describe ollama --region=europe-west1
```

### Problem: Dashboard generation timeout

**Rešitev:**
```bash
# Povečaj timeout v .env
OLLAMA_TIMEOUT=120

# Ali v PowerShell
$env:OLLAMA_TIMEOUT="120"
```

### Problem: Dashboard koda je nepopolna

**Rešitev:**
```python
# Adjust temperature in dashboard_builder_service.py
response = self.ollama_service.generate(
    prompt=prompt,
    temperature=0.2,  # Lower = more consistent
    max_tokens=4096
)
```

### Problem: No dashboards generated

**Preveri:**
1. Ollama service je dosegljiv
2. `USE_OLLAMA=true` je nastavljen
3. Backend logs za napake: `docker logs omni-backend`

---

## Naslednji Koraki

1. ✅ **Testiraj lokalno** - Preveri da vse dela
2. 🚀 **Deploy na Cloud Run** - Objavi spremenjeni backend
3. 🎨 **Build vse dashboarde** - Generiraj vseh 20
4. 📊 **Integriraj v Frontend** - Dodaj dashboarde v UI
5. 🔄 **Setup CI/CD** - Avtomatiziraj gradnjo

---

## Ukazi v Eni Vrstici

```powershell
# Test celotnega workflow-a
.\build-dashboards.ps1 -Action status; `
.\build-dashboards.ps1 -Action list; `
.\build-dashboards.ps1 -Action build-priority -Priority 1; `
.\build-dashboards.ps1 -Action generated
```

**Ali z curl:**
```bash
# Status → List → Build → Check
curl http://localhost:8080/api/v1/dashboards/build/status && \
curl http://localhost:8080/api/v1/dashboards/types && \
curl -X POST http://localhost:8080/api/v1/dashboards/build \
  -H "Content-Type: application/json" \
  -d '{"priority_filter": 1, "save_to_disk": true}' && \
curl http://localhost:8080/api/v1/dashboards/generated
```

---

**Dashboard Builder je pripravljen! 🚀**
