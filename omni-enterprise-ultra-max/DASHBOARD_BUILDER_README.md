# 🎨 Dashboard Builder - Ollama Powered

Automated dashboard generation using **Ollama AI** for the Omni Enterprise Ultra Max platform.

## 🚀 Quick Start

### 1. Check Builder Status

```bash
curl http://localhost:8080/api/v1/dashboards/build/status
```

### 2. List Available Dashboard Types

```bash
curl http://localhost:8080/api/v1/dashboards/types
```

**Available Dashboards (20 types):**

| Priority | Dashboard | Description |
|----------|-----------|-------------|
| ⭐⭐⭐ | Revenue Analytics | Real-time revenue tracking with charts and KPIs |
| ⭐⭐⭐ | User Analytics | User engagement metrics and cohort analysis |
| ⭐⭐⭐ | AI Performance | ML model performance and inference metrics |
| ⭐⭐⭐ | Subscription Metrics | Subscription lifecycle and MRR tracking |
| ⭐⭐⭐ | System Health | Infrastructure monitoring and alerts |
| ⭐⭐⭐ | Security & Auth | Authentication, authorization, security events |
| ⭐⭐ | Affiliate Tracking | Multi-tier affiliate program analytics |
| ⭐⭐ | Marketplace Overview | API marketplace sales and usage |
| ⭐⭐ | Churn Prediction | ML-powered churn risk dashboard |
| ⭐⭐ | Forecast Dashboard | Revenue and user growth forecasting |
| ⭐⭐ | Sentiment Analysis | Customer sentiment from support tickets |
| ⭐⭐ | Anomaly Detection | Real-time anomaly alerts and trends |
| ⭐⭐ | Payment Gateway | Stripe, PayPal, Crypto transaction monitoring |
| ⭐⭐ | API Usage Dashboard | Rate limiting, quotas, endpoint usage |
| ⭐⭐ | Growth Engine | Viral coefficients and referral tracking |
| ⭐ | Gamification Dashboard | User points, badges, leaderboards |
| ⭐ | Recommendation Engine | Product recommendation performance |
| ⭐ | Neo4j Graph Insights | Knowledge graph and relationship analytics |
| ⭐ | Swarm Intelligence | Multi-agent coordination and task distribution |
| ⭐ | AGI Dashboard | Advanced AI reasoning and planning metrics |

### 3. Build All High-Priority Dashboards (Priority 1)

```bash
curl -X POST http://localhost:8080/api/v1/dashboards/build \
  -H "Content-Type: application/json" \
  -d '{"priority_filter": 1, "save_to_disk": true}'
```

### 4. Build All Dashboards

```bash
curl -X POST http://localhost:8080/api/v1/dashboards/build \
  -H "Content-Type: application/json" \
  -d '{"save_to_disk": true, "output_dir": "dashboards/generated"}'
```

### 5. Build Single Dashboard

```bash
curl -X POST http://localhost:8080/api/v1/dashboards/build/Revenue%20Analytics
```

### 6. List Generated Dashboards

```bash
curl http://localhost:8080/api/v1/dashboards/generated
```

---

## 📋 PowerShell Commands

### Build All High-Priority Dashboards

```powershell
Invoke-RestMethod -Uri "http://localhost:8080/api/v1/dashboards/build" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"priority_filter": 1, "save_to_disk": true}' | ConvertTo-Json -Depth 10
```

### Build All Dashboards

```powershell
Invoke-RestMethod -Uri "http://localhost:8080/api/v1/dashboards/build" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"save_to_disk": true}' | ConvertTo-Json -Depth 10
```

### Check Status

```powershell
Invoke-RestMethod -Uri "http://localhost:8080/api/v1/dashboards/build/status" | ConvertTo-Json -Depth 10
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Enable Ollama
USE_OLLAMA=true

# Ollama URL
OLLAMA_URL=https://ollama-661612368188.europe-west1.run.app

# Default Model
OLLAMA_MODEL=llama3

# Timeout (seconds)
OLLAMA_TIMEOUT=60
```

### Cloud Run Deployment

Already configured:
- **Backend**: `https://omni-ultra-backend-661612368188.europe-west1.run.app`
- **Ollama**: `https://ollama-661612368188.europe-west1.run.app`

---

## 📁 Output Structure

Generated dashboards are saved to:

```
backend/dashboards/generated/
├── manifest.json              # Index of all generated dashboards
├── revenue_analytics.tsx       # Revenue dashboard
├── user_analytics.tsx          # User dashboard
├── ai_performance.tsx          # AI metrics dashboard
├── subscription_metrics.tsx    # Subscription dashboard
├── system_health.tsx           # Health monitoring
├── security_&_auth.tsx         # Security dashboard
├── affiliate_tracking.tsx      # Affiliate dashboard
├── marketplace_overview.tsx    # Marketplace dashboard
├── churn_prediction.tsx        # Churn ML dashboard
├── forecast_dashboard.tsx      # Forecasting dashboard
├── sentiment_analysis.tsx      # Sentiment dashboard
├── anomaly_detection.tsx       # Anomaly dashboard
├── payment_gateway.tsx         # Payment dashboard
├── api_usage_dashboard.tsx     # API usage dashboard
├── growth_engine.tsx           # Growth metrics
├── gamification_dashboard.tsx  # Gamification
├── recommendation_engine.tsx   # Recommendations
├── neo4j_graph_insights.tsx    # Graph analytics
├── swarm_intelligence.tsx      # Multi-agent
└── agi_dashboard.tsx           # AGI metrics
```

---

## 🎯 Dashboard Features

Each generated dashboard includes:

✅ **React TypeScript** component  
✅ **Recharts** visualizations (Line, Bar, Pie charts)  
✅ **Real-time data** fetching with auto-refresh  
✅ **WebSocket** support for live updates  
✅ **Loading states** and error handling  
✅ **Tailwind CSS** responsive styling  
✅ **Key metrics cards** with KPIs  
✅ **Mobile & desktop** responsive design  
✅ **Export** to PDF/CSV functionality  
✅ **Date range filters** for time-based analysis  

---

## 🔥 Integration with Frontend

### 1. Copy Generated Dashboards

```bash
# From backend to frontend
cp backend/dashboards/generated/*.tsx frontend/src/pages/dashboards/
```

### 2. Add Routes to Frontend

```typescript
// frontend/src/App.tsx
import { RevenueAnalyticsDashboard } from './pages/dashboards/revenue_analytics';
import { UserAnalyticsDashboard } from './pages/dashboards/user_analytics';
// ... import other dashboards

// Add routes
<Route path="/dashboard/revenue" element={<RevenueAnalyticsDashboard />} />
<Route path="/dashboard/users" element={<UserAnalyticsDashboard />} />
```

### 3. Add Navigation Links

```typescript
const dashboardLinks = [
  { path: '/dashboard/revenue', label: 'Revenue Analytics', icon: '💰' },
  { path: '/dashboard/users', label: 'User Analytics', icon: '👥' },
  { path: '/dashboard/ai', label: 'AI Performance', icon: '🤖' },
  // ... add more
];
```

---

## 🚀 Deployment

### Build Dashboards in Production

```bash
# On Cloud Run backend
curl -X POST https://omni-ultra-backend-661612368188.europe-west1.run.app/api/v1/dashboards/build \
  -H "Content-Type: application/json" \
  -d '{"priority_filter": 1, "save_to_disk": true}'
```

### Automated Build via GitHub Actions

Add to `.github/workflows/ci-cd.yaml`:

```yaml
- name: Generate Dashboards
  run: |
    curl -X POST ${{ secrets.BACKEND_URL }}/api/v1/dashboards/build \
      -H "Content-Type: application/json" \
      -d '{"save_to_disk": true}'
```

---

## 🎨 Customization

### Modify Dashboard Prompt

Edit `backend/services/ai/dashboard_builder_service.py`:

```python
def _create_dashboard_prompt(self, dashboard_type: Dict[str, Any]) -> str:
    # Customize the prompt sent to Ollama
    return f"""Generate a React dashboard for: {dashboard_type['name']}
    
    Requirements:
    1. Add your custom requirements here
    2. Use specific chart types
    3. Include additional features
    """
```

### Add New Dashboard Type

```python
# In dashboard_builder_service.py
self.dashboard_types.append({
    "name": "Custom Dashboard",
    "description": "Your custom dashboard description",
    "endpoints": ["/api/v1/custom/endpoint"],
    "priority": 2
})
```

---

## 📊 Monitoring

### Check Ollama Health

```bash
curl http://localhost:8080/api/v1/ollama/health
```

### View Build Logs

```bash
docker logs omni-backend 2>&1 | grep "Dashboard"
```

---

## 🆘 Troubleshooting

### Ollama Not Responding

```bash
# Check Ollama service
curl https://ollama-661612368188.europe-west1.run.app/api/tags

# Restart backend
docker-compose restart backend
```

### Dashboards Not Generating

1. Check Ollama is enabled: `USE_OLLAMA=true`
2. Verify Ollama URL is correct
3. Check backend logs for errors
4. Try building a single dashboard first

### Generated Code Has Issues

- Adjust temperature (lower = more consistent): `temperature=0.2`
- Modify the prompt in `_create_dashboard_prompt()`
- Use template mode if Ollama is unavailable

---

## 📚 API Reference

### `GET /api/v1/dashboards/types`
List all dashboard types available for generation

### `POST /api/v1/dashboards/build`
Build multiple dashboards with filters

**Body:**
```json
{
  "priority_filter": 1,  // Optional: 1=high, 2=medium, 3=low
  "save_to_disk": true,
  "output_dir": "dashboards/generated"
}
```

### `POST /api/v1/dashboards/build/{dashboard_name}`
Build a single dashboard by name

### `GET /api/v1/dashboards/build/status`
Get builder status and Ollama health

### `GET /api/v1/dashboards/generated`
List all generated dashboard files

---

## ✨ Next Steps

1. **Deploy to Cloud Run** - Backend already has Ollama configured
2. **Integrate with Frontend** - Copy generated TSX files
3. **Customize Dashboards** - Modify prompts and templates
4. **Add More Types** - Extend `dashboard_types` array
5. **Automate Builds** - Add to CI/CD pipeline

---

**Built with ❤️ using Ollama AI + FastAPI + React**
