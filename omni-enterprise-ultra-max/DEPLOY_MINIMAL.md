# Minimal Backend Deployment Instructions

## Current deployment (as of 2025‑11‑01)

- Backend (minimal): https://omni-ultra-backend-661612368188.europe-west1.run.app
- Gateway: https://ai-gateway-661612368188.europe-west1.run.app
- Gateway UPSTREAM_URL has been set to the backend URL above.


## After build completes successfully

Run this command to deploy the minimal backend:

```powershell
gcloud run deploy omni-ultra-backend `
  --image gcr.io/refined-graph-471712-n9/backend-minimal:latest `
  --region europe-west1 `
  --platform managed `
  --allow-unauthenticated `
  --port 8080 `
  --set-secrets OPENAI_API_KEY=OPENAI_API_KEY:latest `
  --min-instances 0 `
  --max-instances 10 `
  --memory 512Mi `
  --cpu 1 `
  --timeout 300 `
  --project refined-graph-471712-n9
```

## Then test end-to-end via gateway

```powershell
Invoke-RestMethod -Uri https://ai-gateway-661612368188.europe-west1.run.app/v1/chat/completions `
  -Method POST `
  -Headers @{
    'Authorization'='Bearer prod-key-omni-2025'
    'Content-Type'='application/json'
  } `
  -Body (@{
    model='gpt-4o-mini'
    messages=@(@{
      role='user'
      content='Test backend routing - say hello'
    })
  } | ConvertTo-Json -Depth 3 -Compress)
```

This should now route through the backend instead of falling back to OpenAI.

You can also verify the gateway/upstream health quickly:

```powershell
Invoke-RestMethod -Uri https://ai-gateway-661612368188.europe-west1.run.app/health -Headers @{ Authorization = 'Bearer prod-key-omni-2025' }
```

Expected response includes `upstream_ok: true`.

## Optional: run the gateway smoke test

This script sends an OpenAI-compatible request and writes a small report under `tests/`.

```powershell
# From repo root
$env:GATEWAY_URL = 'https://ai-gateway-661612368188.europe-west1.run.app'
$env:GATEWAY_TOKEN = 'prod-key-omni-2025'
python .\tests\openai_gateway_smoke.py
```

Exit code 0 indicates PASS; a JSON report file is created in `tests/`.

## Check build status

```powershell
gcloud builds list --limit=1 --project refined-graph-471712-n9 --format="table(id,status,images)"
```
