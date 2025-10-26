# Deploy Missing Services to Google Cloud Run
# Skript za deployment manjkajočih OMNI storitev na Google Cloud Run

param(
    [string]$ProjectId = "refined-graph-471712-n9",
    [string]$Region = "europe-west1",
    [switch]$BuildOnly,
    [switch]$DeployOnly
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 OMNI Platform - Deployment manjkajočih storitev" -ForegroundColor Cyan
Write-Host "Project: $ProjectId" -ForegroundColor Yellow
Write-Host "Region: $Region" -ForegroundColor Yellow

# Manjkajoče storitve za deployment
$MissingServices = @(
    @{
        Name = "omni-api"
        Dockerfile = "Dockerfile.backend"
        Port = 8080
        Memory = "1Gi"
        CPU = "1"
        MaxInstances = 5
        EnvVars = @(
            "OMNI_ENV=production",
            "GOOGLE_CLOUD_PROJECT=$ProjectId"
        )
    },
    @{
        Name = "omni-singularity"
        Dockerfile = "Dockerfile.omni-singularity"
        Port = 8093
        Memory = "2Gi"
        CPU = "2"
        MaxInstances = 3
        EnvVars = @(
            "OMNI_VERSION=10.0",
            "OMNI_MODE=full",
            "QUANTUM_ACCELERATION=true",
            "GOOGLE_CLOUD_PROJECT=$ProjectId"
        )
    },
    @{
        Name = "omni-quantum-backend"
        Dockerfile = "Dockerfile.quantum-platform"
        Port = 8080
        Memory = "2Gi"
        CPU = "2"
        MaxInstances = 3
        EnvVars = @(
            "QUANTUM_PLATFORM_MODE=production",
            "QUANTUM_CORES_MAX=10",
            "GOOGLE_CLOUD_PROJECT=$ProjectId"
        )
    },
    @{
        Name = "omni-api-gateway"
        Dockerfile = "Dockerfile.api-gateway"
        Port = 8082
        Memory = "1Gi"
        CPU = "1"
        MaxInstances = 5
        EnvVars = @(
            "API_PORT=8082",
            "ENABLE_CORS=true",
            "GOOGLE_CLOUD_PROJECT=$ProjectId"
        )
    },
    @{
        Name = "quantum-worker"
        Dockerfile = "Dockerfile.quantum-worker"
        Port = 8080
        Memory = "1Gi"
        CPU = "1"
        MaxInstances = 10
        EnvVars = @(
            "WORKER_MODE=production",
            "GOOGLE_CLOUD_PROJECT=$ProjectId"
        )
    },
    @{
        Name = "quantum-entanglement-node"
        Dockerfile = "Dockerfile.quantum-entanglement"
        Port = 8080
        Memory = "1Gi"
        CPU = "1"
        MaxInstances = 5
        EnvVars = @(
            "NODE_MODE=production",
            "GOOGLE_CLOUD_PROJECT=$ProjectId"
        )
    }
)

function Build-And-Push-Image {
    param($Service)
    
    $ImageName = "gcr.io/$ProjectId/$($Service.Name):latest"
    
    Write-Host "🔨 Building $($Service.Name)..." -ForegroundColor Green
    
    # Preverimo, če Dockerfile obstaja
    if (-not (Test-Path $Service.Dockerfile)) {
        Write-Host "⚠️  Dockerfile $($Service.Dockerfile) ne obstaja. Ustvarjam osnovni Dockerfile..." -ForegroundColor Yellow
        Create-Basic-Dockerfile -ServiceName $Service.Name -DockerfilePath $Service.Dockerfile
    }
    
    # Build Docker image
    docker build -f $Service.Dockerfile -t $ImageName .
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Build failed za $($Service.Name)" -ForegroundColor Red
        return $false
    }
    
    # Push to GCR
    Write-Host "📤 Pushing $ImageName..." -ForegroundColor Blue
    docker push $ImageName
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Push failed za $($Service.Name)" -ForegroundColor Red
        return $false
    }
    
    Write-Host "✅ $($Service.Name) uspešno built in pushed" -ForegroundColor Green
    return $true
}

function Deploy-To-CloudRun {
    param($Service)
    
    $ImageName = "gcr.io/$ProjectId/$($Service.Name):latest"
    
    Write-Host "🚀 Deploying $($Service.Name) to Cloud Run..." -ForegroundColor Magenta
    
    # Pripravimo env vars
    $EnvVarsString = ""
    if ($Service.EnvVars.Count -gt 0) {
        $EnvVarsString = "--set-env-vars=" + ($Service.EnvVars -join ",")
    }
    
    # Deploy to Cloud Run
    $DeployCmd = @(
        "gcloud", "run", "deploy", $Service.Name,
        "--image", $ImageName,
        "--region", $Region,
        "--platform", "managed",
        "--allow-unauthenticated",
        "--port", $Service.Port,
        "--memory", $Service.Memory,
        "--cpu", $Service.CPU,
        "--max-instances", $Service.MaxInstances,
        "--timeout", "300"
    )
    
    if ($EnvVarsString) {
        $DeployCmd += $EnvVarsString
    }
    
    & $DeployCmd[0] $DeployCmd[1..($DeployCmd.Length-1)]
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ $($Service.Name) uspešno deployed" -ForegroundColor Green
        return $true
    } else {
        Write-Host "❌ Deployment failed za $($Service.Name)" -ForegroundColor Red
        return $false
    }
}

function Create-Basic-Dockerfile {
    param($ServiceName, $DockerfilePath)
    
    $DockerfileContent = @"
# Basic Dockerfile for $ServiceName
FROM python:3.11-alpine

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run application
CMD ["python", "main.py"]
"@
    
    Set-Content -Path $DockerfilePath -Value $DockerfileContent
    Write-Host "📝 Ustvarjen osnovni Dockerfile: $DockerfilePath" -ForegroundColor Yellow
}

# Main execution
try {
    # Authenticate with gcloud
    Write-Host "🔐 Checking gcloud authentication..." -ForegroundColor Blue
    gcloud auth list --filter="status:ACTIVE" --format="value(account)" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Gcloud authentication required. Run: gcloud auth login" -ForegroundColor Red
        exit 1
    }
    
    # Set project
    gcloud config set project $ProjectId
    
    # Configure Docker for GCR
    gcloud auth configure-docker --quiet
    
    $SuccessfulDeployments = @()
    $FailedDeployments = @()
    
    foreach ($Service in $MissingServices) {
        Write-Host "`n" + "="*50 -ForegroundColor Cyan
        Write-Host "Processing: $($Service.Name)" -ForegroundColor Cyan
        Write-Host "="*50 -ForegroundColor Cyan
        
        $BuildSuccess = $true
        $DeploySuccess = $true
        
        if (-not $DeployOnly) {
            $BuildSuccess = Build-And-Push-Image -Service $Service
        }
        
        if ($BuildSuccess -and -not $BuildOnly) {
            $DeploySuccess = Deploy-To-CloudRun -Service $Service
        }
        
        if ($BuildSuccess -and $DeploySuccess) {
            $SuccessfulDeployments += $Service.Name
        } else {
            $FailedDeployments += $Service.Name
        }
    }
    
    # Summary
    Write-Host "`n" + "="*60 -ForegroundColor Green
    Write-Host "DEPLOYMENT SUMMARY" -ForegroundColor Green
    Write-Host "="*60 -ForegroundColor Green
    
    if ($SuccessfulDeployments.Count -gt 0) {
        Write-Host "✅ Uspešno deployed:" -ForegroundColor Green
        $SuccessfulDeployments | ForEach-Object { Write-Host "   - $_" -ForegroundColor Green }
    }
    
    if ($FailedDeployments.Count -gt 0) {
        Write-Host "❌ Failed deployments:" -ForegroundColor Red
        $FailedDeployments | ForEach-Object { Write-Host "   - $_" -ForegroundColor Red }
    }
    
    Write-Host "`n🌐 Cloud Run Services:" -ForegroundColor Blue
    gcloud run services list --project=$ProjectId --region=$Region
    
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}