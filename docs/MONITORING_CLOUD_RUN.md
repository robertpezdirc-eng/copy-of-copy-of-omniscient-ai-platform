# Monitoring in alerti za Cloud Run (omni-unified-platform)

Ta dokument vas vodi skozi ključne korake za vzpostavitev spremljanja (uptime checks, alert policies, logi, dashboard) za Cloud Run storitev.

## 1) Uptime Check
Uptime check periodično preverja dosegljivost HTTP endpointa (npr. /health).

- Endpoint: https://omni-unified-platform-661612368188.europe-west1.run.app/health
- Interval: 1 min
- Timeout: 10 s

Konfiguracija prek konzole:
- Odprite Google Cloud Console -> Monitoring -> Uptime checks -> Create check
- Target: URL
- URL: zgornji /health endpoint
- Regions: EU, US
- Alerting: povezava na obstoječi ali novo notification channel (email)

## 2) Alert Policies
Nastavite alert, če uptime check pade (npr. zadnjih 5 min neuspeh).

- Console: Monitoring -> Alerting -> Create policy
- Condition: Uptime check status == failed v vsaj 2 od 3 lokacij
- Notification channels: email ali Slack webhook

## 3) Log-based Metrics (opcijsko)
- Odprite Logging -> Log Explorer
- Filtrirajte `resource.type="cloud_run_revision"` in `severity>=ERROR`
- Create Metric -> Counter (npr. omni_run_errors)
- Alerting: Alert policy, ko `omni_run_errors` > 5 v 5 minutah

## 4) Dashboard
- Monitoring -> Dashboards -> Create
- Dodajte grafe:
  - Uptime check status
  - Latency (Cloud Run request latencies)
  - Error rate (HTTP 5xx)
  - Custom metrics (/metrics endpoint)

## 5) Prometheus /metrics
Backend izpostavlja `/metrics` z osnovnimi SSE metrikami. Če uporabljate Prometheus, dodajte scrape job:

```
- job_name: 'omni-unified-platform'
  scrape_interval: 30s
  metrics_path: /metrics
  static_configs:
    - targets: ['omni-unified-platform-661612368188.europe-west1.run.app']
```

## 6) Operativa
- Teden: pregled logov (Errors, Warnings)
- Mesec: review alert policies, pragov, notification kanali
- Incident: zapis incidentov in ukrepov (post-mortem)

## 7) CORS in domena
Če dodate custom domeno na Firebase Hosting, posodobite Cloud Run env:
- OMNI_FRONTEND_ORIGIN: https://vaša-domena
- ali dodajte več domen v `OMNI_FRONTEND_EXTRA_ORIGINS`, ločeno z vejicami.