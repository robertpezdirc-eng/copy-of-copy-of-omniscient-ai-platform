# 🚀 OMNI ENTERPRISE ULTRA MAX - Hitra Referenca

## ⚡ Hitri Ukazi

### Lokalni Razvoj
```bash
# Zagon celotne platforme
docker-compose up

# Samo backend
docker-compose up backend

# Samo gateway
docker-compose up gateway

# Backend: http://localhost:8080
# Gateway: http://localhost:8081
```

### Testiranje
```powershell
# Health check
Invoke-WebRequest -Uri "http://localhost:8081/health" -Headers @{"x-api-key"="dev-key-123"}

# Backend health
Invoke-WebRequest -Uri "http://localhost:8080/api/health"

# API summary
Invoke-WebRequest -Uri "http://localhost:8081/api/v1/omni/summary"
```

### Production Testing
```powershell
# Backend (direct)
Invoke-WebRequest -Uri "https://omni-ultra-backend-prod-661612368188.europe-west1.run.app/api/health"

# Metrics
Invoke-WebRequest -Uri "https://omni-ultra-backend-prod-661612368188.europe-west1.run.app/metrics"

# API Docs
Start-Process "https://omni-ultra-backend-prod-661612368188.europe-west1.run.app/api/docs"
```

---

## 📦 Deployment

### Gateway (1 ukaz, 3 minute)
```powershell
.\deploy-gateway.ps1
```

Ali ročno:
```bash
cd gateway
gcloud run deploy ai-gateway \
  --source=. \
  --region=europe-west1 \
  --allow-unauthenticated \
  --set-env-vars="UPSTREAM_URL=https://omni-ultra-backend-prod-661612368188.europe-west1.run.app,API_KEYS=prod-key-omni-2025"
```

### Backend
```bash
cd backend
gcloud run deploy omni-ultra-backend \
  --source=. \
  --region=europe-west1 \
  --memory=4Gi \
  --cpu=2 \
  --timeout=300
```

### Dashboard Builder
```powershell
# Status
.\build-dashboards.ps1 -Action status

# Build high priority (6 dashboards)
.\build-dashboards.ps1 -Action build-priority -Priority 1

# Build all (20 dashboards)
.\build-dashboards.ps1 -Action build-all
```

---

## 🔑 Ključni URL-ji

### Production
```
Backend:    https://omni-ultra-backend-prod-661612368188.europe-west1.run.app
API Docs:   https://omni-ultra-backend-prod-661612368188.europe-west1.run.app/api/docs
ReDoc:      https://omni-ultra-backend-prod-661612368188.europe-west1.run.app/api/redoc
Metrics:    https://omni-ultra-backend-prod-661612368188.europe-west1.run.app/metrics
Health:     https://omni-ultra-backend-prod-661612368188.europe-west1.run.app/api/health
```

### Local
```
Backend:    http://localhost:8080
Gateway:    http://localhost:8081
API Docs:   http://localhost:8080/api/docs
```

### GCP
```
Project:    refined-graph-471712-n9
Region:     europe-west1
Zone:       europe-west1-b
```

---

## 📚 Najpogostejši API-ji

### Health & Status
```bash
GET  /api/health              # System health
GET  /api/v1/omni/summary     # Overview
GET  /metrics                 # Prometheus metrics
```

### AI/ML
```bash
POST /api/v1/ai-intelligence/churn-prediction
POST /api/v1/ai-intelligence/recommendations
POST /api/v1/ai-intelligence/sentiment
POST /api/v1/ai-intelligence/forecast
```

### Payments
```bash
POST /api/v1/payments/stripe/checkout
POST /api/v1/payments/paypal/create-order
POST /api/v1/payments/crypto/create-invoice
```

### Affiliate
```bash
POST /api/v1/affiliate/register
GET  /api/v1/affiliate/dashboard/{id}
POST /api/v1/affiliate/track-click
```

### RAG
```bash
POST /api/v1/rag/ingest      # Add documents
POST /api/v1/rag/query       # Ask questions
GET  /api/v1/rag/status      # System status
```

### GDPR
```bash
POST /api/v1/gdpr/export-data     # Data export
POST /api/v1/gdpr/delete-user     # Right to erasure
POST /api/v1/gdpr/consent         # Consent management
```

---

## 🔐 Avtentikacija

### API Key v Header (priporočeno)
```bash
curl -H "x-api-key: your-api-key" \
  https://backend-url/api/endpoint
```

### PowerShell
```powershell
$headers = @{"x-api-key" = "your-api-key"}
Invoke-WebRequest -Uri "https://backend-url/api/endpoint" -Headers $headers
```

### Python
```python
import requests

headers = {"x-api-key": "your-api-key"}
response = requests.get("https://backend-url/api/endpoint", headers=headers)
```

---

## 🔧 Environment Variables

### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db
MONGODB_URI=mongodb://host:27017/db
REDIS_URL=redis://host:6379

# AI/ML
OPENAI_API_KEY=sk-...
USE_OLLAMA=true
OLLAMA_HOST=http://localhost:11434

# Payments
STRIPE_SECRET_KEY=sk_test_...
PAYPAL_CLIENT_ID=...

# Feature Flags
ENABLE_AI_INTELLIGENCE=true
ENABLE_RAG=true
ENABLE_GDPR=true
```

### Gateway (.env)
```bash
UPSTREAM_URL=http://backend:8080
API_KEYS=dev-key-123,prod-key-omni-2025
REDIS_URL=redis://localhost:6379
RATE_LIMIT_PER_MINUTE=100
```

---

## 📊 Monitoring

### Prometheus Queries
```promql
# Request rate
rate(http_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Active users
business_active_users
```

### Cloud Monitoring
```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# Tail logs
gcloud logging tail

# Filter by severity
gcloud logging read "severity>=ERROR" --limit 20
```

---

## 🐛 Debug

### Preveri Zdravje Storitev
```bash
# PostgreSQL
psql -h localhost -U omni -d omni_db -c "SELECT 1;"

# MongoDB
mongosh "mongodb://localhost:27017" --eval "db.adminCommand('ping')"

# Redis
redis-cli PING

# Ollama
curl http://localhost:11434/api/tags
```

### Logiranje
```bash
# Enable debug
export LOG_LEVEL=DEBUG

# Slow request threshold
export PERF_SLOW_THRESHOLD_SEC=0.1
```

### Profiling
```python
# Python profiling
python -m cProfile -s cumulative backend/main.py

# Memory profiling
python -m memory_profiler backend/main.py
```

---

## 💰 Cene

### Tiers
| Tier | Zahtevki/min | Zahtevki/dan | Cena |
|------|--------------|--------------|------|
| FREE | 10 | 1,000 | €0 |
| PRO | 100 | 10,000 | €49/m |
| ENTERPRISE | Unlimited | Unlimited | Custom |

### Mesečni Stroški (Production)
```
Backend (Cloud Run):     €100-150
Gateway (Cloud Run):     €5-10
Databases:               €90-100
Vector DB (optional):    €0-70
LLM APIs (optional):     €200-500
-----------------------------------
SKUPAJ:                  €400-750
```

---

## 🚨 Najpogostejše Težave

### 1. Backend ne reagira
```bash
# Restart
gcloud run services update omni-ultra-backend --region=europe-west1

# Preveri logs
gcloud logging read "resource.type=cloud_run_revision" --limit 20

# Preveri health
curl https://omni-ultra-backend-prod-661612368188.europe-west1.run.app/api/health
```

### 2. Rate Limiting (429)
```bash
# Povečaj limit v gateway config
export RATE_LIMIT_PER_MINUTE=1000

# Ali uporabi drug API key
curl -H "x-api-key: enterprise-key" ...
```

### 3. Database Connection Error
```bash
# Preveri credentials
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1;"

# Preveri firewall
gcloud compute firewall-rules list
```

### 4. Ollama ne deluje
```bash
# Zagon Ollama
ollama serve

# Pull model
ollama pull codellama

# Test
curl http://localhost:11434/api/generate -d '{"model":"codellama"}'
```

---

## 📖 Dokumentacija

### Glavne Datoteke
```
README.md                                  - Quick start
OMNI_ENTERPRISE_ULTRA_MAX_VPOGLED.md      - Celotna dokumentacija (SLO)
OMNI_HITRA_REFERENCA.md                   - Ta dokument
IMPLEMENTATION_COMPLETE.md                 - Technical architecture
DASHBOARD_BUILDER_README.md                - Dashboard builder
QUICK_TEST_GUIDE.md                        - Test scenarios
DEPLOYMENT_PLAN.md                         - Deployment strategies
```

### Struktura Repozitorija
```
/backend/               - ML Backend service
  /routes/              - API endpoints (30+ modules)
  /middleware/          - Custom middleware
  /services/            - Business logic
  /models/              - Data models
  main.py               - FastAPI app

/gateway/               - API Gateway
  /app/                 - Gateway code
    main.py             - Entry point
    proxy.py            - Reverse proxy
    auth.py             - API key auth

/frontend/              - React dashboard
  /src/components/      - UI components
  /src/pages/           - Pages

/dashboards/            - Generated dashboards (20)
docker-compose.yml      - Local development
```

---

## 🎯 Naslednji Koraki

### Za Začetek
1. ✅ **Test Backend** - `curl backend-url/api/health`
2. ⏳ **Deploy Gateway** - `.\deploy-gateway.ps1`
3. 🔍 **Test Integration** - Preveri gateway → backend
4. 📊 **Build Dashboards** - `.\build-dashboards.ps1`

### Za Produkcijo
5. 🔐 **Security** - Nastavi production API keys
6. 📈 **Monitoring** - Setup Grafana dashboards
7. 🌐 **Custom Domain** - Point to gateway URL
8. 💰 **Billing Alerts** - Set up budget alerts

### Za Razvoj
9. 📚 **Read Docs** - OMNI_ENTERPRISE_ULTRA_MAX_VPOGLED.md
10. 🧪 **Write Tests** - Unit + integration tests
11. 🚀 **Add Features** - Extend functionality
12. 🤝 **Contribute** - Submit PRs

---

## 📞 Podpora

### Kontakti
```
Technical Support:  support@omni-platform.eu
Security Issues:    security@omni-platform.eu
DPO (GDPR):        dpo@omni-platform.eu
```

### Koristne Povezave
```
GitHub:      https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform
Issues:      https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform/issues
Discussions: https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform/discussions
```

---

## ✅ Checklist za Launch

### Pre-Launch
- [ ] Backend deployed in healthy
- [ ] Gateway deployed in healthy
- [ ] Database backups configured
- [ ] Monitoring alarms set
- [ ] API keys generated
- [ ] Rate limits configured
- [ ] GDPR compliance verified
- [ ] Security audit completed

### Launch Day
- [ ] DNS pointed to gateway
- [ ] SSL certificates active
- [ ] Load testing completed
- [ ] Rollback plan ready
- [ ] Team on standby
- [ ] Status page updated

### Post-Launch
- [ ] Monitor metrics
- [ ] Check error rates
- [ ] Review logs
- [ ] User feedback
- [ ] Performance tuning
- [ ] Documentation updates

---

**OMNI Enterprise Ultra Max** - *Your Quick Reference Guide* 🚀

*Zadnja posodobitev: 3. november 2025*
*Verzija: 1.0.0*
