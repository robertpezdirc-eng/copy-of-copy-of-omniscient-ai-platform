@echo off
REM Quick Gateway Deployment Script
REM Run this from the omni-enterprise-ultra-max directory

echo ========================================
echo   AI Gateway Deployment
echo ========================================
echo.
echo This will deploy the AI Gateway to Cloud Run.
echo The gateway will proxy to the existing backend:
echo https://omni-ultra-backend-prod-661612368188.europe-west1.run.app
echo.
echo Press Ctrl+C to cancel, or
pause

cd gateway

echo.
echo Deploying gateway to Cloud Run...
echo This will take 2-3 minutes...
echo.

gcloud run deploy ai-gateway ^
  --source=. ^
  --region=europe-west1 ^
  --project=refined-graph-471712-n9 ^
  --allow-unauthenticated ^
  --port=8080 ^
  --set-env-vars="UPSTREAM_URL=https://omni-ultra-backend-prod-661612368188.europe-west1.run.app,API_KEYS=prod-key-omni-2025"

echo.
echo ========================================
echo   Deployment Complete!
echo ========================================
echo.
echo Getting gateway URL...
for /f "delims=" %%i in ('gcloud run services describe ai-gateway --region^=europe-west1 --project^=refined-graph-471712-n9 --format^="value(status.url)"') do set GATEWAY_URL=%%i

echo.
echo Gateway URL: %GATEWAY_URL%
echo.
echo Test with:
echo curl -H "x-api-key: prod-key-omni-2025" %GATEWAY_URL%/health
echo.
pause
