# OMNI – Secrets & Environment Variables (Production)

Centralized reference of required secrets and environment variables for Cloud Run services.

## Global Secrets (Google Secret Manager)
Store these as secrets in Secret Manager and reference them in Cloud Run deployments.

- `OPENAI_API_KEY`
- `GOOGLE_API_KEY`
- `GEMINI_KEY`
- `OMNI_API_KEY`
- `SECRET_KEY` (JWT/crypto)
- `SLACK_WEBHOOK_URL`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- Optional: `IBM_WATSON_KEY`

## Service Environment Variables

- Common
  - `NODE_ENV=production`
  - `LOG_LEVEL=info`
  - `REGION=europe-west1`

- API Gateway (`omni-api-gateway`)
  - `PORT=8080`
  - `CORS_ORIGIN=https://your-domain`
  - `OMNI_API_URL=https://omni-api-<hash>-ew.run.app`
  - `SINGULARITY_URL=https://omni-singularity-<hash>-ew.run.app`
  - Secrets: `OMNI_API_KEY`, `SECRET_KEY`

- OMNI API (`omni-api`)
  - `PORT=8080`
  - `MONGO_URL=mongodb://omni-mongo:27017/omni`
  - `REDIS_URL=redis://omni-redis:6379`
  - Secrets: `SECRET_KEY`

- Singularity (`omni-singularity`)
  - `PORT=8080`
  - `MODEL_PROVIDER=openai|gemini|ibm`
  - Secrets: `OPENAI_API_KEY`, `GEMINI_KEY`, `IBM_WATSON_KEY`

- Quantum Backend (`omni-quantum-backend`)
  - `PORT=8080`
  - `WORKER_URL=https://quantum-worker-<hash>-ew.run.app`

- Quantum Worker (`quantum-worker`)
  - `PORT=8080`

- Quantum Entanglement Node (`quantum-entanglement-node`)
  - `PORT=8080`

- Dashboard (`omni-dashboard`)
  - `PORT=8080`
  - `API_GATEWAY_URL=https://omni-api-gateway-<hash>-ew.run.app`

## Notes
- Replace `<hash>` with actual Cloud Run service suffix if used.
- Prefer `--set-secrets` flags in `gcloud run deploy` for sensitive values.
- Keep non-sensitive ENV in Cloud Run `--set-env-vars`.
- Maintain parity between local `docker-compose.yml` and Cloud Run settings.