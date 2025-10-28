# OPERATIONS RUNBOOK: Omni Platform Stabilization

## Purpose
Hitro stabilizirati platformo do cilja 2.000.000€ vrednosti z opazovanjem, opozarjanjem in odzivom.

## KPI Metrics
- `omni_revenue_eur`: skupni prihodki v EUR (gauge)
- `omni_active_users`: aktivni uporabniki (gauge)
- `omni_conversion_rate`: konverzija 0..1 (gauge)

## Exporter
- Lokacija: `exporters/revenue_exporter.py`
- Endpoint: `http://<host>:9101/metrics`
- Konfiguracija: `KPI_FILE=/data/business_kpis.json`, `POLL_SECONDS=10`
- Docker: `docker-compose.kpi.yml`

## Prometheus Alerts
- Datoteke: `alerts/revenue.rules.yml`, `alerts/availability.rules.yml`
- Naloži v Prometheus preko `rule_files` konfiguracije
- Kritične:
  - `RevenueDropDetected`: >30% padec proti 24h povprečju
  - `HighErrorRate5xx`: >5% 5xx napak 10m

## Grafana Dashboards
- Business KPI: `grafana/dashboards/business_kpi_overview.json`
- Production Overview v2: `grafana/dashboards/omni_production_overview_v2.json`
- Uvozi preko Grafana UI (Dashboards -> Import)

## Playbooks
- Revenue Drop:
  1) Preveri `omni_revenue_eur` trend in recent deploye
  2) Preveri 5xx in P95 latenco; če povišani, rollback zadnjega releasa
  3) Preveri plačilne prehode / API ključe; re-generiraj ključe ob napaki
- High Error Rate:
  1) Identificiraj storitev z najvišjimi 5xx
  2) Scale up ali rollback; preveri DB povezave
  3) Aktiviraj obvoz (feature flag) za problematičen modul

## Procedures
- Release Quality Gate:
  - Pred produkcijo zaženi smoke teste (health, plačila, prijava)
  - Če kateri pade, blokiraj release in ustvarjaj incident
- Incident Response:
  - PagerDuty/Alertmanager: severity critical -> on-call
  - Incident log v `operations/incidents/YYYY-MM-DD.md`

## Verification
- Lokalno: `docker compose -f docker-compose.kpi.yml up -d`
- Prometheus: doda tarčo `omni-revenue-exporter:9101`
- Grafana: uvozi dashboarde, preveri prikaz KPI

## Next
- Dodaj ingestion pipeline za avtomatsko polnjenje `business_kpis.json`
- Razširi exporter z real-time viri (DB, Stripe, trgovina)