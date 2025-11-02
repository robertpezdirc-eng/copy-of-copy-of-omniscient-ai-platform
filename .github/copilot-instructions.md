# Omni Enterprise Ultra Max — AI Agent Guide

**Architecture**
- Two core services: `backend/` (heavy FastAPI ML stack) and `gateway/` (lightweight FastAPI proxy); gateway fronts all external traffic and forwards under `/api/*`.
- Backend toggles "internal mode" via `RUN_AS_INTERNAL=1`, which strips `/internal` prefixes and skips `RateLimiter`/`UsageTracker`; default mode keeps public throttling.
- Observability: both services expose `/metrics` (Prometheus) and `/api/health`; gateway optionally sends traces via OpenTelemetry/Sentry.

**Backend Service**
- Entry point `backend/main.py` lazily attempts to import >20 routers; add new feature modules under `backend/routes/` and register through `_register_routers` (wrap in try/except to avoid startup failures when dependencies are optional).
- Database layer `backend/database.py` initializes PostgreSQL, MongoDB, Redis, Firestore on startup; handle missing services gracefully and log instead of raising to keep Cloud Run boot fast.
- Background utilities (`utils/background_tasks.py`) and adapters (e.g., `adapters/omni_brain_adapter.py`) are optional—guard imports and provide fallbacks like existing routes do.
- Heavy ML deps live in `backend/requirements.txt`; expect long cold starts, so prefer async tasks and caching (see `services/ai/*`).

**Gateway Service**
- `gateway/app/main.py` builds the app with pooled `httpx` clients, Redis-backed rate limiting (`RedisRateLimiter`), response caching, and tracing hooks.
- API key auth lives in `gateway/app/auth.py`; keys are comma-separated in `API_KEYS`, and the prefix (`prod-key-*`) maps to rate tiers via `request.state`.
- Proxy logic in `gateway/app/proxy.py` rehydrates requests and records custom Prometheus metrics in `business_metrics`—reuse those helpers for new upstream calls.
- Secrets can be fetched from Google Secret Manager (`secret_manager.load_secrets_from_manager`); prefer storing sensitive values there instead of `.env` files.

**Local Development**
- `docker-compose.yml` runs backend (port 8080) + gateway (port 8081) with the correct env defaults; use this for parity with Cloud Run/GKE split.
- For ad-hoc runs, set `RUN_AS_INTERNAL=1` when launching backend so gateway proxies work without rate limiting.

**Build & Deployment**
- Backend image: `cloudbuild-backend.yaml` builds `Dockerfile.backend` and pushes to Artifact Registry `europe-west1-docker.pkg.dev/${_PROJECT_ID}/omni/omni-ultra-backend:${_TAG}`; set substitutions `_PROJECT_ID` and `_TAG` (often `$SHORT_SHA`).
- Gateway CI/CD: `gateway/cloudbuild.yaml` builds, pushes, and deploys to Cloud Run in one pipeline; required substitutions include `_PROJECT_ID`, `_REGION`, `_SERVICE`, `_IMAGE`, `_UPSTREAM_URL`, `_API_KEYS`.
- One-off gateway deploy script `deploy-gateway.ps1` wraps `gcloud run deploy`; update `UPSTREAM_URL` to either the Cloud Run backend URL or the GKE internal service (`http://ml-worker.default.svc.cluster.local:8080`).
- Backend GKE manifests live in `backend/k8s/deployment.yaml`; readiness probe waits 300s to accommodate ML warm-up—keep that in mind when changing startup tasks.

**Testing & Validation**
- Unit tests reside under `backend/tests/`; they inject dependencies via `app.dependency_overrides` and patch SDK clients—follow that pattern for new route tests.
- Gateway smoke test `tests/openai_gateway_smoke.py` hits the `/v1/chat/completions` OpenAI-compatible endpoint and writes timestamped reports; run it after gateway deploys (`python tests/openai_gateway_smoke.py`).
- CI workflows in `.github/workflows/` trigger Cloud Build deploys (`deploy-minimal-backend.yml`, `deploy-gateway.yml`) and use project `refined-graph-471712-n9`, region `europe-west1` by default.

**Conventions & Tips**
- Prefer async FastAPI handlers; when calling external services, use shared `httpx.AsyncClient` instances from gateway `main.py` instead of creating new clients.
- When adding middleware, remember FastAPI insertion order: first added wraps later ones; follow current sequence (metrics → performance monitor → usage → rate limiting).
- Log with `logging` module; structured logging is already configured in gateway via `setup_json_logging()`.
- Keep responses deterministic and documented—backend auto-docs live at `/api/docs`; ensure new routes include FastAPI tags and Pydantic models for schema clarity.
