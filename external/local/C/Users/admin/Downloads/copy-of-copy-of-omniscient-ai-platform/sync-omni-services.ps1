# OMNI Services Synchronization Script (fixed)
# Sinhronizacija storitev med lokalnim Docker-jem in Google Cloud Run

param(
    [string]$ProjectId = "refined-graph-471712-n9",
    [string]$Region = "europe-west1",
    [switch]$ShowStatus,
    [switch]$SyncAll,
    [switch]$LocalOnly,
    [switch]$CloudOnly
)

$ErrorActionPreference = "Stop"

Write-Host "🔄 OMNI Platform - Services Synchronization" -ForegroundColor Cyan
Write-Host "Project: $ProjectId | Region: $Region" -ForegroundColor Yellow

function Get-Local-Docker-Status {
    Write-Host "`n🐳 Checking Local Docker Status..." -ForegroundColor Blue
    try {
        Write-Host "Running Containers (omni/quantum):" -ForegroundColor Green
        docker ps --filter "name=omni" --filter "name=quantum" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | ForEach-Object {
            if ($_ -notlike "*NAMES*") { Write-Host "  ✅ $_" -ForegroundColor Green }
        }
        Write-Host "`nAll Containers (omni/quantum):" -ForegroundColor Yellow
        docker ps -a --filter "name=omni" --filter "name=quantum" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | ForEach-Object {
            if ($_ -notlike "*NAMES*") {
                if ($_ -like "*Up*") { $color = "Green" } else { $color = "Red" }
                Write-Host "  📦 $_" -ForegroundColor $color
            }
        }
    } catch {
        Write-Host "❌ Docker not available or not running" -ForegroundColor Red
    }
}

function Get-Cloud-Run-Status {
    Write-Host "`n☁️  Checking Google Cloud Run Status..." -ForegroundColor Blue
    try {
        $cmd = "gcloud run services list --project=$ProjectId --format='table(metadata.name,metadata.labels.cloud\.googleapis\.com/location,status.url)'"
        iex $cmd
    } catch {
        Write-Host "❌ Cannot access Google Cloud Run. Check authentication." -ForegroundColor Red
    }
}

function Get-GCR-Images {
    Write-Host "`n📦 Checking Google Container Registry Images..." -ForegroundColor Blue
    try {
        $cmd = "gcloud container images list --repository=gcr.io/$ProjectId --format='table(name)'"
        iex $cmd
    } catch {
        Write-Host "❌ Cannot access Google Container Registry" -ForegroundColor Red
    }
}

function Sync-Missing-Services {
    Write-Host "`n🚀 Starting synchronization of missing services..." -ForegroundColor Magenta
    $deployScript = Join-Path (Get-Location) "deploy-missing-services.ps1"
    if (Test-Path $deployScript) {
        & $deployScript -ProjectId $ProjectId -Region $Region
    } else {
        Write-Host "❌ deploy-missing-services.ps1 not found" -ForegroundColor Red
    }
}

function Show-Deployment-Commands {
    Write-Host "`n📋 Available Deployment Commands:" -ForegroundColor Cyan
    Write-Host "Local Docker:" -ForegroundColor Yellow
    Write-Host "  docker-compose -f docker-compose.yml up -d"
    Write-Host "  docker-compose -f docker-compose.omni.yml up -d"
    Write-Host "  docker-compose -f docker-compose.quantum.yml up -d"
    Write-Host "`nGoogle Cloud Run:" -ForegroundColor Yellow
    Write-Host "  .\deploy-missing-services.ps1 -ProjectId $ProjectId -Region $Region"
    Write-Host "  gcloud builds submit --config cloudbuild.missing-services.yaml"
}

# Main execution
if ($ShowStatus) {
    Get-Local-Docker-Status
    Get-Cloud-Run-Status
    Get-GCR-Images
} elseif ($SyncAll) {
    Get-Local-Docker-Status
    Get-Cloud-Run-Status
    Get-GCR-Images
    Sync-Missing-Services
} elseif ($LocalOnly) {
    Get-Local-Docker-Status
    Write-Host "`n🐳 Local Docker Compose files:" -ForegroundColor Blue
    Get-ChildItem -Name "docker-compose*.yml" | ForEach-Object { Write-Host "  📄 $_" -ForegroundColor Green }
} elseif ($CloudOnly) {
    Get-Cloud-Run-Status
    Get-GCR-Images
} else {
    Show-Deployment-Commands
    Write-Host "`n🔧 Usage Examples:" -ForegroundColor Cyan
    Write-Host "  .\sync-omni-services.ps1 -ShowStatus    # Show detailed status"
    Write-Host "  .\sync-omni-services.ps1 -SyncAll       # Sync missing services"
    Write-Host "  .\sync-omni-services.ps1 -LocalOnly     # Show only local Docker"
    Write-Host "  .\sync-omni-services.ps1 -CloudOnly     # Show only Cloud services"
}