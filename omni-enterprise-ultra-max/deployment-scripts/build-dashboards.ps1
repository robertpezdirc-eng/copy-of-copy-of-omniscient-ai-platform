#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Build AI-powered dashboards using Ollama

.DESCRIPTION
    CLI tool for generating React TypeScript dashboards using the Dashboard Builder service.
    Uses Ollama AI to generate 20+ different dashboard types with charts, WebSocket support, and responsive design.

.PARAMETER Action
    Action to perform: list, build-all, build-priority, build-single, status, generated

.PARAMETER Priority
    Filter by priority: 1 (high), 2 (medium), 3 (low)

.PARAMETER Dashboard
    Dashboard name to build (for build-single action)

.PARAMETER Url
    Backend URL (default: http://localhost:8080)

.EXAMPLE
    .\build-dashboards.ps1 -Action list
    List all available dashboard types

.EXAMPLE
    .\build-dashboards.ps1 -Action build-priority -Priority 1
    Build all high-priority dashboards (6 dashboards)

.EXAMPLE
    .\build-dashboards.ps1 -Action build-all
    Build all 20 dashboards

.EXAMPLE
    .\build-dashboards.ps1 -Action build-single -Dashboard "Revenue Analytics"
    Build a single dashboard by name

.EXAMPLE
    .\build-dashboards.ps1 -Action status
    Check builder status and Ollama health

.EXAMPLE
    .\build-dashboards.ps1 -Action generated
    List all generated dashboard files
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("list", "build-all", "build-priority", "build-single", "status", "generated")]
    [string]$Action,

    [Parameter(Mandatory=$false)]
    [ValidateSet(1, 2, 3)]
    [int]$Priority,

    [Parameter(Mandatory=$false)]
    [string]$Dashboard,

    [Parameter(Mandatory=$false)]
    [string]$Url = "http://localhost:8080"
)

# Colors
function Write-Success { Write-Host "✅ $args" -ForegroundColor Green }
function Write-Info { Write-Host "ℹ️  $args" -ForegroundColor Cyan }
function Write-Warning { Write-Host "⚠️  $args" -ForegroundColor Yellow }
function Write-Error { Write-Host "❌ $args" -ForegroundColor Red }
function Write-Header { Write-Host "`n🎨 $args`n" -ForegroundColor Magenta }

# Base API URL
$BaseUrl = "$Url/api/v1/dashboards"

# Actions
switch ($Action) {
    "list" {
        Write-Header "Available Dashboard Types"
        
        try {
            $response = Invoke-RestMethod -Uri "$BaseUrl/types" -Method GET
            
            Write-Info "Total dashboards available: $($response.dashboards.Count)"
            Write-Host ""

            # Group by priority
            $priorities = @{
                1 = @{ name = "High Priority ⭐⭐⭐"; color = "Green"; dashboards = @() }
                2 = @{ name = "Medium Priority ⭐⭐"; color = "Yellow"; dashboards = @() }
                3 = @{ name = "Low Priority ⭐"; color = "Gray"; dashboards = @() }
            }

            foreach ($dashboard in $response.dashboards) {
                $priorities[$dashboard.priority].dashboards += $dashboard
            }

            foreach ($p in 1..3) {
                $group = $priorities[$p]
                Write-Host $group.name -ForegroundColor $group.color
                Write-Host ("=" * 60)
                
                foreach ($d in $group.dashboards) {
                    Write-Host "  • " -NoNewline
                    Write-Host "$($d.name)" -ForegroundColor White -NoNewline
                    Write-Host " - $($d.description)" -ForegroundColor DarkGray
                    Write-Host "    Endpoints: $($d.endpoints -join ', ')" -ForegroundColor DarkGray
                }
                Write-Host ""
            }

            Write-Success "Use -Action build-priority -Priority 1 to build high-priority dashboards"
        }
        catch {
            Write-Error "Failed to list dashboards: $_"
            exit 1
        }
    }

    "status" {
        Write-Header "Dashboard Builder Status"
        
        try {
            $response = Invoke-RestMethod -Uri "$BaseUrl/build/status" -Method GET
            
            Write-Host "Configuration:" -ForegroundColor Cyan
            Write-Host "  Backend URL: $($response.backend_url)" -ForegroundColor White
            Write-Host "  GitHub Repo: $($response.github_repo)" -ForegroundColor White
            Write-Host "  Total Dashboards: $($response.total_dashboards)" -ForegroundColor White
            Write-Host ""

            Write-Host "Ollama Status:" -ForegroundColor Cyan
            if ($response.ollama_healthy) {
                Write-Success "  Status: Healthy"
            } else {
                Write-Warning "  Status: Unavailable (will use templates)"
            }

            Write-Host "  Enabled: $($response.ollama_enabled)" -ForegroundColor White
            Write-Host "  URL: $($response.ollama_url)" -ForegroundColor White
            Write-Host "  Model: $($response.ollama_model)" -ForegroundColor White
        }
        catch {
            Write-Error "Failed to get status: $_"
            exit 1
        }
    }

    "build-priority" {
        if (-not $Priority) {
            Write-Error "Priority parameter is required for build-priority action"
            Write-Info "Use: -Priority 1 (high), -Priority 2 (medium), or -Priority 3 (low)"
            exit 1
        }

        $priorityNames = @{ 1 = "High"; 2 = "Medium"; 3 = "Low" }
        Write-Header "Building $($priorityNames[$Priority]) Priority Dashboards"

        try {
            $body = @{
                priority_filter = $Priority
                save_to_disk = $true
                output_dir = "dashboards/generated"
            } | ConvertTo-Json

            Write-Info "Sending request to Ollama... (this may take a few minutes)"
            $response = Invoke-RestMethod -Uri "$BaseUrl/build" `
                -Method POST `
                -ContentType "application/json" `
                -Body $body

            Write-Host ""
            Write-Success "Built $($response.count) dashboards"
            
            Write-Host "`nGenerated Dashboards:" -ForegroundColor Cyan
            foreach ($d in $response.dashboards) {
                if ($d.success) {
                    Write-Host "  ✅ " -ForegroundColor Green -NoNewline
                    Write-Host "$($d.name)" -ForegroundColor White -NoNewline
                    if ($d.file) {
                        Write-Host " → $($d.file)" -ForegroundColor DarkGray
                    } else {
                        Write-Host ""
                    }
                } else {
                    Write-Host "  ❌ " -ForegroundColor Red -NoNewline
                    Write-Host "$($d.name)" -ForegroundColor White -NoNewline
                    Write-Host " - $($d.error)" -ForegroundColor Red
                }
            }

            if ($response.saved_to) {
                Write-Host ""
                Write-Success "Dashboards saved to: $($response.saved_to)"
            }
        }
        catch {
            Write-Error "Failed to build dashboards: $_"
            Write-Info "Check backend logs for details"
            exit 1
        }
    }

    "build-all" {
        Write-Header "Building ALL Dashboards (20 total)"
        Write-Warning "This will take several minutes..."

        try {
            $body = @{
                save_to_disk = $true
                output_dir = "dashboards/generated"
            } | ConvertTo-Json

            Write-Info "Sending request to Ollama..."
            $response = Invoke-RestMethod -Uri "$BaseUrl/build" `
                -Method POST `
                -ContentType "application/json" `
                -Body $body

            Write-Host ""
            Write-Success "Built $($response.count) dashboards"
            
            Write-Host "`nGenerated Dashboards:" -ForegroundColor Cyan
            foreach ($d in $response.dashboards) {
                if ($d.success) {
                    Write-Host "  ✅ $($d.name)" -ForegroundColor Green
                } else {
                    Write-Host "  ❌ $($d.name) - $($d.error)" -ForegroundColor Red
                }
            }

            if ($response.saved_to) {
                Write-Host ""
                Write-Success "Dashboards saved to: $($response.saved_to)"
            }
        }
        catch {
            Write-Error "Failed to build dashboards: $_"
            exit 1
        }
    }

    "build-single" {
        if (-not $Dashboard) {
            Write-Error "Dashboard parameter is required for build-single action"
            Write-Info "Example: -Dashboard 'Revenue Analytics'"
            exit 1
        }

        Write-Header "Building Dashboard: $Dashboard"

        try {
            $encodedName = [System.Web.HttpUtility]::UrlEncode($Dashboard)
            Write-Info "Sending request to Ollama..."
            
            $response = Invoke-RestMethod -Uri "$BaseUrl/build/$encodedName" -Method POST

            Write-Host ""
            if ($response.success) {
                Write-Success "Dashboard built successfully!"
                Write-Host "`nDashboard Details:" -ForegroundColor Cyan
                Write-Host "  Name: $($response.dashboard.name)" -ForegroundColor White
                Write-Host "  Description: $($response.dashboard.description)" -ForegroundColor White
                Write-Host "  Priority: $($response.dashboard.priority)" -ForegroundColor White
                Write-Host "  Code Length: $($response.dashboard.code.Length) characters" -ForegroundColor White
            } else {
                Write-Error "Failed: $($response.error)"
            }
        }
        catch {
            Write-Error "Failed to build dashboard: $_"
            exit 1
        }
    }

    "generated" {
        Write-Header "Generated Dashboard Files"

        try {
            $response = Invoke-RestMethod -Uri "$BaseUrl/generated" -Method GET

            if ($response.dashboards.Count -eq 0) {
                Write-Warning "No generated dashboards found"
                Write-Info "Run: .\build-dashboards.ps1 -Action build-priority -Priority 1"
                exit 0
            }

            Write-Info "Total generated: $($response.dashboards.Count)"
            Write-Host ""

            foreach ($d in $response.dashboards) {
                Write-Host "📊 " -NoNewline -ForegroundColor Cyan
                Write-Host "$($d.name)" -ForegroundColor White
                Write-Host "   File: $($d.file)" -ForegroundColor DarkGray
                Write-Host "   Generated: $($d.generated_at)" -ForegroundColor DarkGray
                Write-Host "   Priority: $($d.priority)" -ForegroundColor DarkGray
                Write-Host ""
            }

            Write-Success "Manifest location: $($response.manifest_path)"
        }
        catch {
            Write-Error "Failed to list generated dashboards: $_"
            exit 1
        }
    }
}

Write-Host ""
