# 🚀 Grafana Monitoring Quick Start Guide (Slovenian)

**Pozdravljen!** Vaše Grafana spremljanje je pripravljeno! 🎉

## 🎯 Kaj je bilo implementirano

### 1. ✅ Metrike za predpomnilnik (Cache Monitoring)

- **Cache hit/miss metrike** - sledenje uspešnosti predpomnjenja
- **Redis metrike** - povezava, spomin, število ključev, povezani odjemalci
- **Velikost predpomnilnika** - število elementov v Redis in pomnilniških predpomnilnikih

**Koda:** 
- `gateway/app/response_cache.py` - dodane Prometheus metrike
- `gateway/app/redis_metrics.py` - zbiranje Redis metrik

### 2. ✅ Spremljanje FastAPI aplikacije

Metrike že obstajajo v:
- `gateway/app/metrics.py` - HTTP zahtevki, zakasnitev, napake
- `backend/middleware/metrics.py` - Backend HTTP metrike

### 3. ✅ Poslovne metrike

Že implementirano v:
- `gateway/app/business_metrics.py` - prihodki, uporabniki, ML modeli, funkcije

### 4. ✅ Grafana nadzorne plošče

Ustvarjene 3 obsežne nadzorne plošče:
- `dashboards/grafana-cache-monitoring.json` - Redis cache
- `dashboards/grafana-fastapi-monitoring.json` - API performance
- `dashboards/grafana-business-metrics.json` - Poslovne in ML metrike

### 5. ✅ Prometheus opozorila

Konfiguracijska datoteka z opozorili:
- `monitoring/prometheus-alerts.yml` - 20+ pravil opozoril

Vrste opozoril:
- Nizka stopnja zadetkov predpomnilnika (< 50% in < 20%)
- Redis nedostopen
- Visoka stopnja napak (> 1% in > 5%)
- Visoka zakasnitev (> 5s in > 10s)
- ML model napake in nizka točnost
- Padec prihodkov
- Nizko sodelovanje uporabnikov

## 🚀 Hitra namestitev

### Možnost 1: Docker Compose (priporočeno)

```bash
# Zagon celotne monitoring infrastrukture
docker-compose -f docker-compose.monitoring.yml up -d

# Dostop do storitev:
# - Grafana: http://localhost:3000 (admin/admin)
# - Prometheus: http://localhost:9090
# - Gateway metrike: http://localhost:8081/metrics
# - Backend metrike: http://localhost:8080/metrics
```

### Možnost 2: Obstoječa Prometheus/Grafana infrastruktura

1. **Konfiguriraj Prometheus** da zajema metrike:
   - Uporabi `monitoring/prometheus.yml` kot primer
   - Dodaj svoje storitve kot cilje (targets)

2. **Uvozi Grafana nadzorne plošče**:
   - Odpri Grafana → Dashboards → Import
   - Naloži vsako JSON datoteko iz `dashboards/`
   - Izberi svoj Prometheus data source

3. **Konfiguriraj opozorila**:
   - Kopiraj `monitoring/prometheus-alerts.yml` v Prometheus
   - Ponovno naloži Prometheus: `curl -X POST http://localhost:9090/-/reload`

## 📊 Pregled nadzornih plošč

### 1. Cache Monitoring Dashboard

**Ključne metrike:**
- Stopnja zadetkov predpomnilnika (%)
- Cache operacije na sekundo
- Redis spomin in število ključev
- Primerjava zakasnitev: predpomnjeno vs nepredpomnjeno

**Uporaba:**
- Spremljanje učinkovitosti cache
- Optimizacija TTL nastavitev
- Identifikacija težav s predpomnilnikom

### 2. FastAPI Application Dashboard

**Ključne metrike:**
- Hitrost zahtevkov (req/s)
- Stopnja napak (4xx, 5xx)
- Zakasnitev percentili (p50, p95, p99)
- Top 10 najpočasnejših končnih točk
- Porazdelitev po metodah

**Uporaba:**
- Identifikacija počasnih končnih točk
- Sledenje vzorcem napak
- Načrtovanje kapacitet

### 3. Business & ML Metrics Dashboard

**Ključne metrike:**
- Prihodki (skupaj, po nivoju, po funkciji)
- Aktivni uporabniki
- ML model točnost in zakasnitev
- Uporaba funkcij
- API klici po najemnikih

**Uporaba:**
- Spremljanje poslovnih KPI-jev
- Nadzor uspešnosti ML modelov
- Analiza sodelovanja uporabnikov

## 🚨 Opozorila

### Pomembna opozorila (Critical)

| Opozorilo | Prag | Opis |
|-----------|------|------|
| CriticallyLowCacheHitRate | < 20% za 5min | Cache skoraj ne deluje |
| RedisDown | 1min | Redis ni dosegljiv |
| HighErrorRate | > 5% za 5min | Visoka stopnja napak strežnika |
| CriticalLatency | > 10s za 5min | Kritična zakasnitev odziva |
| ServiceDown | 2min | Storitev ni dosegljiva |
| MLModelHighFailureRate | > 10% za 5min | Visoka stopnja napak modela |

### Opozorila (Warning)

| Opozorilo | Prag | Opis |
|-----------|------|------|
| LowCacheHitRate | < 50% za 10min | Nizka stopnja zadetkov |
| RedisHighMemoryUsage | > 90% za 5min | Redis visoka uporaba spomina |
| ElevatedErrorRate | > 1% za 10min | Povišana stopnja napak |
| HighLatency | > 5s za 10min | Visoka zakasnitev |
| MLModelLowAccuracy | < 70% za 15min | Nizka točnost modela |
| LowUserEngagement | < 30 za 30min | Nizko sodelovanje uporabnikov |

## 📚 Dokumentacija

**Popolna dokumentacija:** `dashboards/README-GRAFANA.md`

Vsebuje:
- Podrobne navodila za namestitev
- Konfiguracijske primere
- PromQL poizvedbe
- Odpravljanje težav
- Najboljše prakse

## 🔧 Konfiguracijske datoteke

```
monitoring/
├── prometheus.yml          # Prometheus konfiguracija
├── prometheus-alerts.yml   # Pravila opozoril
└── alertmanager.yml        # Alertmanager konfiguracija (obvestila)

dashboards/
├── grafana-cache-monitoring.json
├── grafana-fastapi-monitoring.json
├── grafana-business-metrics.json
└── README-GRAFANA.md       # Podrobna dokumentacija

docker-compose.monitoring.yml  # Celotna monitoring infrastruktura
```

## ✅ Preverjanje namestitve

Zaženi skripto za preverjanje:

```bash
python3 scripts/verify-monitoring.py
```

To bo preverilo:
- ✅ Vse metrike so pravilno definirane
- ✅ Vse nadzorne plošče obstajajo
- ✅ Vse konfiguracijske datoteke so veljavne
- ✅ Dokumentacija je prisotna

## 🎯 Naslednji koraki

1. **Zaženi monitoring infrastrukturo**
   ```bash
   docker-compose -f docker-compose.monitoring.yml up -d
   ```

2. **Dostopaj do Grafane**
   - Odpri: http://localhost:3000
   - Prijava: admin/admin
   - Uvozi nadzorne plošče

3. **Preveri metrike**
   - Gateway: http://localhost:8081/metrics
   - Backend: http://localhost:8080/metrics

4. **Konfiguriraj obvestila** (opcijsko)
   - Nastavi Slack/Email v `monitoring/alertmanager.yml`
   - Ponovno zaženi Alertmanager

## 🔍 Primer PromQL poizvedb

### Cache stopnja zadetkov
```promql
rate(cache_hits_total[5m]) / 
(rate(cache_hits_total[5m]) + rate(cache_misses_total[5m])) * 100
```

### API stopnja napak
```promql
sum(rate(http_requests_total{status=~"5.."}[5m])) /
sum(rate(http_requests_total[5m])) * 100
```

### P95 zakasnitev
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### Prihodki na uro
```promql
sum(increase(business_revenue_total_cents[1h])) / 100
```

## 💡 Najboljše prakse

1. **Ciljne vrednosti:**
   - Cache hit rate: > 80%
   - Error rate: < 1%
   - P95 latency: < 1s

2. **Optimizacija cache:**
   - Spremljaj cache hit rate dnevno
   - Prilagodi TTL glede na podatke
   - Uporabi cache warming za predvidljive vzorce

3. **Preprečevanje alarm fatigue:**
   - Začni s konservativnimi pragi
   - Pregleduj in prilagajaj opozorila tedensko
   - Usmerjaj različne resnosti v različne kanale

## 📞 Pomoč

Če potrebujete pomoč:
1. Preberite `dashboards/README-GRAFANA.md` - podrobna dokumentacija
2. Preverite Prometheus targets: http://localhost:9090/targets
3. Preverite metrike endpoints direktno
4. Preglejte service logs

---

**Srečno s spremljanjem! 🎉**

Vaša platforma ima zdaj profesionalno monitoring rešitev z:
- ✅ Redis cache spremljanje
- ✅ FastAPI performance metrics
- ✅ Poslovne in ML metrike
- ✅ Avtomatska opozorila
- ✅ Grafana nadzorne plošče
