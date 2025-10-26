[CmdletBinding()] param(
    [ValidateSet('Start','Scale','Test','Stop')]
    [string]$Action = 'Start',
    [int]$Workers = 1
)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Definition
$compose = Join-Path $here 'docker-compose.quantum.min.yml'
$envPath = Join-Path $here '.env'

function Get-EnvVars {
    param([string]$path)
    $vars = @{}
    if (Test-Path $path) {
        Get-Content $path | ForEach-Object {
            if ($_ -match '^(\w+)=(.*)$') {
                $vars[$matches[1]] = $matches[2]
            }
        }
    }
    return $vars
}

$envVars = Get-EnvVars -path $envPath
$apiPort = if ($envVars.ContainsKey('API_PORT')) { [int]$envVars['API_PORT'] } else { 8082 }
$platformUrl = if ($envVars.ContainsKey('QUANTUM_PLATFORM_URL')) { $envVars['QUANTUM_PLATFORM_URL'] } else { 'http://localhost:8080' }
$networkName = 'quantum-min_quantum-network'

function Start-Quantum {
    Write-Host "[Quantum] Building and starting minimal stack..." -ForegroundColor Cyan
    if (-not (Test-Path $compose)) { throw "Compose file not found: $compose" }
    docker compose -f $compose build
    docker compose -f $compose up -d
    Write-Host "[Quantum] Stack started: platform(8080), gateway($apiPort), worker(8084)" -ForegroundColor Green
}

function Stop-Quantum {
    Write-Host "[Quantum] Stopping and removing stack..." -ForegroundColor Yellow
    if (-not (Test-Path $compose)) { throw "Compose file not found: $compose" }
    docker compose -f $compose down
    Write-Host "[Quantum] Stack stopped." -ForegroundColor Green
}

function Scale-Workers {
    param([int]$count)
    if ($count -lt 1) { throw "Workers must be >= 1" }
    Write-Host "[Quantum] Scaling workers to $count (1 via Compose + additional via docker run)" -ForegroundColor Cyan

    # Ensure base stack is up
    docker compose -f $compose up -d quantum-worker
    docker compose -f $compose up -d quantum-platform quantum-api-gateway

    # Build worker image name based on compose project
    $workerImage = 'quantum-min-quantum-worker'

    # Create additional workers 2..count
    for ($i = 2; $i -le $count; $i++) {
        $name = "omni-quantum-worker-$i"
        $hostPort = 8084 + ($i - 1)
        $exists = docker ps -a --format '{{.Names}}' | Where-Object { $_ -eq $name }
        if ($exists) {
            Write-Host "[Quantum] Worker $name already exists, skipping." -ForegroundColor Yellow
            continue
        }
        Write-Host "[Quantum] Starting $name on host port $hostPort" -ForegroundColor Cyan
        docker run -d `
            --name $name `
            --network $networkName `
            -e WORKER_ID=$i `
            -e QUANTUM_PLATFORM_URL=$platformUrl `
            -p "$hostPort:8084" `
            $workerImage
    }
    Write-Host "[Quantum] Workers scaled. Active containers:" -ForegroundColor Green
    docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | Select-String 'omni-quantum-worker'
}

function Test-Endpoint {
    param([string]$Url,[string]$Name,[int]$Retries=10,[int]$DelaySec=3)
    for ($r=1; $r -le $Retries; $r++) {
        try {
            $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
            if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 300) {
                Write-Host "[OK] $Name responded $($resp.StatusCode)" -ForegroundColor Green
                return $true
            }
        } catch {
            Write-Host "[Wait] $Name not ready (attempt $r/$Retries)" -ForegroundColor Yellow
        }
        Start-Sleep -Seconds $DelaySec
    }
    Write-Host "[FAIL] $Name did not respond after $Retries attempts" -ForegroundColor Red
    return $false
}

function Test-Quantum {
    Write-Host "[Quantum] Testing connections..." -ForegroundColor Cyan
    $ok1 = Test-Endpoint -Url 'http://localhost:8080/health' -Name 'Quantum Platform'
    $ok2 = Test-Endpoint -Url "http://localhost:$apiPort/api/v1/health" -Name 'API Gateway'
    $ok3 = Test-Endpoint -Url 'http://localhost:8084/worker/health' -Name 'Worker #1'

    # Probe additional workers sequentially
    $overall = $ok1 -and $ok2 -and $ok3
    for ($i = 2; $i -le 20; $i++) {
        $port = 8084 + ($i - 1)
        $name = "Worker #$i"
        $exists = docker ps --format '{{.Names}}' | Where-Object { $_ -eq "omni-quantum-worker-$i" }
        if (-not $exists) { break }
        $okN = Test-Endpoint -Url "http://localhost:$port/worker/health" -Name $name
        $overall = $overall -and $okN
    }
    if ($overall) {
        Write-Host "[Quantum] All tested connections are healthy." -ForegroundColor Green
        exit 0
    } else {
        Write-Host "[Quantum] Some connections failed." -ForegroundColor Red
        exit 1
    }
}

switch ($Action) {
    'Start' { Start-Quantum }
    'Scale' { Scale-Workers -count $Workers }
    'Test'  { Test-Quantum }
    'Stop'  { Stop-Quantum }
}