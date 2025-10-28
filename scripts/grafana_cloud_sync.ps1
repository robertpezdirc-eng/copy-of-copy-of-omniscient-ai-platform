# OMNI Platform - Grafana Cloud Sync Script
param(
    [Parameter(Mandatory=$false)]
    [string]$Action = "status",
    
    [Parameter(Mandatory=$false)]
    [string]$DashboardUid = "omni_local_comprehensive",
    
    [Parameter(Mandatory=$false)]
    [string]$LocalGrafanaUrl = "http://localhost:3000",
    
    [Parameter(Mandatory=$false)]
    [string]$LocalAuth = "admin:admin123"
)

# Load environment variables from .env file
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}

$GrafanaCloudUrl = $env:GRAFANA_CLOUD_URL
$GrafanaCloudApiKey = $env:GRAFANA_CLOUD_API_KEY

function Test-GrafanaConnection {
    param([string]$Url, [string]$Auth)
    
    try {
        $headers = @{}
        if ($Auth.Contains(":")) {
            $bytes = [System.Text.Encoding]::ASCII.GetBytes($Auth)
            $base64 = [System.Convert]::ToBase64String($bytes)
            $headers["Authorization"] = "Basic $base64"
        } else {
            $headers["Authorization"] = "Bearer $Auth"
        }
        
        $response = Invoke-RestMethod -Uri "$Url/api/health" -Headers $headers -Method Get
        Write-Host "Connection to $Url successful" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "Connection to $Url failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Show-Status {
    Write-Host "OMNI Platform Grafana Status" -ForegroundColor Yellow
    Write-Host "============================" -ForegroundColor Yellow
    
    # Test local Grafana
    Write-Host "Local Grafana:" -ForegroundColor Cyan
    if (Test-GrafanaConnection -Url $LocalGrafanaUrl -Auth $LocalAuth) {
        Write-Host "   URL: $LocalGrafanaUrl" -ForegroundColor White
        Write-Host "   Status: Running" -ForegroundColor Green
    }
    
    # Test Grafana Cloud
    Write-Host "Grafana Cloud:" -ForegroundColor Cyan
    if ($GrafanaCloudUrl -and $GrafanaCloudApiKey) {
        if (Test-GrafanaConnection -Url $GrafanaCloudUrl -Auth $GrafanaCloudApiKey) {
            Write-Host "   URL: $GrafanaCloudUrl" -ForegroundColor White
            Write-Host "   Status: Connected" -ForegroundColor Green
        }
    } else {
        Write-Host "   Status: Not configured" -ForegroundColor Yellow
    }
    
    # Show available dashboards
    Write-Host "Available Dashboards:" -ForegroundColor Cyan
    $dashboards = @(
        "omni_local_comprehensive",
        "omni_business", 
        "omni_business_integrations",
        "omni_jira_professional",
        "omni_unified_all"
    )
    
    foreach ($dashboard in $dashboards) {
        Write-Host "   - $dashboard" -ForegroundColor White
    }
}

# Main execution
switch ($Action.ToLower()) {
    "status" {
        Show-Status
    }
    
    default {
        Write-Host "Usage: grafana_cloud_sync.ps1 -Action status" -ForegroundColor Yellow
        Write-Host "Available actions: status" -ForegroundColor Cyan
    }
}