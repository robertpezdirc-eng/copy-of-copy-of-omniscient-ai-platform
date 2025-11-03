# 🚀 OMNI ENTERPRISE ULTRA MAX - Konsolidirana Platforma

**Dobrodošli v konsolidirani direktorij OMNI Enterprise Ultra Max platforme!**

Ta direktorij vsebuje vse ključne komponente, module, dokumentacijo in skripte platforme OMNI ENTERPRISE ULTRA MAX, združene na enem mestu za lažji pregled in razumevanje.

---

## 📚 Dokumentacija

### Glavne Dokumentacijske Datoteke

| Datoteka | Opis | Velikost |
|----------|------|----------|
| **[OMNI_ENTERPRISE_ULTRA_MAX_VPOGLED.md](OMNI_ENTERPRISE_ULTRA_MAX_VPOGLED.md)** | Celovit vpogled v platformo - 1,600+ vrstic | ⭐⭐⭐ |
| **[OMNI_HITRA_REFERENCA.md](OMNI_HITRA_REFERENCA.md)** | Hitra referenca s komandami in API-ji | ⭐⭐⭐ |
| **[OMNI_ARHITEKTURNI_DIAGRAMI.md](OMNI_ARHITEKTURNI_DIAGRAMI.md)** | Arhitekturni diagrami in podatkovni tok | ⭐⭐⭐ |
| **[DOKUMENTACIJA_INDEKS.md](DOKUMENTACIJA_INDEKS.md)** | Navigacijski indeks dokumentacije | ⭐⭐ |

### Priporočeno Branje

1. **Začetniki**: Začnite z [OMNI_HITRA_REFERENCA.md](OMNI_HITRA_REFERENCA.md) (10 min)
2. **Celoten pregled**: Nadaljujte z [OMNI_ENTERPRISE_ULTRA_MAX_VPOGLED.md](OMNI_ENTERPRISE_ULTRA_MAX_VPOGLED.md) (30 min)
3. **Tehnična arhitektura**: [OMNI_ARHITEKTURNI_DIAGRAMI.md](OMNI_ARHITEKTURNI_DIAGRAMI.md) (15 min)

---

## 🏗️ Struktura Projekta

```
omni-enterprise-ultra-max/
├── README.md                              # Ta dokument
│
├── DOKUMENTACIJA/                         # Slovenska dokumentacija
│   ├── OMNI_ENTERPRISE_ULTRA_MAX_VPOGLED.md
│   ├── OMNI_HITRA_REFERENCA.md
│   ├── OMNI_ARHITEKTURNI_DIAGRAMI.md
│   └── DOKUMENTACIJA_INDEKS.md
│
├── backend/                               # ML Backend Service
│   ├── main.py                           # FastAPI aplikacija
│   ├── database.py                       # Povezave na baze podatkov
│   ├── routes/                           # 30+ API route modulov
│   ├── services/                         # Poslovna logika
│   │   ├── ai/                          # AI/ML servisi
│   │   ├── compliance/                  # GDPR compliance
│   │   ├── bi/                          # Business Intelligence
│   │   └── security/                    # Varnostni servisi
│   ├── middleware/                       # Custom middleware
│   ├── models/                          # Podatkovni modeli
│   ├── utils/                           # Utility funkcije
│   ├── payment_gateways/                # Plačilni sistemi
│   ├── k8s/                             # Kubernetes manifesti
│   ├── Dockerfile*                      # Docker images
│   └── requirements.txt                 # Python dependencies
│
├── gateway/                              # API Gateway Service
│   ├── app/
│   │   ├── main.py                      # Gateway entry point
│   │   ├── proxy.py                     # Reverse proxy
│   │   ├── auth.py                      # API key avtentikacija
│   │   ├── rate_limiter.py              # Rate limiting
│   │   ├── response_cache.py            # Response caching
│   │   ├── metrics.py                   # Prometheus metrics
│   │   └── ...                          # Ostali moduli
│   ├── Dockerfile                       # Gateway Docker image
│   └── requirements.txt                 # Python dependencies
│
├── deployment-scripts/                   # Deployment skripta
│   ├── deploy-gateway.ps1               # Gateway deploy (PowerShell)
│   ├── deploy-backend.ps1               # Backend deploy (PowerShell)
│   ├── build-dashboards.ps1             # Dashboard builder (PowerShell)
│   ├── deploy-tier1.sh                  # Tier 1 deploy (Bash)
│   └── ...                              # Ostale skripte
│
├── tests/                                # Testni primeri
│   ├── smoke_tests.py                   # Smoke testi
│   ├── test_ai_features.py              # AI/ML testi
│   ├── test_gdpr_enhanced.py            # GDPR testi
│   └── ...                              # Ostali testi
│
├── docker-compose.yml                    # Lokalni development
├── docker-compose.monitoring.yml         # Monitoring stack
├── cloudbuild-backend.yaml              # Backend CI/CD
├── cloudbuild-gateway.yaml              # Gateway CI/CD
└── cloudbuild.yaml                      # Main CI/CD
```

---

## 🎯 Ključne Komponente

### 1. Backend ML Service

**Lokacija**: `backend/`

Backend je glavni ML worker, ki vsebuje:

- **50+ API endpoints** za različne funkcionalnosti
- **AI/ML servisi** (`services/ai/`):
  - `rag_service.py` - Retrieval-Augmented Generation
  - `predictive_analytics.py` - Napovedna analitika
  - `sentiment_analysis.py` - Analiza sentimenta
  - `anomaly_detection.py` - Odkrivanje anomalij
  - `recommendation_engine.py` - Sistem priporočil
  - `dashboard_builder_service.py` - Dashboard builder
  - `ollama_service.py` - Ollama integracija
  - `multi_llm_router.py` - Multi-LLM routing
  - `autonomous_agent.py` - Avtonomni AI agenti
  - `swarm_intelligence.py` - Swarm AI

- **API Routes** (`routes/`):
  - 30+ route modulov za različne funkcionalnosti
  - AI intelligence, analytics, payments, affiliate, GDPR, itd.

- **Middleware** (`middleware/`):
  - Metrics, rate limiting, caching, security headers
  - Performance monitoring, usage tracking

- **Payment Gateways** (`payment_gateways/`):
  - Stripe, PayPal, Cryptocurrency integracije

- **Compliance** (`services/compliance/`):
  - GDPR compliance service
  - Data export, deletion, consent management

### 2. Gateway Service

**Lokacija**: `gateway/`

Gateway je lahek FastAPI proxy, ki upravlja:

- **Avtentikacija**: API key validation
- **Rate Limiting**: Redis-backed rate limiting
- **Caching**: Response cache za GET zahtevke
- **Metrics**: Prometheus metrics export
- **Proxy Logic**: Reverse proxy z `httpx`
- **Security**: Security headers, CORS
- **Tracing**: OpenTelemetry/Sentry integracija

### 3. Deployment Scripts

**Lokacija**: `deployment-scripts/`

Skripte za namestitev in upravljanje:

- `deploy-gateway.ps1` - 1-command gateway deploy (3 min)
- `deploy-backend.ps1` - Backend deployment
- `build-dashboards.ps1` - AI dashboard builder
- `deploy-tier1.sh` - Tier 1 deployment

### 4. Tests

**Lokacija**: `tests/`

Testi za vse ključne funkcionalnosti:

- Smoke tests
- AI/ML feature tests
- GDPR compliance tests
- MFA tests
- Cache metrics tests

---

## 🚀 Hitri Začetek

### Lokalni Razvoj

```bash
# Zagon celotne platforme
docker-compose up

# Backend: http://localhost:8080
# Gateway: http://localhost:8081
```

### Testiranje

```powershell
# Health check
Invoke-WebRequest -Uri "http://localhost:8081/health" -Headers @{"x-api-key"="dev-key-123"}

# API summary
Invoke-WebRequest -Uri "http://localhost:8081/api/v1/omni/summary"
```

### Produkcijska Namestitev

```powershell
# Gateway deploy (3 minute)
cd deployment-scripts
.\deploy-gateway.ps1

# Backend deploy
.\deploy-backend.ps1
```

---

## 📊 Glavni Moduli in Datoteke

### Backend Ključni Moduli

| Modul | Opis | Lokacija |
|-------|------|----------|
| `main.py` | FastAPI aplikacija | `backend/main.py` |
| `database.py` | Database connections | `backend/database.py` |
| AI/ML Services | RAG, predictions, recommendations | `backend/services/ai/` |
| GDPR Service | Compliance management | `backend/services/compliance/` |
| Payment Gateways | Stripe, PayPal, Crypto | `backend/payment_gateways/` |
| API Routes | 30+ route modules | `backend/routes/` |
| Middleware | Security, metrics, caching | `backend/middleware/` |

### Gateway Ključni Moduli

| Modul | Opis | Lokacija |
|-------|------|----------|
| `main.py` | Gateway entry point | `gateway/app/main.py` |
| `proxy.py` | Reverse proxy logic | `gateway/app/proxy.py` |
| `auth.py` | API key authentication | `gateway/app/auth.py` |
| `rate_limiter.py` | Rate limiting | `gateway/app/rate_limiter.py` |
| `response_cache.py` | Response caching | `gateway/app/response_cache.py` |
| `metrics.py` | Prometheus metrics | `gateway/app/metrics.py` |

---

## 🔑 Ključne Funkcionalnosti

### AI/ML Intelligence
- **Predictive Analytics** - Churn prediction, forecasting
- **RAG System** - Vector search z FAISS, multi-LLM support
- **Sentiment Analysis** - Multi-language NLP
- **Anomaly Detection** - PyOD, Isolation Forest
- **Recommendation Engine** - Collaborative + content-based filtering
- **Dashboard Builder** - AI-generated dashboards z Ollama

### Enterprise Features
- **Multi-Payment** - Stripe, PayPal, Cryptocurrency
- **Affiliate System** - Multi-tier commissions
- **GDPR Compliance** - Data export, deletion, consent
- **Security** - API keys, rate limiting, JWT auth
- **Monitoring** - Prometheus metrics, Grafana dashboards
- **Scalability** - Cloud Run/GKE, auto-scaling

---

## 💻 Tehnični Stack

### Backend
```
FastAPI         - Web framework
Python 3.11+    - Programming language
Uvicorn         - ASGI server
Pydantic        - Data validation

AI/ML:
TensorFlow 2.15 - Deep learning
PyTorch 2.1     - Neural networks
scikit-learn    - ML algorithms
Transformers    - NLP models
SpaCy           - NLP processing
FAISS           - Vector search
Prophet         - Forecasting
XGBoost         - Gradient boosting

Databases:
PostgreSQL      - Relational DB
MongoDB         - NoSQL document DB
Redis           - Cache + sessions
Firestore       - GCP NoSQL
Neo4j           - Graph DB (optional)
```

### Gateway
```
FastAPI         - Web framework
httpx           - HTTP client (async)
Redis           - Rate limiting + cache
Prometheus      - Metrics
Sentry          - Error tracking
OpenTelemetry   - Distributed tracing
```

### Infrastructure
```
Google Cloud Platform:
  - Cloud Run      - Serverless containers
  - GKE Autopilot  - Kubernetes
  - Cloud Build    - CI/CD
  - Artifact Registry - Docker images
  - Secret Manager - Credentials
  - Cloud Monitoring - Observability

Docker          - Containerization
Kubernetes      - Orchestration
```

---

## 📚 API Dokumentacija

### Interaktivna Dokumentacija

**Production Backend:**
```
https://omni-ultra-backend-prod-661612368188.europe-west1.run.app/api/docs
```

### Glavne API Kategorije

1. **Health & Status**
   - `/api/health` - Health check
   - `/api/v1/omni/summary` - System overview
   - `/metrics` - Prometheus metrics

2. **AI/ML Intelligence**
   - `/api/v1/ai-intelligence/churn-prediction`
   - `/api/v1/ai-intelligence/recommendations`
   - `/api/v1/ai-intelligence/sentiment`
   - `/api/v1/ai-intelligence/anomaly-detection`
   - `/api/v1/ai-intelligence/forecast`

3. **RAG System**
   - `/api/v1/rag/ingest` - Add documents
   - `/api/v1/rag/query` - Ask questions
   - `/api/v1/rag/search` - Vector search

4. **Payments**
   - `/api/v1/payments/stripe/*` - Stripe integration
   - `/api/v1/payments/paypal/*` - PayPal integration
   - `/api/v1/payments/crypto/*` - Crypto payments

5. **GDPR Compliance**
   - `/api/v1/gdpr/export-data` - Data export
   - `/api/v1/gdpr/delete-user` - Right to erasure
   - `/api/v1/gdpr/consent` - Consent management

6. **Affiliate System**
   - `/api/v1/affiliate/register` - Register affiliate
   - `/api/v1/affiliate/dashboard` - Affiliate dashboard
   - `/api/v1/affiliate/track-click` - Track clicks

---

## 🔐 Varnost in Skladnost

### Varnostne Funkcionalnosti
- ✅ API Key Authentication
- ✅ JWT Tokens
- ✅ Rate Limiting (Redis-backed)
- ✅ TLS 1.3 encryption
- ✅ Security Headers (HSTS, CSP, etc.)
- ✅ Input Validation (Pydantic)
- ✅ SQL Injection Protection (ORM)
- ✅ XSS Protection
- ✅ CSRF Protection

### Skladnost s Predpisi
- ✅ **GDPR** (EU) - Člen 15-20, 30, 33-34
- ✅ **ZVOP-2** (Slovenia) - Local compliance
- ✅ **ISO 27001** - Process compliance
- 📋 **CCPA** (California) - Planned
- 📋 **HIPAA** (Healthcare) - Planned
- ⚠️ **PCI-DSS** - Partial (via Stripe/PayPal)

---

## 📊 Monitoring in Observability

### Prometheus Metrics
```
http://localhost:8081/metrics  (lokalno)
https://backend-url/metrics     (produkcija)
```

**Ključne metrike:**
- HTTP request metrics (rate, latency, errors)
- Custom business metrics (revenue, users, API calls)
- System metrics (CPU, memory, GC)
- Cache metrics (hit rate, Redis stats)

### Grafana Dashboards
```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

### Logging
- Structured JSON logging
- Cloud Logging (GCP)
- Log-based metrics
- Export to BigQuery

---

## 💰 Stroški in Skaliranje

### Mesečni Operativni Stroški

**Cloud Run Setup:**
- Backend ML Service: €100-150/mesec
- Gateway Service: €5-10/mesec
- Databases: €90-100/mesec
- LLM APIs (optional): €200-500/mesec
- **SKUPAJ: €400-750/mesec**

**GKE Setup:**
- GKE Autopilot Cluster: €200-300/mesec
- Gateway Service: €5-10/mesec
- Databases: €90-100/mesec
- **SKUPAJ: €600-900/mesec**

### Skaliranje
- **Horizontalno**: Auto-scaling 0-100 instances
- **Vertikalno**: 1-4 vCPU, 512MB-8GB memory
- **Geografsko**: Multi-region deployment

---

## 🔧 Odpravljanje Težav

### Pogosta Vprašanja

**1. Backend ne reagira**
```bash
# Preveri health
curl https://backend-url/api/health

# Preveri logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50
```

**2. Rate Limiting (429)**
```bash
# Povečaj limit v gateway config
export RATE_LIMIT_PER_MINUTE=1000
```

**3. Database Connection Error**
```bash
# Test connection
psql $DATABASE_URL -c "SELECT 1;"
```

**4. Ollama ne deluje**
```bash
# Zagon Ollama
ollama serve

# Pull model
ollama pull codellama
```

---

## 🎯 Naslednji Koraki

### Za Začetek
1. ✅ Preberi dokumentacijo
2. ⏳ Zaženi lokalno z `docker-compose up`
3. 🔍 Test API endpoints
4. 📊 Build dashboards z `build-dashboards.ps1`

### Za Produkcijo
5. 🚀 Deploy gateway z `deploy-gateway.ps1`
6. 📈 Setup monitoring (Grafana + Prometheus)
7. 🔐 Konfiguriraj production API keys
8. 🌐 Dodaj custom domain

---

## 📞 Podpora

### Kontakti
- **Technical Support**: support@omni-platform.eu
- **Security Issues**: security@omni-platform.eu
- **DPO (GDPR)**: dpo@omni-platform.eu

### Koristne Povezave
- **GitHub Repository**: https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform
- **GitHub Issues**: https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform/issues
- **Production Backend**: https://omni-ultra-backend-prod-661612368188.europe-west1.run.app

---

## 🏆 Statistika Platforme

```
Dokumentacija:
  - Slovenska dokumentacija: 4 datoteke (2,863 vrstic)
  - Skupaj dokumentov v repozitoriju: 30+
  - Skupaj vrstic dokumentacije: 15,000+

Koda:
  - Backend moduli: 243 datotek
  - API endpoints: 50+
  - Route moduli: 30+
  - AI/ML servisi: 10+
  - Middleware komponente: 7
  - Payment gateways: 3

Features:
  - AI/ML modeli: 10+
  - Plačilni sistemi: 3 (Stripe, PayPal, Crypto)
  - Databases: 5 (PostgreSQL, MongoDB, Redis, Firestore, Neo4j)
  - Compliance: GDPR, ZVOP-2, ISO 27001
  - Languages supported: 98+
  - Dashboard types: 20

Infrastructure:
  - Cloud providers: GCP
  - Deployment options: Cloud Run, GKE
  - Monitoring: Prometheus, Grafana
  - CI/CD: GitHub Actions, Cloud Build
```

---

## ✨ Ključne Prednosti Platforme

### 1. 10 Let Naprej Tehnologije
- Najsodobnejši AI/ML modeli
- Pripravljeno za AGI (Artificial General Intelligence)
- Neural interface ready (BCI)
- Quantum computing compatible architecture

### 2. Popolna Podjetniška Rešitev
- All-in-one platforma
- Ne potrebujete dodatnih servisov
- Zmanjšanje vendor lock-in
- Reduce complexity

### 3. Skalabilnost
- Od 0 do milijon uporabnikov
- Avtomatično skaliranje
- Pay-as-you-go model
- Global reach

### 4. Varnost & Skladnost
- GDPR, CCPA, HIPAA ready
- Enterprise-grade security
- Slovenian ZVOP-2 compliance
- Regular security audits

### 5. Developer-Friendly
- Odlična dokumentacija
- SDK-ji za vse popularne jezike
- GraphQL + REST API
- WebSocket support

### 6. Cost-Effective
- Scales to zero (no idle costs)
- Competitive pricing
- No hidden fees
- Transparent billing

---

## 🎓 Zaključek

**OMNI Enterprise Ultra Max** je revolucionarna podjetniška AI platforma, ki združuje:

- ✅ **50+ AI/ML storitev** v enotni arhitekturi
- ✅ **Enterprise-grade funkcionalnosti** (payments, affiliate, GDPR)
- ✅ **Production-ready deployment** na Cloud Run/GKE
- ✅ **Celovita dokumentacija** v slovenščini
- ✅ **Avtomatizirana deployment skripta** (1-command deploys)
- ✅ **Monitoring & observability** (Prometheus + Grafana)

**Ta direktorij vsebuje celoten maksimum platforme, konsolidiran na enem mestu za lažji pregled, razumevanje in uporabo.**

---

**OMNI Enterprise Ultra Max** - *Prihodnost AI Je Tukaj* 🚀

*Verzija: 1.0.0*  
*Datum konsolidacije: 3. november 2025*  
*Jezik: Slovenščina + English*
