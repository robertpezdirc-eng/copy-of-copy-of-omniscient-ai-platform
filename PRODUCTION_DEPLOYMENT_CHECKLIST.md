# 🚀 Production Deployment Checklist

Celoten deployment plan za vse implementirane features. Sledite korakom za uspešen production launch.

---

## ✅ Predpogoji (5 min)

- [ ] Google Cloud Project ID: `refined-graph-471712-n9`
- [ ] Region: `europe-west1`
- [ ] gcloud CLI nameščen in konfiguriran
- [ ] Docker nameščen lokalno
- [ ] Git repository kloniran

```bash
# Preveri gcloud config
gcloud config list

# Preveri Docker
docker --version

# Preveri Git
git status
```

---

## 📦 Korak 1: Deploy Redis (30 min)

### 1.1 Ustvari Cloud Memorystore instance

```bash
gcloud redis instances create omni-cache \
  --size=1 \
  --region=europe-west1 \
  --tier=basic \
  --redis-version=redis_6_x \
  --project=refined-graph-471712-n9
```

### 1.2 Pridobi connection details

```bash
gcloud redis instances describe omni-cache \
  --region=europe-west1 \
  --project=refined-graph-471712-n9 \
  --format="value(host,port)"
```

### 1.3 Testiraj povezavo

```bash
# Set environment variable
export REDIS_HOST=<host-from-above>
export REDIS_PORT=<port-from-above>

# Test locally
redis-cli -h $REDIS_HOST -p $REDIS_PORT ping
# Expected: PONG
```

**✅ Checkpoint:** Redis vrne "PONG"

---

## 📊 Korak 2: Setup Grafana Cloud (1 ura)

### 2.1 Ustvari Grafana Cloud account

1. Obiščite: https://grafana.com/auth/sign-up
2. Izberite Free tier
3. Potrdite email

### 2.2 Pridobi credentials

1. Login v Grafana Cloud
2. Navigate: Administration > Data sources > Prometheus
3. Kopirajte:
   - Remote Write URL: `https://prometheus-prod-XX-YY.grafana.net/api/prom/push`
   - Instance ID: `123456`
   - API Key: Ustvari novo ali uporabi obstoječo

### 2.3 Konfiguriraj Prometheus forwarding

```bash
cd grafana/
./setup-grafana-cloud.sh
```

Script bo vprašal za:
- Grafana Cloud Remote Write URL
- Instance ID (username)
- API Key

### 2.4 Start Prometheus container

```bash
docker-compose up -d
```

### 2.5 Preveri da metrics tečejo

```bash
# Check container status
docker ps | grep prometheus

# Check logs
docker logs grafana-prometheus-1

# Wait 30 seconds, then check Grafana Cloud
# Go to Explore > Prometheus
# Query: {job="omni-backend"}
```

**✅ Checkpoint:** Vidite metrics v Grafana Cloud Explorer

---

## 📈 Korak 3: Import Grafana Dashboards (30 min)

### 3.1 Automated import

```bash
cd grafana/
./import-dashboards.sh
```

Script bo uvozil vseh 6 dashboardov:
1. System Health
2. API Usage
3. ML Performance
4. Revenue Analytics
5. Affiliate Tracking
6. Security Events

### 3.2 Manual verification

1. Login v Grafana Cloud
2. Navigate: Dashboards
3. Preveri da vseh 6 dashboardov obstaja
4. Odpri vsak dashboard in preveri da se podatki nalagajo

**✅ Checkpoint:** Vseh 6 dashboardov prikazuje data

---

## 🔐 Korak 4: Enable Multi-Tenancy (5 min)

### 4.1 Set environment variable

```bash
export ENABLE_MULTI_TENANCY=true
```

### 4.2 Update Cloud Run environment

```bash
gcloud run services update omni-ultra-backend \
  --set-env-vars ENABLE_MULTI_TENANCY=true \
  --region=europe-west1 \
  --project=refined-graph-471712-n9
```

### 4.3 Test tenant endpoints

```bash
# Test with demo API key
curl -H "Authorization: Bearer demo-key-tenant-a" \
  https://your-backend-url/api/v1/tenant/usage

# Expected: JSON response with tenant quotas
```

**✅ Checkpoint:** API vrne tenant usage data

---

## 🐛 Korak 5: Configure Sentry (15 min)

### 5.1 Ustvari Sentry project

1. Obiščite: https://sentry.io/signup/
2. Ustvari novo project
3. Izberite platform: Python

### 5.2 Kopiraj DSN

Format: `https://xxxxx@yyy.ingest.sentry.io/zzzzz`

### 5.3 Set environment variables

```bash
export SENTRY_DSN=https://xxxxx@yyy.ingest.sentry.io/zzzzz
export SENTRY_ENVIRONMENT=production
export SENTRY_TRACES_SAMPLE_RATE=0.1
```

### 5.4 Update Cloud Run

```bash
gcloud run services update omni-ultra-backend \
  --set-env-vars SENTRY_DSN=$SENTRY_DSN,SENTRY_ENVIRONMENT=production,SENTRY_TRACES_SAMPLE_RATE=0.1 \
  --region=europe-west1 \
  --project=refined-graph-471712-n9
```

### 5.5 Test error tracking

```bash
# Trigger test error
curl https://your-backend-url/api/test-error

# Check Sentry dashboard
# Navigate to Issues - you should see the test error
```

**✅ Checkpoint:** Error je viden v Sentry dashboard

---

## 🚀 Korak 6: Deploy Updated Backend (20 min)

### 6.1 Update environment variables v Cloud Run

```bash
gcloud run services update omni-ultra-backend \
  --set-env-vars \
    REDIS_HOST=$REDIS_HOST,\
    REDIS_PORT=$REDIS_PORT,\
    ENABLE_MULTI_TENANCY=true,\
    SENTRY_DSN=$SENTRY_DSN,\
    SENTRY_ENVIRONMENT=production \
  --region=europe-west1 \
  --project=refined-graph-471712-n9
```

### 6.2 Deploy latest code

```bash
# From repo root
gcloud builds submit \
  --config=cloudbuild-backend.yaml \
  --substitutions=_PROJECT_ID=refined-graph-471712-n9,_TAG=latest \
  --project=refined-graph-471712-n9
```

### 6.3 Wait for deployment

```bash
gcloud run services describe omni-ultra-backend \
  --region=europe-west1 \
  --project=refined-graph-471712-n9 \
  --format="value(status.url)"
```

**✅ Checkpoint:** Service je running in dostopen

---

## 🧪 Korak 7: Validation Tests (30 min)

### 7.1 Test caching

```bash
# First call (cache miss)
time curl https://your-backend-url/api/intelligence/predictions/revenue

# Second call (cache hit - should be instant)
time curl https://your-backend-url/api/intelligence/predictions/revenue

# Check cache stats
curl https://your-backend-url/api/v1/cache/stats
```

**Expected:**
- First call: ~500ms
- Second call: ~50ms (10x faster)
- Cache hit rate: >0%

### 7.2 Test multi-tenancy

```bash
# Test tenant A
curl -H "Authorization: Bearer demo-key-tenant-a" \
  https://your-backend-url/api/v1/tenant/usage

# Test tenant B
curl -H "Authorization: Bearer demo-key-tenant-b" \
  https://your-backend-url/api/v1/tenant/usage

# Test quota enforcement (make 101 requests to exceed free tier)
for i in {1..101}; do
  curl -H "Authorization: Bearer demo-key-tenant-a" \
    https://your-backend-url/api/intelligence/predictions/revenue
done
```

**Expected:**
- Tenant A in B imata različne usage numbers
- 101. request vrne 429 Too Many Requests

### 7.3 Test observability

```bash
# Check Prometheus metrics
curl https://your-backend-url/metrics | grep cache_hit_rate

# Check Grafana dashboards
# Open Grafana Cloud > Dashboards > System Health
# Verify metrics are flowing
```

**Expected:**
- Metrics endpoint vrne Prometheus format
- Grafana dashboards prikazujejo live data

### 7.4 Test error tracking

```bash
# Trigger intentional error
curl https://your-backend-url/api/intentional-error

# Check Sentry
# Navigate to Issues - should see new error in <1 minute
```

**Expected:**
- Error je viden v Sentry dashboard
- Stack trace je prikazan
- Tenant context je v tagih

**✅ Checkpoint:** Vsi 4 testi uspešni

---

## 📝 Korak 8: SDK Publishing (Optional - 1 ura)

### 8.1 Python SDK na PyPI

```bash
cd sdks/python/

# Install build tools
pip install build twine

# Build distribution
python -m build

# Upload to PyPI (requires account)
twine upload dist/*
```

### 8.2 JavaScript SDK na NPM

```bash
cd sdks/javascript/

# Build
npm run build

# Publish (requires npm account)
npm publish --access public
```

**✅ Checkpoint:** SDKs so dostopni na PyPI in NPM

---

## 📋 Korak 9: Final Verification (15 min)

### 9.1 Complete feature checklist

- [ ] ✅ Redis caching aktiven (70% hit rate)
- [ ] ✅ Grafana Cloud povezan (6 dashboards)
- [ ] ✅ Multi-tenancy enabled (tenant isolation)
- [ ] ✅ Sentry error tracking (real-time alerts)
- [ ] ✅ Prometheus metrics (35+ metrics)
- [ ] ✅ Backend deployed na Cloud Run
- [ ] ✅ Vsi validation testi uspešni

### 9.2 Performance verification

```bash
# Run load test (100 concurrent requests)
ab -n 1000 -c 100 https://your-backend-url/api/intelligence/predictions/revenue
```

**Expected:**
- Requests per second: >100
- Mean response time: <500ms (with cache)
- Failed requests: 0

### 9.3 Cost verification

```bash
# Check Cloud Run costs
gcloud billing accounts list

# Expected monthly costs:
# - Cloud Run: $20-50
# - Redis: $25-40
# - Cloud Build: $5-10
# - Total: ~$50-100/month
```

**✅ Checkpoint:** Vsi features delujejo v production

---

## 🎉 Success Criteria

Platform je production-ready ko:

1. **Caching** - Cache hit rate >70%, latency reduction >80%
2. **Observability** - Vseh 6 Grafana dashboards prikazuje data
3. **Multi-tenancy** - Tenant isolation deluje, quota enforcement active
4. **Error Tracking** - Sentry beleži errors v <1 minuti
5. **Performance** - >100 req/sec, <500ms p95 latency
6. **Cost** - Monthly run rate <$100

---

## 🚨 Troubleshooting

### Redis connection issues

```bash
# Check Redis instance status
gcloud redis instances describe omni-cache \
  --region=europe-west1 \
  --project=refined-graph-471712-n9

# Check network connectivity from Cloud Run
# Add to Cloud Run service: --vpc-connector=your-connector
```

### Grafana ne prikazuje metrics

```bash
# Check Prometheus container logs
docker logs grafana-prometheus-1

# Check remote_write configuration
cat grafana/prometheus.yml | grep remote_write

# Test remote_write URL
curl -X POST $GRAFANA_REMOTE_WRITE_URL \
  -H "Authorization: Bearer $GRAFANA_API_KEY"
```

### Multi-tenancy ne deluje

```bash
# Check environment variable je set
gcloud run services describe omni-ultra-backend \
  --region=europe-west1 \
  --format="value(spec.template.spec.containers[0].env)"

# Check backend logs
gcloud logging read "resource.type=cloud_run_revision" \
  --limit=50 \
  --project=refined-graph-471712-n9
```

### Sentry ne beleži errors

```bash
# Check DSN je valid
curl -I $SENTRY_DSN

# Check environment variable
echo $SENTRY_DSN

# Test with Python script
python -c "import sentry_sdk; sentry_sdk.init('$SENTRY_DSN'); 1/0"
```

---

## 📞 Support

**Vprašanja?**
- GitHub Issues: https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform/issues
- Documentation: Glej `/DEPLOYMENT_GUIDE_REDIS_GRAFANA.md`, `/MULTI_TENANCY_GUIDE.md`

**Next Steps:**
- Monitor dashboards prvih 24 ur
- Adjust cache TTLs based on usage patterns
- Configure additional alerts v Grafana
- Scale Redis instance če je potrebno

---

**🎯 Target completion time: 3-4 hours**

**💰 Estimated monthly cost: $50-100**

**📈 Expected improvements:**
- 70-80% cost reduction (caching)
- 99.9% uptime (observability)
- Scale to 1000+ tenants (multi-tenancy)
- <1 min error detection (Sentry)
