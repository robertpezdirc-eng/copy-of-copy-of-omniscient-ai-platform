@echo off
set PROJECT=refined-graph-471712-n9
set REGION=europe-west1
set REPO=omni-ultra
set IMAGE=omni-frontend
set TAG=v1.0.0
set API=https://omni-ultra-backend-prod-661612368188.europe-west1.run.app
set WS=wss://omni-ultra-backend-prod-661612368188.europe-west1.run.app

echo Building & deploying frontend to Cloud Run...

gcloud builds submit ^
  --config=frontend/cloudbuild.yaml ^
  --project=%PROJECT% ^
  --substitutions=_PROJECT_ID=%PROJECT%,_REGION=%REGION%,_REPO=%REPO%,_IMAGE=%IMAGE%,_TAG=%TAG%,_VITE_API_URL=%API%,_VITE_WS_URL=%WS%

echo Fetching service URL...
for /f "delims=" %%i in ('gcloud run services describe omni-frontend --region^=%REGION% --project^=%PROJECT% --format^="value(status.url)"') do set FRONTEND_URL=%%i

echo Frontend URL: %FRONTEND_URL%
