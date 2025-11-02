# ML Worker (Backend) on GKE

This backend hosts the heavy AI stack. In split-architecture, it runs as an internal service on GKE, while the AI Gateway (Cloud Run) fronts it.

## 1) Build and push image

- Use the existing Dockerfile `Dockerfile.backend`.
- Tag and push to Artifact Registry or Container Registry.

Example (Artifact Registry):

```powershell
# Auth
gcloud auth configure-docker europe-west1-docker.pkg.dev

# Build
docker build -t europe-west1-docker.pkg.dev/PROJECT/REPO/omni-ultra-backend:$(git rev-parse --short HEAD) -f Dockerfile.backend .

# Push
docker push europe-west1-docker.pkg.dev/PROJECT/REPO/omni-ultra-backend:$(git rev-parse --short HEAD)
```

## 2) Deploy to GKE Autopilot

- Create a cluster (once):

```powershell
gcloud container clusters create-auto omni-ml-autopilot --region=europe-west1 --project=PROJECT
```

- Update `backend/k8s/deployment.yaml` image:

```
image: europe-west1-docker.pkg.dev/PROJECT/REPO/omni-ultra-backend:<TAG>
```

- Apply manifests:

```powershell
kubectl apply -f backend/k8s/deployment.yaml
kubectl rollout status deploy/ml-worker
kubectl get svc ml-worker
```

## 3) Point gateway to the worker

Use the ClusterIP DNS name in the same namespace:

```
UPSTREAM_URL=http://ml-worker.default.svc.cluster.local:8080
```

Update your Cloud Run gateway environment to point to this URL.

## 4) Health and metrics

- Health: `GET /api/health`
- Metrics: `GET /metrics` (if `prometheus-client` installed; it is in backend/requirements.txt)
- Gateway can call `GET /api/health` to verify readiness.

## 5) Notes

- Internal mode is enabled via `RUN_AS_INTERNAL=1`, which:
  - Disables public RateLimiter and UsageTracker middleware
  - Supports calling the same routes via `/internal/...` by stripping the prefix (e.g., `/internal/api/ai/...`)
- Resource requests/limits are set high by default; tune based on perf.
