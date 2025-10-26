# OMNI Platform – Production Runbook

This runbook outlines the operational steps to build, deploy, verify, and monitor the OMNI platform in production on Google Cloud Run.

## Prerequisites
- Google Cloud project: `refined-graph-471712-n9`
- Workload Identity Federation configured:
  - Workload identity provider: `projects/661612368188/locations/global/workloadIdentityPools/github/providers/github`
  - Service account: `ci-deployer@refined-graph-471712-n9.iam.gserviceaccount.com`
- GitHub secrets:
  - `GCP_PROJECT_ID`: `refined-graph-471712-n9`
  - `GCP_REGION`: `europe-west1`
- Service Account roles for CI deployer:
  - `Cloud Build Editor`
  - `Cloud Run Admin`
  - `Storage Admin`
  - `Service Account User`

## Build & Deploy
- Primary workflow: `.github/workflows/deploy-cloudrun-prod.yml`
- Trigger: push to `main` or manual dispatch
- Steps:
  - OIDC authentication to GCP
  - `gcloud builds submit --config cloudbuild.missing-services.yaml`
  - Verify Cloud Run services
  - Basic smoke checks against `/healthz` or `/health`

## Services covered
- `omni-api`
- `omni-singularity`
- `omni-quantum-backend`
- `omni-api-gateway`
- `quantum-worker`
- `quantum-entanglement-node`
- `omni-dashboard`

## Config & Secrets
- Use `--set-env-vars` and `--set-secrets` in Cloud Run deployments (defined in `cloudbuild.missing-services.yaml`).
- Ensure Secret Manager entries exist for keys:
  - `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `GEMINI_KEY`, `OMNI_API_KEY`, `SECRET_KEY`, `SLACK_WEBHOOK_URL`, `SMTP_USERNAME`, `SMTP_PASSWORD`.
- Database/cache endpoints:
  - Redis: `redis://omni-redis:6379`
  - MongoDB: `mongodb://omni-mongo:27017/omni`

## Observability
- Prometheus: service in `docker-compose.yml` and `prometheus.yml`
- Grafana: dashboards under `grafana/`
- Alertmanager: config under `alerts/` (Slack webhook)
- Cloud Logging & Error Reporting (enable in GCP console)

## Networking & Security
- Cloud Run ingress: public, or restrict via IAM
- Set `--min-instances` for warm start where needed
- `--cpu` and `--memory` per service (see cloudbuild file)
- Configure HTTPS with managed certificates (if behind Cloud Load Balancer)

## Rollback
- Use `gcloud run services update --image gcr.io/<project>/<image>:<previous_sha>`
- Or re-run GitHub Action with an older commit SHA

## Smoke Tests
- `/healthz` for `omni-dashboard`
- `/healthz` for `omni-api-gateway`
- `/health` for `omni-singularity`
- Add additional endpoints per service as needed

## Operational Tips
- Keep OIDC as the only auth mechanism for CI (avoid SA keys)
- Gradually migrate images to Artifact Registry (optional)
- Tag releases for traceability; consider adding a tag-triggered workflow
- Maintain uptime SLOs via Alertmanager and Cloud Monitoring