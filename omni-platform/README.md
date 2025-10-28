# Omni Platform — Docs & Demo

This repository hosts the Omni Platform backend and frontend, including agents for Access, Billing, Policy (Revenue), and RL Core.

## OpenAPI & Endpoints

Backend base: `VITE_API_BASE_URL` or `VITE_BACKEND_URL` (e.g. `http://localhost:8004`). FastAPI auto docs: `GET /docs`, schema: `GET /openapi.json`.

- Auth & Tenants
  - `POST /api/v1/access/create-tenant` — `{ tenant_id }` → creates tenant + API key.
  - `GET /api/v1/access/token` — headers: `tenant_id` → returns API key.
  - `POST /api/v1/access/rotate-key` — headers: `tenant_id` → rotates key.
  - `GET /api/v1/access/verify` — headers: `x-api-key`, `tenant_id` → verifies.
  - `GET /api/v1/access/agent/{tenant_id}` — get unified `UserAgent` profile.
  - `PUT /api/v1/access/agent` — update `UserAgent` fields: `real_name`, `billing_address`, `contact_email`, `compliance_status`.

- Billing
  - `GET /api/v1/billing/catalog` — list catalog items.
  - `POST /api/v1/billing/catalog/add` — add `{ name, price, currency, scope }`.
  - `PUT /api/v1/billing/catalog/{id}` — update.
  - `DELETE /api/v1/billing/catalog/{id}` — delete.

- Policy (Revenue)
  - `GET /api/v1/policy/revenue/history` — timeline of revenue/policy distribution.

- RL Core
  - `POST /api/v1/rl/market/process` — `{ trends: [{ name, sentiment }] }` → generates global catalog entries and records distribution.

- Admin UI
  - `GET /admin` — backend-rendered dashboard.

### cURL Examples

```bash
# Create tenant and get API key
curl -s -X POST "$BASE/api/v1/access/create-tenant" -H "Content-Type: application/json" -d '{"tenant_id":"finops-demo"}'
curl -s "$BASE/api/v1/access/token" -H "tenant_id: finops-demo"

# Verify
curl -s "$BASE/api/v1/access/verify" -H "tenant_id: finops-demo" -H "x-api-key: <API_KEY>"

# RL Core market process
curl -s -X POST "$BASE/api/v1/rl/market/process" \
  -H "tenant_id: finops-demo" -H "x-api-key: <API_KEY>" -H "Content-Type: application/json" \
  -d '{"trends":[{"name":"AI Agents-as-a-Service","sentiment":"bullish"}]}'

# Revenue history
curl -s "$BASE/api/v1/policy/revenue/history" -H "tenant_id: finops-demo" -H "x-api-key: <API_KEY>"

# Billing catalog add/list/update/delete
curl -s -X POST "$BASE/api/v1/billing/catalog/add" -H "tenant_id: finops-demo" -H "x-api-key: <API_KEY>" -H "Content-Type: application/json" -d '{"name":"AI Agent","price":99,"currency":"USD","scope":"global"}'
curl -s "$BASE/api/v1/billing/catalog" -H "tenant_id: finops-demo" -H "x-api-key: <API_KEY>"
curl -s -X PUT "$BASE/api/v1/billing/catalog/<ID>" -H "tenant_id: finops-demo" -H "x-api-key: <API_KEY>" -H "Content-Type: application/json" -d '{"price":100}'
curl -s -X DELETE "$BASE/api/v1/billing/catalog/<ID>" -H "tenant_id: finops-demo" -H "x-api-key: <API_KEY>"
```

## Demo — End-to-End

- Backend dev: `python -m uvicorn main:app --host 0.0.0.0 --port 8004 --reload` from `omni-platform/backend`.
- Frontend: set `VITE_API_BASE_URL=http://localhost:8004` and run Vite dev server or serve built assets.
- Flow: Create tenant → get key → RL Core market process → check Revenue history → add/update/delete catalog → use Admin Dashboard (React or `/admin`).

## Deploy — GitHub + Cloud Run + Vercel

### GitHub Actions (Cloud Run)
Add `.github/workflows/cloudrun.yml` (needs secrets `GCP_PROJECT`, `GCP_REGION`, `CLOUDRUN_SERVICE`, `GCP_SA_KEY_JSON`).

### Cloud Run locally
- Build image: `docker build -f Dockerfile.backend -t omni-backend .`
- Run: `docker run -p 8004:8004 omni-backend`

### Vercel Frontend
- `omni-platform/frontend` as project root.
- Set env `VITE_API_BASE_URL` to your backend URL.
- Deploy with Vercel; optional `vercel.json` included.

## Monetization Status
- Status: Active — preparing listings and investor outreach.
- Deploy targets: Cloud Run (backend), Vercel (frontend).
- Assets: Investor Brief PDF, demo script, marketplace guide.
- Architecture overview and agents.
- Market positioning.
- Monetization and valuation approach.

## Marketplace Listing Guidance
See `docs/marketplaces.md` for step-by-step on Acquire.com, Flippa, Product Hunt, Indie Hackers, and GitHub Sponsors.