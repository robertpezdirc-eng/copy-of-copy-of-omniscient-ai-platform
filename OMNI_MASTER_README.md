# Omni Platform – Master README (Konsolidiran pregled)

Ta dokument združuje vse ključne dodatke, module, generatoje, orodja, agente, infrastrukturo ter zadnje spremembe po vseh lokacijah (lokalno, Docker, GitHub, Vertex AI, Google Cloud Run) v zadnjih 48 urah, kjer je bilo mogoče zanesljivo ugotoviti.

## 1. Namen in obseg
- Celovit pregled Omni platforme: arhitektura, moduli, generatorji, orodja, agenti.
- Pregled infrastrukture: Docker Compose skladi, Cloud Run storitve, Vertex AI nastavitve, GKE konfiguracije.
- Indeks pomembnih README/MD dokumentov po kategorijah.
- Zadnje zaznane spremembe v zadnjih 48 urah (lokalni repo, brez `.venv`).

## 2. Arhitektura – glavne komponente
- `Omni Dashboard` – admin/operativni UI (`omni-dashboard`), health endpoint `GET /api/health`.
- `Omni API Gateway` – prehod do modulov in storitev (Cloud Run, Nginx proxy).
- `Omni License Server` – strežnik licenc (MongoDB odvisnost), Admin GUI, Client Panel.
- `Monitoring Stack` – Prometheus (9090), Grafana (3000), Alertmanager (9093), Loki, Tempo, Promtail, Node Exporter (9100), Mailhog (8025/1025).
- `Reverse Proxy` – `nginx` (80/443) pred `omni-dashboard` ali `server`.
- `Podatkovne storitve` – MongoDB (27017), Redis (6379), SQLite (lokalna datoteka) v nekaterih skladih.
- `Quantum/Advanced` – `omni-singularity` + `omni-quantum-backend` (posebne zahteve CPU/GPU/RAM v docker-compose.omni.yml).

## 3. Moduli, generatorji in agenti
- Generatorji:
  - `ModuleGenerator` v `dynamic-modular-systems.js` (ustvarja module z osnovnimi endpointi `/status`, `/health`, `/metrics`; podpira tip `traffic-optimizer`).
  - `document_generator`, `test_generator` registrirana v centralnih orodjih (platform coordinator) – generiranje dokumentacije/testnih predlogov.
- Orodja:
  - `omni_development_tools.py` – predlogi za odpravo napak na podlagi stack trace.
  - `omni_integration_verifier.py` – preverjanje prisotnosti jedrnih komponent (npr. `omni_sync_core`, `omni_device_manager`).
  - `omni_deployment_tools.py` – orkestracija kontejnerjev (omrežja, volumni, storitve).
  - API `moduleAPI.js` – `POST /api/modules` za ustvarjanje novega modula z meta in health metrikami.
- Agenti:
  - `CommercialAgent` (več implementacij: strežniško in večagentni sistemi) – tržna analiza, kampanje, napoved prihodkov.
  - `CommercialIntelligenceEngine` – monetizacijske strategije, tržna analiza.
  - `System Health` moduli – `get_system_health` / `health_check` v več sistemih (admin, cloud, production dashboard, core). 
  - `Healthcare` – zdravstveni modul (AI diagnostika, telemedicina, wellness) z integracijo v UI (Zdravstveni Modul).
- Upravljanje modulov:
  - `omni_ultra_core.py` – nalaganje obstoječih modulov + ustvarjanje novih.
  - `omni_universal_integrator.py` – fallback moduli (A/B/C verzije) za manjkajoče industrije.
  - `module-manager.js` (client) – pregled modulov, licenc in stanja.

## 4. Docker Compose skladi
- `omni-platform/docker-compose.yml` in ekvivalentne kopije:
  - Storitve: `omni-dashboard`, `nginx-proxy`, `prometheus`, `grafana`, `alertmanager`, `mock-slack`, `mailhog`, `node-exporter`.
  - Omrežje: `omni-network` (bridge); Volumen: `grafana_data`.
  - Kredenciali: `gcp-credentials.json` mounted v dashboard.
- `external/github/OMNIBOT12_from_github/omni-docker/docker-compose.yml`:
  - `mongo` (healthcheck `mongosh ping`), `server` (licence, health `license/stats`), `admin` (health `curl /`).
  - `docker-compose.dev.yml` (override) za razvoj: `omni-server`, `omni-admin`, `omni-client`, `mongodb`.
- `external/github/OMNIBOT12_from_github/omni-global/docker-compose.yml` in `docker-compose.simple.yml`:
  - `server` (3000/3443), `admin` (4000/4443), `nginx` (80/443), `mongo`, `redis`.
  - SSL cert volumni in healthchecki na `server`/`admin`.
- `docker-compose.omni.yml` (Singularity Quantum Dashboard v10.0):
  - `omni-singularity`, `omni-storage` (SQLite), `omni-redis`, `omni-quantum-backend`, `omni-dashboard`, `omni-api-gateway`, `omni-load-balancer` (nginx), `prometheus`.
- `docker-compose.yml` v korenu (observability stack):
  - Grafana, Prometheus, Alertmanager, Loki, Tempo, Promtail, Pyroscope, Node Exporter, cAdvisor, Telemetrygen, Loggen.

## 5. Cloud Run / Vertex AI / GKE
- Cloud Run:
  - Konfiguracija (`cloudrun-url.json`) za `omni-dashboard`: image `gcr.io/.../omni-dashboard:latest`, env (`OMNI_ENV`, `GF_*` za Grafano), resursi (CPU/MEM), URL do storitve, health endpointi.
  - GitHub Actions workflow `.github/workflows/deploy-cloudrun-prod.yml`:
    - OIDC auth, `gcloud` setup, Docker auth za GCR/AR, `gcloud builds submit` za manjkajoče storitve.
    - Verifikacija storitev, smoke testi na `omni-dashboard` in `omni-api-gateway`, rollback za `omni-api-gateway` ob neuspehu.
- Vertex AI:
  - `vertex_ai_config.json`: project, region, model `gemini-2.5-pro`, nastavitve Omni (AI provider, learning mode, knowledge base path).
  - `vertex_oauth_vertex.json`: trenutna 404 za določeno Gemini endpoint – potrebno preveriti dovoljenja/model id.
- GKE (Kubernetes):
  - `google-cloud-deploy.yaml` (prod): `Deployment` (3 replike), limiti/requests, liveness/readiness probe, volume mounts, sidecar za monitoring.
  - `Services` (LoadBalancer, ClusterIP), `Secrets`, `ConfigMap`, `Ingress` + managed certifikati, `PDB`, `HPA`.

## 6. Indeks dokumentacije (README/MD)
Spodaj je kuriran indeks ključnih README/MD dokumentov po kategorijah in značilnih lokacijah v repozitoriju:
- Omni Platform in Observability:
  - `omni-platform/docker-compose.yml` + spremljajoča `README.md` (lokalni deployment, monitoring, health endpoints).
  - Root observability `docker-compose.yml` (Grafana/Prometheus) z razlago metrik in alertov.
- Omni Global in License System:
  - `external/github/OMNIBOT12_from_github/omni-global/docker-compose.yml` + `README.md` (server, admin, nginx, mongo, redis, SSL).
  - `external/github/OMNIBOT12_from_github/omni-docker/DOCKER-INSTALLATION.md` (instalacija, zagon, health, logi).
- Razvojni sklad (dev overrides):
  - `external/.../omni-docker/docker-compose.dev.yml` + `project_artifacts/...docker-compose.dev.yml` (debug porti, hot-reload).
- Napredne komponente:
  - `docker-compose.omni.yml` (Singularity/Quantum), spremljajoča dokumentacija v modulu.
- Cloud in CI/CD:
  - `.github/workflows/deploy-cloudrun-prod.yml` (CI/CD v Cloud Run), `google-cloud-deploy.yaml` (GKE prod), `vertex_ai_config.json` (Vertex AI).

Opomba: V repozitoriju obstaja še mnogo dodatnih `README.md` (100+), razporejenih po podmapah (npr. `omni-core`, `omni-cloud`, `ultimate package`, `vr projects`). Ta indeks zajema glavne vstopne točke in infrastrukturo, ki veže celoten sistem.

## 7. Zadnje spremembe (zadnjih 48 ur)
Na lokalni poti `C:\Users\admin\Downloads\copy-of-copy-of-omniscient-ai-platform` (brez `.venv`) so bile zadnje spremembe zaznane predvsem v Docker/operativnih datotekah:
- `external/github/OMNIBOT12_from_github/docker-compose.yml` (posodobitev).
- `external/github/OMNIBOT12_from_github/docker-compose.production.yml` (posodobitev).
- `external/github/OMNIBOT12_from_github/DOCKER-INSTALLATION.md` (posodobitev).
- `external/github/OMNIBOT12_from_github/docker-env-validator.js` (posodobitev).
- `external/github/OMNIBOT12_from_github/docker-health-check.js` (posodobitev).
- `external/github/OMNIBOT12_from_github/docker-logs-monitor.js` (posodobitev).
- `external/github/OMNIBOT12_from_github/docker-ssl-setup.js` (posodobitev).
- `external/github/OMNIBOT12_from_github/docker-start.bat` (posodobitev).

Te spremembe kažejo krepitev stabilnosti, health checkov, SSL, logiranja in produkcijskega compose setupa.

## 8. Zagon lokalno (Docker)
- Priprava `.env` in `gcp-credentials.json` kjer je potrebno.
- `docker compose up -d` v ustrezni mapi (npr. `omni-platform`, `omni-global`, root observability). 
- Health preverjanje:
  - `omni-dashboard`: `curl http://localhost:8080/api/health`
  - `server`: `curl http://localhost:3000/api/health` ali `license/stats`
  - `admin`: `curl http://localhost:4000/health`
- Grafana: `http://localhost:3000` (admin pwd: `omni_admin_2024` v lokalnem setupu).

## 9. Deploy (Cloud Run / GKE)
- Cloud Run prod preko GitHub Actions:
  - Push v main, workflow izvede build/push, verifikacijo storitev, smoke teste in eventualni rollback.
- GKE prod:
  - Uporabi `google-cloud-deploy.yaml` z `kubectl apply -f` in posodobi secrets/configmaps pred deployem.
- Vertex AI:
  - Preveri model/endpoint dovoljenja (404 v `vertex_oauth_vertex.json`), posodobi `vertex_ai_config.json` projekt/region/model id.

## 10. Integracija modulov in zdravje sistema
- Dodajanje modulov preko API (`POST /api/modules`) s polji: `name`, `description`, `port`, `endpoint`, `capabilities`, `dependencies`.
- Health checki centralizirano (dashboard, admin, api gateway) + Prometheus scrape in alerting.
- Fallback moduli (A/B/C) za manjkajoče industrije z `omni_universal_integrator.py`.

## 11. Indeks povezav in stalnih lokacij
- Lokalno:
  - Root: `C:\Users\admin\Downloads\copy-of-copy-of-omniscient-ai-platform\`
  - Konfiguracije: `cloudrun-url.json`, `vertex_ai_config.json`, `google-cloud-deploy.yaml`, `.github/workflows/deploy-cloudrun-prod.yml`.
  - Docker sklad: `omni-platform/`, `external/github/OMNIBOT12_from_github/omni-global/`, `external/github/OMNIBOT12_from_github/omni-docker/`, root `docker-compose.yml` (observability).
- Docker:
  - Images: `omni-dashboard`, `omni-api-gateway`, `omni-server`, `omni-admin`, `mongo`, `redis`, `nginx`, monitoring images (prom/*, grafana/*).
- GitHub:
  - Workflow za Cloud Run: `.github/workflows/deploy-cloudrun-prod.yml`.
  - Kode: `external/github/OMNIBOT12_from_github/...` (več podsistemov, README/MD dokumentov).
- Vertex AI:
  - Konfiguracija: `vertex_ai_config.json`, OAuth/token validacija: `vertex_oauth_vertex.json`.
- Google Cloud Run:
  - Storitev: `omni-dashboard` (URL v `cloudrun-url.json`).

## 12. Kaj je novega (povzetek)
- Okrepljen Docker produkcijski setup (compose, health, SSL, logi) v zadnjih 48h.
- Konsolidacija dokumentacije in indeks glavnih README.
- Poudarek na CI/CD (Cloud Run workflow) in Kubernetes prod konfiguraciji.
- Pregled generatorjev (`ModuleGenerator`) in centralnih orodij (dokumentacija/test generator).

---
Če želite, lahko dodamo avtomatsko skripto za generiranje indeksa vseh `README.md` in detekcijo sprememb (PowerShell/Node), ter ga povežemo v CI, da se `OMNI_MASTER_README.md` posodablja ob vsakem pushu.