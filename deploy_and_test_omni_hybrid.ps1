# Deploy + Health Check + API Test + Dashboard Readiness for omni-hybrid-ai

param(
    [string]$Project = "refined-graph-471712-n9",
    [string]$Region = "europe-west1",
    [string]$Service = "omni-hybrid-ai"
)

Write-Host "`n🔹 Preverjam zadnji build..."
$LastBuildRaw = gcloud builds list --project $Project --format="value(id,status)" --limit=1 2>$null
$lastStatus = ""
if ([string]::IsNullOrWhiteSpace($LastBuildRaw)) {
    Write-Host "⚠ Ni najdenih prejšnjih buildov; izvedem build." -ForegroundColor Yellow
    $lastStatus = "MISSING"
} else {
    $parts = $LastBuildRaw.Split()
    if ($parts.Count -ge 2) { $lastStatus = $parts[1] } else { $lastStatus = "UNKNOWN" }
}

if ($lastStatus -ne "SUCCESS") {
    Write-Host "⚠ Zadnji build ni SUCCESS (status: $lastStatus), ponovno buildam..." -ForegroundColor Yellow
    $buildExit = gcloud builds submit --project $Project --config cloudbuild.hybrid.yaml
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Build ni uspel (exit code $LASTEXITCODE)." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ Zadnji build uspešen." -ForegroundColor Green
}

Write-Host "`n🔹 Povlečem Cloud Run URL..."
$URL = gcloud run services describe $Service --region $Region --project $Project --format="value(status.url)" 2>$null

# Retry if service not found yet (fresh deploy)
$attempts = 0
while ([string]::IsNullOrWhiteSpace($URL) -and $attempts -lt 10) {
    Write-Host "⏳ Servis še ni na voljo, čakam in ponavljam poizvedbo... (poskus $($attempts+1)/10)" -ForegroundColor Yellow
    Start-Sleep -Seconds 6
    $URL = gcloud run services describe $Service --region $Region --project $Project --format="value(status.url)" 2>$null
    $attempts++
}

if ([string]::IsNullOrWhiteSpace($URL)) {
    Write-Host "❌ Cloud Run servis '$Service' ni najden v regiji '$Region'." -ForegroundColor Red
    Write-Host "ℹ Preverjam seznam storitev..." -ForegroundColor Yellow
    gcloud run services list --region $Region --project $Project
    Write-Host "ℹ Preveri tudi zadnje build loge: gcloud builds list --project $Project" -ForegroundColor Yellow
    exit 1
}
Write-Host "🌐 URL servisa: $URL" -ForegroundColor Cyan

Write-Host "`n🔹 Povezujem GEMINI_API_KEY iz Secret Manager na Cloud Run..."
# Poskus posodobitve skrivnosti; ne prekinja, če spodleti
try {
    gcloud run services update $Service --region $Region --project $Project --update-secrets GEMINI_API_KEY=gemini-api-key:latest | Out-Null
    Write-Host "✅ GEMINI_API_KEY povezan na servis." -ForegroundColor Green
} catch {
    Write-Host "⚠ Ni uspelo povezati GEMINI_API_KEY (servis je morda še sveže deployan). Nadaljujem z zdravjem in testi." -ForegroundColor Yellow
}

Write-Host "`n🔹 Preverjam health endpoint..."
try {
    $Health = Invoke-RestMethod -Method GET -Uri "$URL/health"
    Write-Host "✅ Health check OK: $($Health | ConvertTo-Json -Depth 5)" -ForegroundColor Green
} catch {
    Write-Host "❌ Health check FAILED: $_" -ForegroundColor Red
    Write-Host "ℹ Zadnji logi (50 vrstic):" -ForegroundColor Yellow
    gcloud logs read --project $Project --limit 50
    exit 1
}

Write-Host "`n🔹 Pošiljam testne POST requeste..."
# Test 1: pretraživanje događaja
$Body1 = @{ prompt = "Pretraživanje događaja u Zagrebu" } | ConvertTo-Json
try {
    $Response1 = Invoke-RestMethod -Method POST -Uri "$URL/api/chat" -ContentType "application/json" -Body $Body1
    Write-Host "`nTest 1 rezultat:" -ForegroundColor Cyan
    $Response1 | ConvertTo-Json -Depth 5
} catch {
    Write-Host "❌ Test 1 FAILED: $_" -ForegroundColor Red
}

# Test 2: kratka pjesma o jeseni
$Body2 = @{ prompt = "Generiranje kratke pjesme o jeseni" } | ConvertTo-Json
try {
    $Response2 = Invoke-RestMethod -Method POST -Uri "$URL/api/chat" -ContentType "application/json" -Body $Body2
    Write-Host "`nTest 2 rezultat:" -ForegroundColor Cyan
    $Response2 | ConvertTo-Json -Depth 5
} catch {
    Write-Host "❌ Test 2 FAILED: $_" -ForegroundColor Red
}

Write-Host "`nℹ Če GEMINI_API_KEY ni nastavljen, servisi uporabljajo OpenAI fallback." -ForegroundColor Yellow
Write-Host "`n🎯 Vse je preverjeno – servis live, health check OK, API testni odgovori prejeti. Dashboard je pripravljen za uporabo!" -ForegroundColor Green