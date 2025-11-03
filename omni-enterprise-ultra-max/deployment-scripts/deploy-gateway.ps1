# Quick Gateway Deployment Script for PowerShell
# Run this from the omni-enterprise-ultra-max directory

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   AI Gateway Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will deploy the AI Gateway to Cloud Run." -ForegroundColor Yellow
Write-Host "The gateway will proxy to the existing backend:" -ForegroundColor Yellow
Write-Host "https://omni-ultra-backend-prod-661612368188.europe-west1.run.app" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to cancel, or any key to continue..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Set-Location gateway

Write-Host ""
Write-Host "Deploying gateway to Cloud Run..." -ForegroundColor Cyan
Write-Host "This will take 2-3 minutes..." -ForegroundColor Yellow
Write-Host ""

gcloud run deploy ai-gateway `
  --source=. `
  --region=europe-west1 `
  --project=refined-graph-471712-n9 `
  --allow-unauthenticated `
  --port=8080 `
  --set-env-vars="UPSTREAM_URL=https://omni-ultra-backend-prod-661612368188.europe-west1.run.app,API_KEYS=prod-key-omni-2025"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Getting gateway URL..." -ForegroundColor Yellow
$GATEWAY_URL = gcloud run services describe ai-gateway --region=europe-west1 --project=refined-graph-471712-n9 --format="value(status.url)"

Write-Host ""
Write-Host "Gateway URL: $GATEWAY_URL" -ForegroundColor Green
Write-Host ""
Write-Host "Test with PowerShell:" -ForegroundColor Yellow
Write-Host "Invoke-WebRequest -Uri `"$GATEWAY_URL/health`" -Headers @{`"x-api-key`"=`"prod-key-omni-2025`"}" -ForegroundColor White
Write-Host ""
Write-Host "Or with curl:" -ForegroundColor Yellow
Write-Host "curl -H `"x-api-key: prod-key-omni-2025`" $GATEWAY_URL/health" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
