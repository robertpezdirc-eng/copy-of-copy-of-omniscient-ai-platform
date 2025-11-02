# 🚀 DEPLOYMENT GUIDE - Redis & Grafana Setup
## Production Observability and Caching

Pripravil: AI Platform Architect  
Datum: November 2, 2025

---

## ✅ ŠE NAREDILI STE (v prejšnjih korakih):

1. ✅ Dodali Redis caching na 10+ endpoints
2. ✅ Integrirali OpenTelemetry tracing
3. ✅ Enhanced Prometheus metrics
4. ✅ Cache statistics endpoint

**Zdaj sledi:** Deploy Redis in setup Grafana za produkcijsko okolje

---

## 📦 KORAK 1: Deploy Redis na Google Cloud Memorystore (30 min)

### 1.1 Ustvarite Redis instanco

```bash
# Basic tier (za začetek, cenejše)
gcloud redis instances create omni-cache \
  --size=1 \
  --region=europe-west1 \
  --tier=basic \
  --redis-version=redis_6_x

# Ali Standard tier (za produkcijo, high availability)
gcloud redis instances create omni-cache-prod \
  --size=2 \
  --region=europe-west1 \
  --tier=standard-ha \
  --redis-version=redis_6_x
```

**Cene:**
- Basic (1GB): ~€25/mesec
- Standard HA (2GB): ~€80/mesec

### 1.2 Dobite Redis connection info

```bash
# Get host IP
gcloud redis instances describe omni-cache \
  --region=europe-west1 \
  --format="value(host)"

# Get port
gcloud redis instances describe omni-cache \
  --region=europe-west1 \
  --format="value(port)"

# Rezultat bo nekaj kot:
# Host: 10.20.30.40
# Port: 6379
```

### 1.3 Nastavite environment variables

**Za Cloud Run:**
```bash
gcloud run services update omni-ultra-backend \
  --region=europe-west1 \
  --set-env-vars="REDIS_HOST=10.20.30.40,REDIS_PORT=6379"
```

**Za GKE (kubernetes):**
```yaml
# V backend/k8s/deployment.yaml
env:
  - name: REDIS_HOST
    value: "10.20.30.40"
  - name: REDIS_PORT
    value: "6379"
```

**Za local development:**
```bash
# V .env file
REDIS_HOST=10.20.30.40
REDIS_PORT=6379

# Ali uporabite local Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 1.4 Test connection

```bash
# Deploy novo verzijo
gcloud run deploy omni-ultra-backend \
  --source . \
  --region=europe-west1

# Test cache endpoint
curl https://your-service.run.app/api/v1/cache/stats

# Expected response:
{
  "status": "connected",
  "total_cache_keys": 0,
  "keyspace_hits": 0,
  "keyspace_misses": 0,
  "hit_rate": 0.0,
  "db_keys": 0
}
```

---

## 📊 KORAK 2: Setup Grafana Cloud (BREZPLAČNO) (1-2 uri)

### 2.1 Ustvarite Grafana Cloud account

1. Pojdite na: https://grafana.com/auth/sign-up/create-user
2. Izberite "Free Forever" plan (vključuje):
   - 10,000 series metrics
   - 50GB logs
   - 14 days retention
   - 3 users
   - ✅ Popolnoma zadosti za vaš projekt!

### 2.2 Setup Prometheus Remote Write

Po prijavi:

1. V Grafana Cloud konzoli: **Grafana Cloud Portal → Prometheus**
2. Kliknite "Send Metrics" → "Via Prometheus Remote Write"
3. Kopirajte:
   - **Remote Write URL**: `https://prometheus-xxx.grafana.net/api/prom/push`
   - **Username**: `123456`
   - **Password/API Key**: generirajte nov API key

### 2.3 Configure backend to send metrics to Grafana

Dodajte v `backend/requirements.txt`:
```txt
# Že imate prometheus-client, dodajte samo:
requests>=2.31.0  # že imate
```

**Option A: Pushgateway (priporočeno za Cloud Run)**

Deploy Pushgateway:
```bash
# Local testing
docker run -d -p 9091:9091 prom/pushgateway

# Production - uporabite Cloud Run
gcloud run deploy pushgateway \
  --image=prom/pushgateway \
  --region=europe-west1 \
  --platform=managed \
  --allow-unauthenticated
```

Konfigurirajte metrics push:
```python
# V backend/middleware/metrics_enhanced.py dodajte
from prometheus_client import push_to_gateway, CollectorRegistry
import os

PUSHGATEWAY_URL = os.getenv("PUSHGATEWAY_URL", "localhost:9091")

# Push metrics every 60 seconds
async def push_metrics_periodically():
    while True:
        try:
            push_to_gateway(
                PUSHGATEWAY_URL,
                job='omni-backend',
                registry=registry
            )
        except Exception as e:
            logger.error(f"Failed to push metrics: {e}")
        await asyncio.sleep(60)
```

**Option B: Use Grafana Agent (bolj napredna rešitev)**

Če želite direct integration brez Pushgateway, sledite: https://grafana.com/docs/agent/

### 2.4 Import ready-made dashboards

V Grafana UI:

1. **Dashboard → Import**
2. Uporabite te dashboard IDs (pre-built za FastAPI):
   - **FastAPI Dashboard**: ID `14695`
   - **Redis Dashboard**: ID `11835`
   - **Prometheus 2.0**: ID `3662`

3. **Ali ustvarite custom dashboard:**

```json
{
  "dashboard": {
    "title": "Omni Platform Metrics",
    "panels": [
      {
        "title": "Cache Hit Rate",
        "targets": [{
          "expr": "rate(cache_operations_total{result='hit'}[5m]) / rate(cache_operations_total[5m]) * 100"
        }]
      },
      {
        "title": "API Request Rate",
        "targets": [{
          "expr": "rate(http_requests_total[5m])"
        }]
      },
      {
        "title": "API Latency (p95)",
        "targets": [{
          "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
        }]
      },
      {
        "title": "ML Predictions per Minute",
        "targets": [{
          "expr": "rate(ml_predictions_total[1m]) * 60"
        }]
      },
      {
        "title": "Error Rate",
        "targets": [{
          "expr": "rate(http_requests_total{status=~'5..'}[5m])"
        }]
      }
    ]
  }
}
```

### 2.5 Setup Alerting (opcijsko, ampak priporočeno)

V Grafana Cloud → Alerting:

**Alert 1: High Error Rate**
```yaml
Query: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
Condition: Error rate > 1%
Alert when: For 5 minutes
Notify: Email / Slack
```

**Alert 2: Cache Unavailable**
```yaml
Query: up{job="omni-backend"} == 0
Condition: Service down
Alert when: For 1 minute
Notify: Email / SMS / PagerDuty
```

**Alert 3: High Latency**
```yaml
Query: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
Condition: p95 latency > 2 seconds
Alert when: For 10 minutes
Notify: Email
```

---

## 🎯 KORAK 3: Verify Everything Works

### 3.1 Test caching

```bash
# First request (cache MISS)
time curl https://your-service.run.app/api/intelligence/predictions/revenue

# Second request (cache HIT - should be instant)
time curl https://your-service.run.app/api/intelligence/predictions/revenue

# Check cache stats
curl https://your-service.run.app/api/v1/cache/stats
```

**Pričakovan rezultat:**
- First request: 1-2 seconds
- Second request: 50-100ms (20x faster!)
- Cache stats: hit_rate increasing

### 3.2 Check Grafana dashboards

1. Odprite Grafana Cloud
2. Pojdite na vaš dashboard
3. Bi morali videti:
   - ✅ Request rate naraščajoč
   - ✅ Cache hit rate (začne pri 0%, naraste na 60-80%)
   - ✅ Latency pada (zaradi cachinga)
   - ✅ ML predictions tracked

### 3.3 Monitor logs

```bash
# Cloud Run logs
gcloud run services logs read omni-ultra-backend \
  --region=europe-west1 \
  --limit=50

# Poiščite:
# "✅ Redis connected: 10.20.30.40:6379"
# "🎯 Cache HIT: get_revenue_predictions"
# "📊 Using Console exporter for traces"
```

---

## 📈 PRIČAKOVANI REZULTATI (po deploy-u)

### Performance Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Average Latency** | 2000ms | 400ms | 80% faster |
| **Cache Hit Rate** | 0% | 70% | ✅ |
| **Cost per 1M requests** | $100 | $30 | 70% cheaper |
| **p95 Latency** | 5000ms | 800ms | 84% faster |
| **Error Detection Time** | Hours | 5 minutes | 98% faster |

### Cost Savings (mesečno)

```
Requests per month: 10M
Cost before caching: 10M * $0.00001 = $100
Cost with 70% cache hit: 3M * $0.00001 = $30
Redis Memorystore: $25/month
─────────────────────────────────────────
Net savings: $45/month
```

**Pri 100M requests/month:** Prihranite $500+/mesec!

---

## 🐛 TROUBLESHOOTING

### Problem: Redis connection failed

```bash
# Check if Redis is accessible from Cloud Run
gcloud redis instances describe omni-cache --region=europe-west1

# Check VPC connector (if needed)
gcloud compute networks vpc-access connectors list

# Create VPC connector if missing
gcloud compute networks vpc-access connectors create omni-connector \
  --region=europe-west1 \
  --range=10.8.0.0/28
```

### Problem: Metrics ne prihajajo v Grafana

1. Check Prometheus endpoint:
```bash
curl https://your-service.run.app/metrics
```

2. Preverite če so metrics v pravilnem formatu:
```
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/health",status="200"} 1234
```

3. Check Pushgateway logs (če uporabljate):
```bash
gcloud run services logs read pushgateway --region=europe-west1
```

### Problem: Cache hit rate is 0%

1. Check Redis connection:
```bash
curl https://your-service.run.app/api/v1/cache/stats
```

2. Check environment variables:
```bash
gcloud run services describe omni-ultra-backend \
  --region=europe-west1 \
  --format="value(spec.template.spec.containers[0].env)"
```

3. Check logs for cache operations:
```bash
gcloud run services logs read omni-ultra-backend \
  --region=europe-west1 \
  | grep -i cache
```

---

## 🎓 NEXT STEPS

Po uspešnem deployment:

**Kratkoročno (ta teden):**
1. ✅ Monitor cache hit rate v Grafani
2. ✅ Dodajte več cached endpoints (cilj: 15-20)
3. ✅ Setup alerts za critical metrics

**Srednjeročno (naslednji teden):**
1. Multi-tenancy middleware
2. Tenant-specific quota enforcement
3. Usage-based billing tracking

**Dolgoročno (naslednji mesec):**
1. Auto-scaling based on metrics
2. Advanced caching strategies (cache warming)
3. Distributed tracing with Jaeger

---

## 📞 Support

Če imate težave:

1. Check logs: `gcloud run services logs read omni-ultra-backend`
2. Check metrics: `curl https://your-service/metrics`
3. Check cache stats: `curl https://your-service/api/v1/cache/stats`
4. Vprašajte v komentarjih PR-ja

---

**Status:** ✅ Redis deployment ready  
**Status:** ✅ Grafana Cloud ready  
**Status:** ⏳ Awaiting your deployment

**Predvideno trajanje:** 30 min (Redis) + 1 ura (Grafana) = **1.5 uri skupaj**

---

*Prepared by: AI Platform Architect*  
*Last Updated: November 2, 2025*
