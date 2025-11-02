# QUICK START GUIDE - Implementation Steps
## Redis Caching + Observability

Pripravil sem implementacijo za Redis caching in observability. Tukaj so koraki za začetek:

---

## 1. REDIS CACHING (Quick Win - 2-3 ure)

### Korak 1: Deploy Redis (Cloud Memorystore)

```bash
# Cloud Memorystore (priporočeno za produkcijo)
gcloud redis instances create omni-cache \
  --size=1 \
  --region=europe-west1 \
  --tier=basic

# Dobite IP:
gcloud redis instances describe omni-cache \
  --region=europe-west1 \
  --format="value(host)"
```

**ALI za lokalni development:**

```bash
# Docker
docker run -d --name redis -p 6379:6379 redis:latest

# Ali z docker-compose
# Dodajte v docker-compose.yml:
services:
  redis:
    image: redis:latest
    ports:
      - "6379:6379"
```

### Korak 2: Nastavite environment variables

```bash
# V .env ali Cloud Run
REDIS_HOST=10.x.x.x  # IP iz Memorystore
REDIS_PORT=6379
# REDIS_PASSWORD=xxx  # če uporabljate
```

### Korak 3: Uporabite caching v routes

Odprite poljubno route file, npr. `backend/routes/ai_intelligence_routes.py`:

```python
# Na vrhu dodajte import
from utils.cache import cache_response

# Dodajte decorator na drage operacije
@router.post("/predict/revenue-lstm")
@cache_response(ttl=1800)  # 30 minut cache
async def predict_revenue_lstm(payload: LSTMForecastRequest):
    # Vaša obstoječa koda ostane enaka
    result = await lstm_service.train(...)
    return result

# Za HuggingFace search (dolgo traja)
@router.get("/huggingface/search")
@cache_response(ttl=3600, key_prefix="hf_search")  # 1 ura
async def search_models(query: str):
    results = await huggingface_hub.search(query)
    return results
```

### Korak 4: Dodajte cache statistics endpoint

V `backend/main.py` ali v `backend/routes/ai_routes.py`:

```python
from utils.cache import get_cache_stats

@app.get("/api/v1/cache/stats")
async def cache_stats():
    """Get cache hit rate and statistics"""
    return get_cache_stats()
```

### Korak 5: Test

```bash
# Restart backend
# Prvi request - MISS (počasno)
curl http://localhost:8080/api/v1/predict/revenue-lstm -d '{...}'

# Drugi request - HIT (hitro!)
curl http://localhost:8080/api/v1/predict/revenue-lstm -d '{...}'

# Statistika
curl http://localhost:8080/api/v1/cache/stats
```

**Pričakovani rezultat:** 50-70% reduction v response time in stroških!

---

## 2. OBSERVABILITY (Critical - 1-2 dni)

### Korak 1: Dodajte dependencies v requirements.txt

```bash
# Dodajte na konec backend/requirements.txt:
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-instrumentation-fastapi==0.42b0
opentelemetry-exporter-jaeger==1.21.0  # optional
opentelemetry-exporter-otlp==1.21.0     # optional
```

### Korak 2: Setup v main.py

Odprite `backend/main.py` in dodajte:

```python
# Na vrh
from middleware.telemetry import setup_telemetry, instrument_fastapi, TelemetryMiddleware
from middleware.metrics_enhanced import EnhancedMetricsMiddleware, get_metrics

# V lifespan funkcijo
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting OMNI Enterprise Ultra Max API...")
    
    # Setup telemetry
    setup_telemetry("omni-backend")
    
    await init_databases()
    logger.info("✅ All systems operational")
    yield
    await close_databases()

app = FastAPI(lifespan=lifespan)

# Po app creation
instrument_fastapi(app)

# Dodajte middleware (PRED obstoječimi)
app.add_middleware(TelemetryMiddleware)
app.add_middleware(EnhancedMetricsMiddleware)

# Dodajte metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics"""
    from starlette.responses import Response
    return Response(get_metrics(), media_type="text/plain")
```

### Korak 3: Environment variables

```bash
# Za Console output (development)
ENABLE_TELEMETRY=true
OTEL_EXPORTER=console

# Za Jaeger (če ga imate)
ENABLE_TELEMETRY=true
OTEL_EXPORTER=jaeger
JAEGER_HOST=localhost
JAEGER_PORT=6831
```

### Korak 4: Grafana Cloud (BREZPLAČNO)

1. Odprite https://grafana.com/auth/sign-up/create-user
2. Izberite "Free Forever" plan
3. Po prijavi:
   - Grafana Cloud → "Add Prometheus data source"
   - Kopirajte Remote Write URL
   - Generirajte API Key

4. V Cloud Run dodajte:
```bash
GRAFANA_CLOUD_URL=https://prometheus-xxx.grafana.net/api/prom/push
GRAFANA_CLOUD_USER=xxx
GRAFANA_CLOUD_KEY=xxx
```

### Korak 5: Dodajte tracking v ML operacijah

V `backend/routes/ai_intelligence_routes.py`:

```python
from middleware.metrics_enhanced import track_ml_prediction, track_revenue_event
import time

@router.post("/predict/revenue-lstm")
async def predict_revenue_lstm(request: Request, payload: LSTMForecastRequest):
    tenant_id = getattr(request.state, 'tenant_id', 'default')
    
    start = time.time()
    result = await lstm_service.train(...)
    duration = time.time() - start
    
    # Track metrics
    track_ml_prediction("lstm", tenant_id, duration)
    track_revenue_event(tenant_id, "ml_inference")
    
    return result
```

### Korak 6: Deploy in preveri

```bash
# Deploy
gcloud run deploy ...

# Check metrics
curl https://your-backend.run.app/metrics

# V Grafana Cloud boste videli:
# - http_requests_total
# - http_request_duration_seconds
# - ml_predictions_total
# - cache_operations_total
```

---

## 3. HITRI DASHBOARD (Grafana)

Ko imate Grafana Cloud, dodajte ta basic dashboard:

1. New Dashboard → Add visualization
2. Izberite Prometheus data source
3. Queries:

```promql
# Request rate
rate(http_requests_total[5m])

# Latency p95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# Cache hit rate
rate(cache_operations_total{result="hit"}[5m]) / 
rate(cache_operations_total[5m])

# ML predictions per tenant
sum by(tenant_id) (rate(ml_predictions_total[5m]))
```

---

## PRIORITETE (če ste sami):

### Dan 1: Redis (2-3 ure)
- ✅ Deploy Redis
- ✅ Dodajte caching na 5 najpočasnejših endpoints
- ✅ Test

### Dan 2: Metrics (2-3 ure)  
- ✅ Dodajte Prometheus metrics
- ✅ Setup Grafana Cloud
- ✅ Osnovni dashboard

### Dan 3: Tracing (opcijsko - 2 ure)
- ✅ Enable OpenTelemetry
- ✅ Dodajte na kritične ML operacije

---

## FILES CREATED:

1. `backend/utils/cache.py` - Redis caching decorator
2. `backend/middleware/telemetry.py` - OpenTelemetry setup
3. `backend/middleware/metrics_enhanced.py` - Enhanced Prometheus metrics
4. `QUICKSTART_IMPLEMENTATION.md` - Ta dokument

**Vse je pripravljeno za uporabo!** Samo sledite korakom zgoraj.

Če imate vprašanja pri kateremkoli koraku, vprašajte.
