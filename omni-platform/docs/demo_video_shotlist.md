# Omni Platform – Demo Video Shotlist (OBS)

This shotlist guides you through a 6–8 minute demo recording in OBS Studio. It includes scene sequencing, timing, and URLs to open during recording.

## Preflight (2 minutes)
- Confirm backend running: `http://localhost:8004/api/health` returns JSON.
- Confirm frontend dev: `http://localhost:5175/` loads without errors.
- Confirm architecture image: `http://localhost:8009/omni-platform/docs/diagrams/architecture.png` opens.
- OBS → Settings → Output → Recording:
  - Format: `mp4` (or `mkv`), Encoder: GPU (NVENC/AMF) if available.
  - Recording Path: choose your target folder.
- OBS → Settings → Video: Base/Output 1920x1080, 30 fps.
- OBS Sources: add `Window Capture` for browser window and `Audio Input Capture` for mic.

## Scene Order and Timing

1) Intro – Architecture (30–45s)
- Show the architecture image full-screen.
- URL: `http://localhost:8009/omni-platform/docs/diagrams/architecture.png`.
- Narration: “This is the Omni Platform architecture: Vite frontend, FastAPI backend, Cloud Run/Vercel deploy, streaming chat and FinOps analytics under one roof.”

2) Frontend – Landing + Admin (1–2m)
- Switch to the frontend app.
- URL: `http://localhost:5175/`.
- Actions:
  - Navigate through landing/home.
  - Open Admin Dashboard.
  - Enter `tenant_id` and `x-api-key` as required.
- Narration: “The Admin Dashboard lets you generate catalogs from market data, manage items, and visualize revenue history.”

3) Backend – Health and API (1m)
- Show backend health.
- URL: `http://localhost:8004/api/health`.
- Optional cURL snippet (narrate):
  - `curl -s http://localhost:8004/api/health | jq`.
- Narration: “FastAPI responds with health info and metrics endpoints are available for ops.”

4) Admin Actions – Catalog & Revenue (2–3m)
- Back to Admin Dashboard.
- Demonstrate:
  - “Generate from Market Data” with a sample source.
  - “Add Catalog Item” (name, price, SKU).
  - Show Revenue History chart updates.
- Narration: “Catalog updates are immediate and revenue analytics consolidate per tenant.”

5) Monetization + Deploy (45–60s)
- Briefly show `investor_brief.pdf` (local path) and mention deploy targets.
- Narration: “We deploy backend to Cloud Run, frontend to Vercel. Assets like Investor Brief and demo script ship with the repo.”

6) Outro (15–30s)
- Return to architecture image or homepage.
- CTA: “To try it: set `VITE_API_BASE_URL`, run `npm run dev`, and point to your backend. For production, use Cloud Run/Vercel. Contact us for enterprise features.”

## OBS Tips
- Audio levels: keep mic peak between -12 and -6 dB.
- Hotkeys: assign `Start/Stop Recording` to easy keys.
- Scene switching: use OBS Studio Mode to preview before switching live.
- Keep browser zoom at 100% to avoid blurriness; use F11 full-screen if desired.

## Optional Script Snippets
- Health check:
  - `GET http://localhost:8004/api/health`.
- Market data generation (pseudo):
  - Run dashboard action and narrate how it aggregates sources.
- Catalog addition:
  - Add name/price, show UI update.

## Recording Checklist
- Backend up at `:8004`.
- Frontend up at `:5175`.
- Architecture image accessible at `:8009`.
- OBS set to 1080p/30fps, mic working, window capture correct.
- Press `Start Recording`, follow scene order, then `Stop Recording`.