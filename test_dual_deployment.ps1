# Test Dual Deployment Script (ASCII-safe)
# Testira backend in frontend servise po uspešnem deployu

Write-Host "Testiranje Omni Dual Deployment..." -ForegroundColor Cyan

# 1) Preveri zadnji build status
Write-Host "1) Preverjam zadnji Cloud Build status..." -ForegroundColor Yellow
$buildStatus = gcloud builds list --format="value(status)" --limit=1 --project refined-graph-471712-n9
$color = if ($buildStatus -eq "SUCCESS") { "Green" } else { "Red" }
Write-Host ("Build Status: {0}" -f $buildStatus) -ForegroundColor $color

if ($buildStatus -ne "SUCCESS") {
    Write-Host "Build ni uspešen. Prekinjam testiranje." -ForegroundColor Red
    exit 1
}

# 2) Pridobi URL-je servisov
Write-Host "2) Pridobivam URL-je servisov..." -ForegroundColor Yellow

$backendUrl = gcloud run services describe omni-backend --platform managed --region europe-west1 --format="value(status.url)" --project refined-graph-471712-n9
$frontendUrl = gcloud run services describe omni-frontend --platform managed --region europe-west1 --format="value(status.url)" --project refined-graph-471712-n9

Write-Host ("Backend URL: {0}" -f $backendUrl) -ForegroundColor Green
Write-Host ("Frontend URL: {0}" -f $frontendUrl) -ForegroundColor Green

# 3) Health check backend
Write-Host "3) Health check backend..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri ("{0}/health" -f $backendUrl) -Method GET
    Write-Host ("Backend Health: {0}" -f $healthResponse.status) -ForegroundColor Green
    Write-Host ("Timestamp: {0}" -f $healthResponse.timestamp) -ForegroundColor Gray
} catch {
    Write-Host ("Backend health check failed: {0}" -f $_.Exception.Message) -ForegroundColor Red
}

# 4) Test providers endpoint
Write-Host "4) Testiram providers endpoint..." -ForegroundColor Yellow
try {
    $providersResponse = Invoke-RestMethod -Uri ("{0}/health/providers" -f $backendUrl) -Method GET
    Write-Host "Providers Response:" -ForegroundColor Green
    $providersResponse | ConvertTo-Json -Depth 3 | Write-Host -ForegroundColor Gray
} catch {
    Write-Host ("Providers endpoint failed: {0}" -f $_.Exception.Message) -ForegroundColor Red
}

# 5) Test chat endpoint z OpenAI
Write-Host "5) Testiram chat z OpenAI..." -ForegroundColor Yellow
$chatPayload1 = @{
    message = "Povej kratko šalo o računalnikih."
    provider = "openai"
} | ConvertTo-Json

try {
    $chatResponse1 = Invoke-RestMethod -Uri ("{0}/api/chat" -f $backendUrl) -Method POST -Body $chatPayload1 -ContentType "application/json"
    Write-Host "OpenAI Response:" -ForegroundColor Green
    Write-Host ("Provider: {0}" -f $chatResponse1.provider) -ForegroundColor Cyan
    Write-Host ("Model: {0}" -f $chatResponse1.model) -ForegroundColor Cyan
    Write-Host ("Response: {0}" -f $chatResponse1.response) -ForegroundColor White
} catch {
    Write-Host ("OpenAI chat failed: {0}" -f $_.Exception.Message) -ForegroundColor Red
}

# 6) Test chat endpoint z Gemini
Write-Host "6) Testiram chat z Gemini..." -ForegroundColor Yellow
$chatPayload2 = @{
    message = "Generiraj seznam 3 idej za AI projekt."
    provider = "gemini"
} | ConvertTo-Json

try {
    $chatResponse2 = Invoke-RestMethod -Uri ("{0}/api/chat" -f $backendUrl) -Method POST -Body $chatPayload2 -ContentType "application/json"
    Write-Host "Gemini Response:" -ForegroundColor Green
    Write-Host ("Provider: {0}" -f $chatResponse2.provider) -ForegroundColor Cyan
    Write-Host ("Model: {0}" -f $chatResponse2.model) -ForegroundColor Cyan
    Write-Host ("Response: {0}" -f $chatResponse2.response) -ForegroundColor White
} catch {
    Write-Host ("Gemini chat failed: {0}" -f $_.Exception.Message) -ForegroundColor Red
}

# 7) Test frontend dostopnost
Write-Host "7) Testiram frontend dostopnost..." -ForegroundColor Yellow
try {
    $frontendResponse = Invoke-WebRequest -Uri $frontendUrl -Method GET
    if ($frontendResponse.StatusCode -eq 200) {
        Write-Host ("Frontend je dostopen (Status: {0})" -f $frontendResponse.StatusCode) -ForegroundColor Green
        if ($frontendResponse.Content -match "Omni Dashboard") {
            Write-Host "Frontend vsebuje pravilno vsebino" -ForegroundColor Green
        } else {
            Write-Host "Frontend ne vsebuje pričakovane vsebine" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host ("Frontend test failed: {0}" -f $_.Exception.Message) -ForegroundColor Red
}

Write-Host "Testiranje končano!" -ForegroundColor Cyan
Write-Host "Povzetek URL-jev:" -ForegroundColor Yellow
Write-Host ("Frontend (Chat UI): {0}" -f $frontendUrl) -ForegroundColor Green
Write-Host ("Backend (API): {0}" -f $backendUrl) -ForegroundColor Green
Write-Host "Namig: Odpri frontend URL v brskalniku za interaktivni chat!" -ForegroundColor Cyan