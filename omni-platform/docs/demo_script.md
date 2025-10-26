# Demo Script — Omni Platform (End-to-End)

## Setup
- Start backend: `python -m uvicorn main:app --host 0.0.0.0 --port 8004 --reload` (from `omni-platform/backend`).
- Frontend: set `VITE_API_BASE_URL=http://localhost:8004` and run Vite dev or serve.

## Flow (5–7 min)
1) Create Tenant
- POST /api/v1/access/create-tenant with `{"tenant_id":"finops-demo"}`.
- GET /api/v1/access/token with header `tenant_id: finops-demo` → copy API key.

2) RL Core Market Process
- POST /api/v1/rl/market/process with trends; headers: `tenant_id`, `x-api-key`.
- Explain: auto-creates global catalog items and records distribution.

3) Revenue History
- GET /api/v1/policy/revenue/history — show entries.

4) Billing Catalog
- POST /api/v1/billing/catalog/add` — add item.
- GET /api/v1/billing/catalog — list.
- PUT /api/v1/billing/catalog/{id}` — update price.
- DELETE /api/v1/billing/catalog/{id}` — remove item.

5) Admin Dashboard (React)
- Enter API Key and Tenant ID, click "Osveži".
- Click "Generate from Market Data" and "Add Catalog Item".
- Show Revenue History timeline and Catalog table with actions.

## Recording Tips
- Use OBS (1080p, 30fps), capture browser and terminal.
- Include short intro: problem → solution → E2E demo → deploy URLs.
- Keep commands readable; paste curl snippets from README.

## Preflight Checklist
- Backend running on `http://localhost:8004` and healthy at `/api/health`.
- Frontend dev server available and `VITE_API_BASE_URL` set to backend.
- Test tenant `finops-demo` and API key obtained.
- Clean browser cache or use incognito for fresh UI state.

## cURL Snippets (Copy/Paste)
- Create tenant:
  - `curl -s -X POST "http://localhost:8004/api/v1/access/create-tenant" -H "Content-Type: application/json" -d '{"tenant_id":"finops-demo"}'`
- Issue API key:
  - `curl -s "http://localhost:8004/api/v1/access/token" -H "tenant_id: finops-demo"`
- Market process:
  - `curl -s -X POST "http://localhost:8004/api/v1/rl/market/process" -H "Content-Type: application/json" -H "x-api-key: <API_KEY>" -H "tenant_id: finops-demo" -d '{"trends":[{"name":"AI Agents-as-a-Service","sentiment":"bullish"},{"name":"RL-driven FinOps","sentiment":"neutral"}]}'`
- Revenue history:
  - `curl -s "http://localhost:8004/api/v1/policy/revenue/history" -H "x-api-key: <API_KEY>" -H "tenant_id: finops-demo"`
- Add catalog item:
  - `curl -s -X POST "http://localhost:8004/api/v1/billing/catalog/add" -H "Content-Type: application/json" -H "x-api-key: <API_KEY>" -H "tenant_id: finops-demo" -d '{"name":"Pro Tier","price":99,"currency":"USD","scope":"global"}'`

## Timings (Guide)
- Intro + setup: 60–90s
- Tenant + API key: 60s
- Market process + results: 90s
- History + catalog tour: 60–90s
- Admin Dashboard actions: 60s
- Wrap-up CTA: 30–45s

## Monetization Highlights
- Subscription tiers and usage-based add-ons demonstrated in catalog.
- Revenue history shows distribution records linked to RL Core actions.
- Admin Dashboard accelerates tenant onboarding and catalog changes.

## Deploy Notes (Cloud Run / Vercel)
- Backend: build via `Dockerfile.backend` and deploy to Cloud Run.
- Frontend: deploy to Vercel; set `VITE_API_BASE_URL` to Cloud Run URL.
- Verify `/api/health` and UI connectivity post-deploy.

## Wrap-up CTA
- Invite investors to access demo instance and review PDF brief.
- Share marketplace listing and sponsor links.