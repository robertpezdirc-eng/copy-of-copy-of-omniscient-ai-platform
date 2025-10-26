i
 manjka prevei ce je# OMNI Platform Professional Dashboard Deployment Script (PowerShell)
Write-Host "🚀 OMNI Platform Professional Dashboard Deployment" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# 1. Check Python installation
Write-Status "Checking Python installation..."
try {
    $pythonVersion = & python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Python found: $pythonVersion"
    } else {
        throw "Python not found"
    }
} catch {
    Write-Error-Custom "Python is not installed. Please install Python 3.8 or higher."
    exit 1
}

# 2. Create necessary directories
Write-Status "Creating necessary directories..."
$directories = @(
    "omni_platform\static",
    "omni_platform\templates",
    "omni_platform\logs",
    "grafana\dashboards",
    "grafana\datasources"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Success "Created directory: $dir"
    } else {
        Write-Status "Directory already exists: $dir"
    }
}

# 3. Install Python dependencies
Write-Status "Installing Python dependencies..."
if (Test-Path "requirements.txt") {
    try {
        & pip install -r requirements.txt
        Write-Success "Python dependencies installed"
    } catch {
        Write-Warning "Failed to install from requirements.txt. Installing basic dependencies..."
        & pip install fastapi uvicorn plotly pandas psutil python-multipart python-jose[cryptography] passlib[bcrypt]
    }
} else {
    Write-Warning "requirements.txt not found. Installing basic dependencies..."
    & pip install fastapi uvicorn plotly pandas psutil python-multipart python-jose[cryptography] passlib[bcrypt]
}

# 4. Create GCP credentials template if it doesn't exist
if (!(Test-Path "gcp-credentials.json")) {
    Write-Status "Creating GCP credentials template..."
    $gcpTemplate = @"
{
  "type": "service_account",
  "project_id": "your-gcp-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
}
"@
    Set-Content -Path "gcp-credentials.json" -Value $gcpTemplate
    Write-Warning "Created GCP credentials template. Please update with your actual credentials."
}

# 5. Set environment variables
Write-Status "Setting up environment..."
$env:GOOGLE_CLOUD_PROJECT = if ($env:GOOGLE_CLOUD_PROJECT) { $env:GOOGLE_CLOUD_PROJECT } else { "omni-platform-2024" }
$env:OMNI_ENV = if ($env:OMNI_ENV) { $env:OMNI_ENV } else { "production" }

Write-Success "Environment configured"

# 6. Start the dashboard
Write-Status "Starting OMNI Platform Professional Dashboard..."
Write-Host ""
Write-Host "🎉 OMNI Platform Professional Dashboard" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Starting the enterprise dashboard..." -ForegroundColor Yellow
Write-Host "This may take a few moments..." -ForegroundColor Yellow
Write-Host ""

try {
    # Start the dashboard in a new PowerShell process
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = "python"
    $startInfo.Arguments = "omni_dashboard_professional.py"
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $false

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    $process.Start() | Out-Null

    # Wait a moment for startup
    Start-Sleep -Seconds 3

    # Get IP address
    $ipAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike "*Loopback*"} | Select-Object -First 1).IPAddress

    Write-Host ""
    Write-Success "OMNI Dashboard is now running!"
    Write-Host ""
    Write-Host "📊 Dashboard URLs:" -ForegroundColor Cyan
    Write-Host "   Main Dashboard: http://$ipAddress`:8080" -ForegroundColor Green
    Write-Host "   Login Page: http://$ipAddress`:8080/login" -ForegroundColor Green
    Write-Host "   Health Check: http://$ipAddress`:8080/api/health" -ForegroundColor Green
    Write-Host "   API Documentation: http://$ipAddress`:8080/api/docs" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔑 Login Credentials:" -ForegroundColor Cyan
    Write-Host "   Username: admin" -ForegroundColor Yellow
    Write-Host "   Password: omni_admin_2024" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "☁️ Google Cloud Integration:" -ForegroundColor Cyan
    Write-Host "   - Update gcp-credentials.json with your service account key" -ForegroundColor Yellow
    Write-Host "   - Set GOOGLE_CLOUD_PROJECT environment variable" -ForegroundColor Yellow
    Write-Host "   - Restart dashboard to apply GCP integration" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "📊 Features:" -ForegroundColor Cyan
    Write-Host "   ✅ Real-time system monitoring" -ForegroundColor Green
    Write-Host "   ✅ Google Cloud integration" -ForegroundColor Green
    Write-Host "   ✅ JWT authentication" -ForegroundColor Green
    Write-Host "   ✅ Interactive charts and graphs" -ForegroundColor Green
    Write-Host "   ✅ Service status monitoring" -ForegroundColor Green
    Write-Host "   ✅ Alert management" -ForegroundColor Green
    Write-Host "   ✅ Professional UI/UX" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔧 Management Commands:" -ForegroundColor Cyan
    Write-Host "   Check status: Get-Process python" -ForegroundColor Yellow
    Write-Host "   View logs: Get-Content omni_platform\logs\omni_dashboard.log -Tail 20" -ForegroundColor Yellow
    Write-Host "   Stop dashboard: Stop-Process -Name python" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press Ctrl+C to stop the dashboard..." -ForegroundColor Red
    Write-Host ""

    # Keep the script running
    $process.WaitForExit()

} catch {
    Write-Error-Custom "Failed to start dashboard: $($_.Exception.Message)"
    Write-Host ""
    Write-Host "🔍 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "   1. Check if port 8080 is available" -ForegroundColor Gray
    Write-Host "   2. Verify Python dependencies are installed" -ForegroundColor Gray
    Write-Host "   3. Check the logs in omni_platform\logs\omni_dashboard.log" -ForegroundColor Gray
    Write-Host ""
    exit 1
}