# OMNI Platform - Lokalna Grafana Namestitev

## Pregled

Ta navodila opisujejo, kako nastaviti lokalno Docker Grafana instanco za razvoj in testiranje, ki prikazuje podatke iz vseh virov podatkov (GitHub, Google Cloud Run, Jira, OMNI API).

## Arhitektura

```
┌─────────────────────────────────────┐  
│  LOKALNA DOCKER GRAFANA             │  
│  (na vašem računalniku)             │  
│  ├─ Vsi dashboardi                  │  
│  ├─ Development/Testing             │  
│  └─ Polna kontrola                  │  
└─────────────────────────────────────┘  
            │  
            │ Prikazuje podatke iz:  
            ↓  
┌──────────────────────────────────────┐  
│  IZVORI PODATKOV (nespremenjeni)     │  
│  ├─ GitHub (code, commits, PRs)      │  
│  ├─ Google Cloud Run (metrics)      │  
│  ├─ Jira (issues, projects)         │  
│  └─ Vaša aplikacija (custom API)    │  
└──────────────────────────────────────┘  
            │  
            │ Isti podatki dostopni tudi za:  
            ↓  
┌─────────────────────────────────────┐  
│  GRAFANA CLOUD (tukaj)              │  
│  ├─ Backup/produkcijski dashboard   │  
│  ├─ 24/7 dostopnost                 │  
│  └─ Share z ekipo/klienti           │  
└─────────────────────────────────────┘
```

## Hitri Začetek

### 1. Priprava Okolja

```bash
# Kopiraj in nastavi environment spremenljivke
cp .env.example .env
# Uredi .env datoteko z vašimi dejanskimi vrednostmi
```

### 2. Zagon Lokalne Grafana

```bash
# Zagon z lokalnimi nastavitvami
docker-compose -f docker-compose.yml -f docker-compose.local.yml up -d

# Preveri status
docker-compose ps
```

### 3. Dostop do Grafana

- URL: http://localhost:3000
- Username: admin
- Password: admin123 (ali kot nastavljeno v .env)

## Konfiguracija Virov Podatkov

### GitHub
1. Ustvari Personal Access Token v GitHub Settings
2. Nastavi `GITHUB_TOKEN` v .env datoteki
3. Datasource se avtomatsko konfigurira

### Jira
1. Ustvari API Token v Jira Settings
2. Nastavi `JIRA_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN` v .env
3. Datasource se avtomatsko konfigurira

### Google Cloud
1. Ustvari Service Account v GCP Console
2. Prenesi JSON ključ in ga shrani kot `gcp-key.json`
3. Nastavi `GCP_PROJECT_ID` v .env
4. Datasource se avtomatsko konfigurira

### OMNI Platform APIs
1. Zagoni OMNI Platform storitve:
   ```bash
   # Backend API (port 8004)
   python backend/main.py
   
   # Hybrid AI (port 8080)
   python backend/omni_hybrid_ai.py
   
   # OMNI Director (port 3001)
   cd omni-search && npm start
   ```

## Dashboardi

### Lokalni Celoviti Dashboard
- **Ime**: OMNI Local Comprehensive Dashboard
- **Lokacija**: Local Development folder
- **Vsebuje**:
  - OMNI Platform Health
  - AI Providers Status
  - GitHub Repositories
  - Jira Issues by Status
  - Google Cloud Run Metrics
  - System Monitoring

### Obstoječi Dashboardi
- `omni_business.json` - Poslovni pregled
- `omni_business_integrations.json` - Integracije
- `omni_jira_professional.json` - Jira profesionalni
- `omni_unified_all.json` - Enotni pregled

## Grafana Cloud Sinhronizacija

### Nastavitev Backup/Production
1. Ustvari Grafana Cloud račun
2. Nastavi `GRAFANA_CLOUD_*` spremenljivke v .env
3. Uporabi Grafana API za sinhronizacijo dashboardov:

```bash
# Export lokalnega dashboarda
curl -H "Authorization: Bearer admin:admin123" \
     http://localhost:3000/api/dashboards/uid/omni_local_comprehensive

# Import v Grafana Cloud
curl -X POST \
     -H "Authorization: Bearer ${GRAFANA_CLOUD_API_KEY}" \
     -H "Content-Type: application/json" \
     -d @dashboard.json \
     ${GRAFANA_CLOUD_URL}/api/dashboards/db
```

## Troubleshooting

### Grafana se ne zažene
```bash
# Preveri loge
docker-compose logs omni-grafana

# Restart storitve
docker-compose restart omni-grafana
```

### Datasources ne delujejo
1. Preveri .env spremenljivke
2. Preveri network connectivity
3. Preveri API ključe in dovoljenja

### Dashboardi se ne naložijo
```bash
# Preveri mount points
docker-compose exec omni-grafana ls -la /var/lib/grafana/dashboards

# Restart z rebuild
docker-compose down
docker-compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
```

## Monitoring in Alerting

### Prometheus Metrics
- CPU, Memory, Disk usage
- Application metrics
- Custom OMNI metrics

### Loki Logs
- Application logs
- System logs
- Error tracking

### Tempo Tracing
- Request tracing
- Performance monitoring
- Distributed tracing

## Varnost

### Lokalni Razvoj
- Uporabi močna gesla
- Omeji dostop na localhost
- Redno posodobi Docker images

### Produkcija (Grafana Cloud)
- Uporabi HTTPS
- Nastavi proper authentication
- Omeji API dostop
- Redno backup dashboardov

## Dodatne Funkcionalnosti

### Custom Plugins
- Infinity Datasource za REST APIs
- Jira Plugin za issue tracking
- Google Cloud Monitoring
- GitHub Plugin za repository metrics

### Alerting
- Nastavi alerts za kritične metrije
- Integriraj z Slack/Teams
- Email notifikacije

## Podpora

Za vprašanja in podporo:
1. Preveri loge: `docker-compose logs`
2. Preveri dokumentacijo: `/docs`
3. Kontaktiraj OMNI Platform team