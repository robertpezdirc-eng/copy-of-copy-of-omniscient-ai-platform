# AI Gateway

A lightweight FastAPI gateway that fronts the heavy ML worker. It handles auth, metrics, logging, and proxies requests to the upstream ML worker.

## Public Endpoints (No Authentication Required)

- `/` - Service information and available endpoints
- `/health` - Health check with upstream status
- `/readyz` - Kubernetes readiness probe
- `/livez` - Kubernetes liveness probe
- `/metrics` - Prometheus metrics (if enabled)
- `/docs` - OpenAPI documentation

## Protected Endpoints (Require API Key)

- `/api/*` - All API routes (proxied to upstream ML worker)

## Environment Variables

- UPSTREAM_URL: Base URL of the ML worker (e.g., http://ml-worker.default.svc.cluster.local:8080)
- API_KEYS: Comma-separated list of API keys; if unset/empty, the gateway accepts requests without a key (dev only)
- SENTRY_DSN: Optional Sentry DSN
- SERVICE_NAME: Name of the service (defaults to ai-gateway)
- ENVIRONMENT: Environment label (dev/stage/prod)

Notes:
- Gateway route `/api/{path}` forwards to upstream `/api/{path}` (matches backend route structure)
- Backend can run with `RUN_AS_INTERNAL=1` so the same routes are also available under `/internal/...` if needed

## Run locally

1. Create a Python venv and install requirements
2. Set env vars:
   - UPSTREAM_URL=http://localhost:9000
   - API_KEYS=dev-key-123 (optional)
3. Start server:

```
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

Visit:
- http://localhost:8080/ - Service info
- http://localhost:8080/health - Health check
- http://localhost:8080/readyz - Readiness probe
- http://localhost:8080/livez - Liveness probe
- http://localhost:8080/metrics - Prometheus metrics
- http://localhost:8080/docs - API documentation
- Proxy: http://localhost:8080/api/<path> (forwards to `${UPSTREAM_URL}/<path>`, requires API key)

## Docker build

```
docker build -t ai-gateway -f gateway/Dockerfile .
```

## Deploy to Cloud Run via Cloud Build

1. Create a Cloud Build trigger or run:

```powershell
cd gateway
gcloud builds submit --config=cloudbuild.yaml --project=refined-graph-471712-n9 `
  --substitutions=_PROJECT_ID=refined-graph-471712-n9,_REGION=europe-west1,_SERVICE=ai-gateway,_IMAGE=gateway,_UPSTREAM_URL=http://ml-worker.default.svc.cluster.local:8080,_API_KEYS=dev-key-123 `
  --timeout=20m
```

2. Confirm deployment:

```powershell
gcloud run services describe ai-gateway --region=europe-west1 --project=refined-graph-471712-n9 --format="value(status.url)"
```

3. Test:

```powershell
$GATEWAY_URL = (gcloud run services describe ai-gateway --region=europe-west1 --format="value(status.url)")
Invoke-WebRequest -Uri "$GATEWAY_URL/health" -UseBasicParsing | Select-Object -ExpandProperty Content
```

## End-to-end setup for split architecture

1. Build and push backend image.
2. Deploy backend to GKE (see `backend/DEPLOYMENT_GKE.md` for steps).
3. Deploy gateway to Cloud Run with `UPSTREAM_URL` pointing to GKE internal service.
4. Done. Gateway at your Cloud Run URL; backend at ClusterIP on GKE.

Refer to `docker-compose.yml` for quick local dev/test scenario.
