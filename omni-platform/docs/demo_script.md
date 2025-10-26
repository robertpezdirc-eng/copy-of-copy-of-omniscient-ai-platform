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