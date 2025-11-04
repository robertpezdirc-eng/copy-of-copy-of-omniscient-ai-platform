# Cloud Testing Setup (Vercel + Render)

Ta vodič ti omogoča, da v nekaj minutah povežeš GitHub repo in testiraš frontend (Vercel) ter gateway (Render), brez lokalnega nastavljanja.

## Pregled
- Frontend (React/Vite) → Vercel (Preview deploy za PR-je, Production za `master`).
- Gateway (Python/FastAPI) → Render (Docker build, stalni web servis).
- Monorepo podpora: Render uporablja `render.yaml` blueprint; Vercel deploya iz `frontend/`.

## 1) Render (gateway) – enostaven deploy preko blueprinta
1. Odpri https://render.com → New + → Blueprint → prilepi URL do repozitorija.
2. Render bo sam zaznal `render.yaml` v rootu in predlagal dva servisa:
   - `gateway` (Web Service, Docker iz `gateway/Dockerfile`)
   - `frontend` (Static Site iz `frontend/`)
3. Nastavi environment spremenljivke za `gateway`:
   - `OPENAI_API_KEY` = tvoj ključ (obvezno)
   - `UPSTREAM_URL` = `https://api.openai.com/v1` (privzeto)
   - `SENTRY_DSN` (po želji)
   - `REDIS_URL` (po želji)
4. Deploy. Render bo zgradil Docker image za gateway in postavil URL (npr. `https://gateway-xxxxx.onrender.com`).
5. Frontend bo zgrajen z `npm ci && npm run build` in objavljen iz `dist`.
   - `VITE_API_URL` se bo (če Render podpira `fromService`) avtomatsko nastavil na gateway URL.
   - Če ne, ga ročno nastavi v Render Static Site → Environment → `VITE_API_URL = https://gateway-xxxxx.onrender.com`.

## 2) Vercel (frontend) – PR preview in produkcija
1. Odpri https://vercel.com → New Project → Import Git Repository → izberi repo.
2. V nastavitvah projekta nastavi `Root Directory` na `frontend/`.
3. Build/publish nastavitve:
   - Build Command: `npm ci && npm run build`
   - Output Directory: `dist`
4. Environment spremenljivke:
   - `VITE_API_URL` = URL do gateway-ja (Render URL iz prejšnjega koraka)
5. Shrani in deploy.
   - Ob vsakem PR boš dobil Vercel Preview URL.
   - Ob pushu v `master` (ali `main`) bo izveden Production deploy.

### Enoklikovni deploy gumbi
- Vercel (frontend iz podmape `omni-enterprise-ultra-max/frontend`):
  - Klikni: https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Frobertpezdirc-eng%2Fcopy-of-copy-of-omniscient-ai-platform&root-directory=omni-enterprise-ultra-max%2Ffrontend&project-name=omni-frontend&repository-name=omni-frontend
  - Nato v Vercel UI dodaj `VITE_API_URL` (Render gateway URL).
- Render (gateway + frontend preko blueprinta):
  - Klikni: https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2Frobertpezdirc-eng%2Fcopy-of-copy-of-omniscient-ai-platform
  - Če Render ne najde `render.yaml` v rootu repozitorija, lahko servise ustvariš ročno:
    - Web Service (Docker) → Root Directory: `omni-enterprise-ultra-max/gateway` → Deploy from Dockerfile.
    - Static Site → Root Directory: `omni-enterprise-ultra-max/frontend` → Build `npm ci && npm run build`, Publish `dist`.

## 3) GitHub Actions za Vercel (opcijsko)
V repo je dodan `.github/workflows/deploy-frontend-vercel.yml`, ki omogoča avtomatske deploye.

Nastavi GitHub Secrets (Repo → Settings → Secrets and variables → Actions):
- `VERCEL_TOKEN` – Vercel token (Account → Tokens)
- `VERCEL_ORG_ID` – ID organizacije ali osebni račun
- `VERCEL_PROJECT_ID` – ID projekta za ta `frontend`

Workflow se sproži na PR in push v `master`. Production deploy se zgodi ob pushu v `master`.

## Testiranje
1. Ustvari PR → počakaj Vercel preview → odpri URL in testiraj UI.
2. API klici naj kažejo na `VITE_API_URL` (gateway na Render). Preveri, da se endpointi odzivajo (npr. `/metrics`).
3. Po merge v `master` preveri Production URL (Vercel) in Production gateway (Render).

### Lighthouse CI (avtomatski audit)
- Zaženite workflow `Lighthouse CI` (GitHub Actions → Run workflow) in vnesite `frontend_url` (Vercel/Render URL).
- Workflow izvede `lhci autorun` in objavi rezultate (performance, accessibility, SEO) v začasno javno hrambo.
- Priporočilo: ciljajte Performance ≥ 90, Accessibility ≥ 90, SEO ≥ 90. Morebitna opozorila so označena kot `warn`.

### SPA routing (Vercel)
- Datoteka `frontend/vercel.json` dodaja rewrites za SPA, da vse poti kažejo na `index.html`.
- To zagotovi pravilno delovanje client-side routinga v produkciji.

## Opombe
- Blueprint `render.yaml` omogoča hiter start. Če Render ne podpira avtomatske povezave `VITE_API_URL`, nastavi ročno po prvem deployu.
- Za Railway lahko uporabiš `gateway/Dockerfile` brez dodatnih datotek; priporočam UI deploy in nastavitev `OPENAI_API_KEY`, `UPSTREAM_URL` ter start `uvicorn` v primeru brez Dockerja.