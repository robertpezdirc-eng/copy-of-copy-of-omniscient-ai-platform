# CI Smoke Tests: PayPal Sandbox Verification

This guide sets up minimal CI smoke tests to verify PayPal sandbox credentials and remote verification mode.

## Prerequisites
- Set the following repository secrets:
  - `PAYPAL_CLIENT_ID`
  - `PAYPAL_CLIENT_SECRET`
  - Optionally `PAYPAL_WEBHOOK_ID`
- Ensure `PAYPAL_VERIFY_MODE=remote` and `PAYPAL_ENV=sandbox` are set in the environment.

## .env Example
Use `.env.example` provided in the repo. In CI, pass env vars from secrets:

- `PAYPAL_VERIFY_MODE=remote`
- `PAYPAL_ENV=sandbox`
- `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET`

## GitHub Actions Example
```yaml
name: Smoke - PayPal Sandbox
on:
  workflow_dispatch:
  push:
    paths:
      - 'backend/**'
      - '.github/workflows/paypal-smoke.yml'

jobs:
  paypal-smoke:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set env
        env:
          PAYPAL_VERIFY_MODE: remote
          PAYPAL_ENV: sandbox
          PAYPAL_CLIENT_ID: ${{ secrets.PAYPAL_CLIENT_ID }}
          PAYPAL_CLIENT_SECRET: ${{ secrets.PAYPAL_CLIENT_SECRET }}
        run: |
          echo "PAYPAL_VERIFY_MODE=$PAYPAL_VERIFY_MODE" >> $GITHUB_ENV
          echo "PAYPAL_ENV=$PAYPAL_ENV" >> $GITHUB_ENV
          echo "PAYPAL_CLIENT_ID=$PAYPAL_CLIENT_ID" >> $GITHUB_ENV
          echo "PAYPAL_CLIENT_SECRET=$PAYPAL_CLIENT_SECRET" >> $GITHUB_ENV

      - name: OAuth token
        id: token
        run: |
          curl -s -u "$PAYPAL_CLIENT_ID:$PAYPAL_CLIENT_SECRET" \
            -d "grant_type=client_credentials" \
            https://api-m.sandbox.paypal.com/v1/oauth2/token > token.json
          cat token.json | jq -e '.access_token' > /dev/null

      - name: Verify API call
        run: |
          ACCESS_TOKEN=$(cat token.json | jq -r '.access_token')
          curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
            https://api-m.sandbox.paypal.com/v1/notifications/webhooks | jq -e '.webhooks' > /dev/null
```

## PowerShell Smoke (local)
```powershell
$clientId = $Env:PAYPAL_CLIENT_ID
$clientSecret = $Env:PAYPAL_CLIENT_SECRET
$pair = "$clientId:$clientSecret"
$headers = @{ Authorization = "Basic $([Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($pair)))" }
$body = @{ grant_type = "client_credentials" }
$response = Invoke-RestMethod -Uri https://api-m.sandbox.paypal.com/v1/oauth2/token -Method Post -Headers $headers -Body $body
$token = $response.access_token
Invoke-RestMethod -Uri https://api-m.sandbox.paypal.com/v1/notifications/webhooks -Headers @{ Authorization = "Bearer $token" } -Method Get
```

## Notes
- Sandbox endpoints use `api-m.sandbox.paypal.com`.
- Treat failures as non-blocking for initial smoke; report and continue.
- Expand tests later to validate `WEBHOOK_ID` and signature verification.