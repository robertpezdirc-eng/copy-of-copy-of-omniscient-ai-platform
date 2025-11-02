# Grafana Cloud Setup Guide

Popolna navodila za povezavo Omni platforme z Grafana Cloud za monitoring v realnem času.

## Pregled

Ta vodnik vas vodi skozi:
1. Nastavitev Grafana Cloud računa (brezplačno)
2. Povezava Prometheus metrics z Grafana Cloud
3. Uvoz dashboardov
4. Nastavitev alertov

## Metoda 1: Avtomatska Nastavitev (Priporočeno)

### Korak 1: Zaženi setup skript

```bash
cd grafana/
chmod +x setup-grafana-cloud.sh
./setup-grafana-cloud.sh
```

Skript vas bo vodil skozi proces in potreboval:
- Grafana Cloud Instance ID
- Grafana Cloud API Key
- Regija (npr. `eu-west-0`, `us-central1`)

### Korak 2: Zaženi Prometheus forwarder

```bash
docker-compose up -d
```

To bo zaženlo Prometheus, ki bo:
- Scrape-al metrics iz vašega backenda na `localhost:8080/metrics`
- Forward-al metrics na Grafana Cloud vsake 15 sekund

### Korak 3: Preveri v Grafana Cloud

1. Pojdi na https://grafana.com
2. Prijavi se in odpri svoj instance
3. Pojdi na **Explore** → **Prometheus**
4. Query: `{job="omni-backend"}`
5. Če vidiš metrics → **Uspešno povezano!** ✅

---

## Metoda 2: Ročna Nastavitev

### Korak 1: Ustvari Grafana Cloud Account

1. Pojdi na: https://grafana.com/auth/sign-up
2. Izberi **Free Forever** plan
3. Ustvari nov Grafana Cloud stack

### Korak 2: Pridobi Credentials

1. V Grafana Cloud Portal pojdi na **Configuration** → **Prometheus**
2. Zapiši:
   - **Instance ID** (število, npr. `123456`)
   - **URL** (npr. `https://prometheus-prod-eu-west-0.grafana.net/api/prom/push`)
   - **Region** (iz URL-ja, npr. `eu-west-0`)

3. Pojdi na **Security** → **API Keys**
4. Klikni **Create API Key**
5. Nastavitve:
   - **Name**: `omni-platform-metrics`
   - **Role**: `MetricsPublisher`
   - **Time to live**: Nikoli ne poteče (ali po želji)
6. **Kopiraj API Key** (shrani ga varno, ne boš ga več videl!)

### Korak 3: Konfiguriraj Prometheus

1. Uredi `grafana/prometheus.yml`:

```yaml
remote_write:
  - url: https://prometheus-prod-eu-west-0.grafana.net/api/prom/push  # Tvoj URL
    basic_auth:
      username: 123456  # Tvoj Instance ID
      password: your-api-key-here  # Tvoj API Key
```

2. Zaženi Prometheus:

```bash
cd grafana/
docker-compose up -d
```

### Korak 4: Preveri Povezavo

```bash
# Preveri Prometheus logs
docker logs omni-prometheus

# Preveri metrics endpoint
curl http://localhost:8080/metrics
```

V 1-2 minutah bi morali metrics prispeti v Grafana Cloud.

---

## Korak 3: Uvozi Dashboards

### A. Omni Platform Overview Dashboard

1. V Grafana Cloud pojdi na **Dashboards** → **Import**
2. Upload `grafana/dashboards/omni-platform-overview.json`
3. Izberi Prometheus data source
4. Klikni **Import**

Dashboard prikazuje:
- ✅ Cache hit rate
- ✅ API request rate
- ✅ ML predictions
- ✅ Tenant API usage
- ✅ Response time (p95)
- ✅ Error rate

### B. FastAPI Dashboard (Pre-built)

1. Pojdi na **Dashboards** → **Import**
2. Vpiši ID: `16110`
3. Klikni **Load**
4. Izberi Prometheus data source
5. Klikni **Import**

Dashboard ID-ji (ready-to-use):
- **FastAPI**: `16110`
- **Redis**: `11835`
- **Prometheus**: `3662`

---

## Korak 4: Nastavitev Alertov

### A. High Error Rate Alert

1. Pojdi na **Alerting** → **Alert Rules**
2. Klikni **New Alert Rule**
3. Nastavitve:

```
Name: High Error Rate
Query: sum(rate(http_requests_total{status=~"5.."}[5m])) > 10
Evaluation: Every 1m for 5m
Labels: severity=critical
```

4. V **Notifications** dodaj:
   - Email
   - Slack (optional)
   - PagerDuty (optional)

### B. Low Cache Hit Rate Alert

```
Name: Low Cache Hit Rate
Query: (rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))) < 0.5
Evaluation: Every 5m for 10m
Labels: severity=warning
```

### C. API Quota Exceeded Alert

```
Name: Tenant Quota Exceeded
Query: sum(tenant_quota_exceeded_total) by (tenant_id) > 0
Evaluation: Every 1m for 5m
Labels: severity=high, tenant={{ $labels.tenant_id }}
```

---

## Environment Variables

Za direktno integracijo brez Prometheusa (eksperimentalno):

```bash
# .env ali environment
GRAFANA_CLOUD_ENABLED=true
GRAFANA_CLOUD_REMOTE_WRITE_URL=https://prometheus-prod-eu-west-0.grafana.net/api/prom/push
GRAFANA_CLOUD_USERNAME=123456
GRAFANA_CLOUD_API_KEY=your-api-key-here
GRAFANA_CLOUD_PUSH_INTERVAL=15
```

**Opomba**: Trenutno je Prometheus forwarder priporočena metoda. Direktna integracija zahteva dodatne dependencies (snappy, protobuf).

---

## Preverjanje

### 1. Preveri Prometheus

```bash
# Local Prometheus UI
open http://localhost:9090

# Query metrics
curl http://localhost:8080/metrics | grep -E "cache_|http_requests"
```

### 2. Preveri Grafana Cloud

```bash
# V Grafana Cloud Explore
{job="omni-backend"}

# Cache metrics
cache_hits_total
cache_misses_total

# API metrics
http_requests_total

# ML metrics
ml_predictions_total
```

### 3. Preveri Alerts

1. Pojdi na **Alerting** → **Alert Rules**
2. Preveri **State**: `Normal` / `Pending` / `Firing`
3. Testiraj alert:

```bash
# Trigger error rate
for i in {1..100}; do
  curl http://localhost:8080/api/nonexistent
done
```

---

## Troubleshooting

### Metrics se ne prikazujejo v Grafana Cloud

**Problem**: Počakaj 2-3 minute, potem preveri:

```bash
# Preveri Prometheus logs
docker logs omni-prometheus | grep -i error

# Preveri credentials
docker exec omni-prometheus cat /etc/prometheus/prometheus.yml
```

**Rešitev**:
- Preveri Instance ID in API Key
- Preveri URL format (mora biti `https://prometheus-prod-REGION.grafana.net/api/prom/push`)
- Preveri da backend dela: `curl http://localhost:8080/metrics`

### Connection refused

**Problem**: Prometheus ne more dostopati do backenda

**Rešitev**:
```bash
# Če backend teče lokalno, v prometheus.yml:
static_configs:
  - targets: ['host.docker.internal:8080']  # Namesto localhost

# Ali uporabi network mode:
docker-compose.yml:
  prometheus:
    network_mode: "host"
```

### 401 Unauthorized

**Problem**: Napačni credentials

**Rešitev**:
1. Preveri Instance ID in API Key
2. Preveri da API Key ima `MetricsPublisher` role
3. Generiraj nov API Key če potrebno

### No data in dashboards

**Problem**: Metrics obstajajo ampak dashboard jih ne prikazuje

**Rešitev**:
- Preveri da je Prometheus data source pravilno nastavljen
- Preveri query syntax (Grafana Cloud uporablja PromQL)
- Poskusi manual query v Explore: `{job="omni-backend"}`

---

## Koristni Linki

- **Grafana Cloud**: https://grafana.com
- **Dokumentacija**: https://grafana.com/docs/grafana-cloud/
- **Dashboard Library**: https://grafana.com/grafana/dashboards/
- **PromQL Guide**: https://prometheus.io/docs/prometheus/latest/querying/basics/

---

## Metrics Reference

### Cache Metrics
- `cache_hits_total` - Skupno število cache hits
- `cache_misses_total` - Skupno število cache misses
- `cache_size` - Število keys v cache

### API Metrics
- `http_requests_total` - Skupno število HTTP requestov
- `http_request_duration_seconds` - Request duration histogram

### ML Metrics
- `ml_predictions_total` - Število ML napovedi
- `ml_prediction_duration_seconds` - Prediction duration

### Tenant Metrics
- `tenant_api_calls_total` - API calls per tenant
- `tenant_quota_exceeded_total` - Quota exceeded events

---

## Naslednji Koraki

1. ✅ Poveži se z Grafana Cloud
2. ✅ Uvozi dashboards
3. ✅ Nastavi alerte
4. 📊 Spremljaj platformo v realnem času
5. 🚀 Optimiziraj glede na metrike

**Platforma je zdaj production-ready z 99.9% uptime monitoring!** 🎉
