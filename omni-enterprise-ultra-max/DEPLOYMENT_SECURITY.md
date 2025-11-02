# Security Deployment Guide

This document explains how to build and deploy the backend with the new security features (encryption, GDPR endpoints, secure headers) to Cloud Run, and how to run locally via Docker Compose.

## Prerequisites
- Google Cloud project (Project ID)
- Google Cloud SDK installed and authenticated (`gcloud auth login`)
- Artifact Registry enabled
- Cloud Build API enabled
- (Optional) Docker Desktop for local runs

## 1) Configure encryption key (recommended)
Production should supply a stable 256-bit key via Google Secret Manager.

- Generate a 256-bit key and base64url encode it (no padding):
  - Python: `import os, base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip('='))`
- Create secret and add version:
  - `gcloud secrets create OMNI_ENCRYPTION_KEY --replication-policy=automatic`
  - `echo <YOUR_KEY> | gcloud secrets versions add OMNI_ENCRYPTION_KEY --data-file=-`
- Note the resource name: `projects/<PROJECT_ID>/secrets/OMNI_ENCRYPTION_KEY/versions/latest`

The backend will read this via `GCP_SECRET_ENCRYPTION_KEY` env var.

## 2) Build and deploy backend via Cloud Build + Cloud Run
Use the included PowerShell script to wrap the steps.

```powershell
# From repo root
# Minimal example (encryption secret optional but recommended)
./deploy-backend.ps1 -PROJECT_ID <PROJECT_ID> -REGION europe-west1 -SERVICE omni-ultra-backend -TAG (Get-Date -Format "yyyyMMdd-HHmmss") -ENCRYPTION_SECRET_RESOURCE "projects/<PROJECT_ID>/secrets/OMNI_ENCRYPTION_KEY/versions/latest"
```

Under the hood, this script:
- Runs `gcloud builds submit --config cloudbuild-backend.yaml` and fills `_PROJECT_ID`/`_TAG`
- Deploys to Cloud Run with environment variables:
  - `RUN_AS_INTERNAL=0`
  - `PERF_SLOW_THRESHOLD_SEC=1.0`
  - `GCP_PROJECT_ID=<PROJECT_ID>`
  - `GCP_SECRET_ENCRYPTION_KEY=<secret resource>` (if provided)

## 3) Verify deployment
- Open the Cloud Run URL displayed after deployment.
- Health: `GET /api/health`
- Security endpoints:
  - `GET /api/v1/security/status`
  - `POST /api/v1/security/crypto/encrypt` with body `{ "plaintext": "hello", "aad": "ctx" }`
  - `POST /api/v1/security/crypto/decrypt` with body `{ "token": "...", "aad": "ctx" }`
  - `POST /api/v1/security/consent` with `{ "user_id": "u1", "consent": { "marketing": true } }`
  - `POST /api/v1/security/gdpr/export` with `{ "user_id": "u1" }`
  - `POST /api/v1/security/gdpr/erase` with `{ "user_id": "u1" }`

## 4) Local run (optional)
`docker-compose.yml` runs backend (port 8080) and gateway (port 8081). Ensure Docker Desktop is running.

```powershell
# Build and start services in the background
docker compose up --build -d

# Check health
curl http://localhost:8080/api/health
```

If you want a stable encryption key locally, set `OMNI_ENCRYPTION_KEY` in your environment with the base64url-encoded key.

## 5) Observability and security notes
- Security headers are applied globally; add a Content-Security-Policy when frontends are well-scoped.
- PII log redaction scrubs common patterns (emails, bearer tokens) — extend as needed.
- GDPR service is best-effort; integrate real data sources over time.
- For Secret Manager access on Cloud Run, ensure the service account has `Secret Manager Secret Accessor` role.
