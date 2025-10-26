param(
  [string]$BaseUrl = "http://localhost:8004",
  [string]$TenantId = "finops-demo",
  [string]$Action = "full", # full | start | status | tick
  [string]$MonitorId = "",
  [hashtable]$PriceOverrides = @{ "gpt-4" = 0.0025; "gemini-ultra" = 0.0018 }
)

Write-Host "Fetching API key for tenant: $TenantId" -ForegroundColor Cyan
$token = Invoke-RestMethod -Method GET -Uri "$BaseUrl/api/v1/auth/token/$TenantId"
$ApiKey = $token.api_key
$headers = @{ "X-API-KEY" = $ApiKey; "tenant_id" = $TenantId }
Write-Host "Using API key: $ApiKey" -ForegroundColor Green

Write-Host "Health check..." -ForegroundColor Cyan
$health = Invoke-RestMethod -Method GET -Uri "$BaseUrl/api/health"
Write-Host "Health: $($health.status)" -ForegroundColor Green

function Start-Monitor {
  param([string]$Window = "realtime")
  Write-Host "Starting FinOps monitor..." -ForegroundColor Cyan
  $startBody = @{ window = $Window }
  $start = Invoke-RestMethod -Method POST -Uri "$BaseUrl/api/v1/finops/monitor/start" -Headers $headers -Body ($startBody | ConvertTo-Json) -ContentType "application/json"
  return $start.monitor_id
}

function Get-MonitorStatus {
  param([string]$Id)
  $status = Invoke-RestMethod -Method GET -Uri "$BaseUrl/api/v1/finops/monitor/status/$Id" -Headers $headers
  Write-Host "Status: $($status.status) Window: $($status.window)" -ForegroundColor Green
}

function Tick-Monitor {
  param([string]$Id, [hashtable]$Overrides)
  Write-Host "Triggering monitor tick..." -ForegroundColor Cyan
  $tickBody = @{ monitor_id = $Id; price_overrides = $Overrides }
  $tick = Invoke-RestMethod -Method POST -Uri "$BaseUrl/api/v1/finops/monitor/tick" -Headers $headers -Body ($tickBody | ConvertTo-Json) -ContentType "application/json"
  Write-Host "Tick response status: $($tick.status)" -ForegroundColor Green
}

switch ($Action) {
  "start" {
    $MonitorId = Start-Monitor
    Write-Host "Monitor started: $MonitorId" -ForegroundColor Green
  }
  "status" {
    if (-not $MonitorId) { $MonitorId = Start-Monitor }
    Get-MonitorStatus -Id $MonitorId
  }
  "tick" {
    if (-not $MonitorId) { $MonitorId = Start-Monitor }
    Get-MonitorStatus -Id $MonitorId
    Tick-Monitor -Id $MonitorId -Overrides $PriceOverrides
    Get-MonitorStatus -Id $MonitorId
  }
  default { # full
    $MonitorId = Start-Monitor
    Get-MonitorStatus -Id $MonitorId
    Tick-Monitor -Id $MonitorId -Overrides $PriceOverrides
    Get-MonitorStatus -Id $MonitorId
  }
}