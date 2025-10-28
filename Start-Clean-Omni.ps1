Param(
  [string]$Services = "omni-backend,omni-prometheus,omni-grafana,omni-alertmanager,omni-loki,omni-tempo,omni-promtail,omni-pyroscope,omni-node-exporter,omni-cadvisor,omni-loggen,omni-telemetrygen,omni-kpi-ingestion"
)

Write-Host "[OMNI] Clean start initiated..." -ForegroundColor Cyan

try {
  docker compose down --remove-orphans | Out-Null
} catch {
  Write-Host "[OMNI] compose down failed (ignored): $_" -ForegroundColor Yellow
}

# Free common conflicts
foreach ($name in @('omni-prometheus','prometheus')) {
  try { docker rm -f $name | Out-Null } catch {}
}

Write-Host "[OMNI] Building omni-backend image..." -ForegroundColor Cyan
docker compose build omni-backend

$svcList = $Services.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
Write-Host "[OMNI] Starting services: $($svcList -join ', ')" -ForegroundColor Cyan
docker compose up -d --build $svcList

Write-Host "[OMNI] Waiting for backend health at http://localhost:8080/api/health ..." -ForegroundColor Cyan
$ok = $false
for ($i=0; $i -lt 30; $i++) {
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:8080/api/health" -TimeoutSec 3
    if ($r.StatusCode -eq 200) { $ok = $true; break }
  } catch { Start-Sleep -Seconds 2 }
}

if ($ok) {
  Write-Host "[OMNI] Backend is healthy." -ForegroundColor Green
} else {
  Write-Host "[OMNI] Backend did not become healthy in time." -ForegroundColor Red
}

Write-Host "[OMNI] Prometheus UI on http://localhost:9091, Grafana UI on http://localhost:3000" -ForegroundColor Cyan