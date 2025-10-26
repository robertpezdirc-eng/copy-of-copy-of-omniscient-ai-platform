# PowerShell script for parallel building of all Omni modules
# Requires PowerShell 7+ for ForEach-Object -Parallel

param(
    [int]$ThrottleLimit = 3
)

# Activate virtual environment
$venv = "C:\Users\admin\Downloads\copy-of-copy-of-omniscient-ai-platform\OMNIBOT13\.venv\Scripts\Activate.ps1"
if (Test-Path $venv) {
    . $venv
    Write-Host "Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "Virtual environment not found at $venv" -ForegroundColor Red
    exit 1
}

$stateFile = "omni_build_state.json"

if (-Not (Test-Path $stateFile)) {
    Write-Host "Initializing build state..." -ForegroundColor Yellow

    $modules = @(
        @{name="omni-platform-v1.0.0"; status="pending"; age=0; last_build=$null},
        @{name="omni-desktop-v1.0.0"; status="pending"; age=0; last_build=$null},
        @{name="omni-frontend-v1.0.0"; status="pending"; age=0; last_build=$null}
    )
    $modules | ConvertTo-Json -Depth 3 | Set-Content $stateFile
    Write-Host "Build state initialized" -ForegroundColor Green
}

$state = Get-Content $stateFile | ConvertFrom-Json

Write-Host "OMNI Platform - Parallel Build" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan
Write-Host "Starting parallel build of all Omni modules..." -ForegroundColor White

# Function to build a module
function Build-Module {
    param($module)

    $moduleName = $module.name
    $moduleStatus = $module.status

    if ($moduleStatus -ne "built") {
        Write-Host "Building module: $moduleName..." -ForegroundColor Yellow

        try {
            $buildCommand = "python build_module.py --module `"$moduleName`""
            $buildResult = Invoke-Expression $buildCommand 2>&1

            if ($LASTEXITCODE -eq 0) {
                Write-Host "SUCCESS: $moduleName built successfully" -ForegroundColor Green
                $module.status = "built"
                $module.age = 0
                $module.last_build = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.ffffff"
            } else {
                Write-Host "FAILED: $moduleName build failed" -ForegroundColor Red
                Write-Host "Error details: $buildResult" -ForegroundColor Red
                $module.status = "failed"
                $module.last_build = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.ffffff"
            }
        }
        catch {
            Write-Host "ERROR: Exception during $moduleName build" -ForegroundColor Red
            Write-Host $_.Exception.Message -ForegroundColor Red
            $module.status = "error"
            $module.last_build = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.ffffff"
        }
    } else {
        Write-Host "Module $moduleName already built, skipping..." -ForegroundColor Blue
    }

    return $module
}

# Use Start-Process for parallel processing (PowerShell 5.1 compatible)
$processes = @()
$moduleResults = @{}

foreach ($module in $state.modules) {
    $moduleName = $module.name
    $moduleStatus = $module.status

    if ($moduleStatus -ne "built") {
        Write-Host "Starting build process for module: $moduleName..." -ForegroundColor Yellow

        # Create a temporary script for this module
        $tempScript = @"
        `$moduleName = "$moduleName"
        Write-Host "Building module: `$moduleName..." -ForegroundColor Yellow

        try {
            `$buildCommand = "python build_module.py --module `"$moduleName`""
            `$buildResult = Invoke-Expression `$buildCommand 2>&1

            if (`$LASTEXITCODE -eq 0) {
                Write-Host "SUCCESS: `$moduleName built successfully" -ForegroundColor Green
                `$result = @{name=`$moduleName; status="built"; age=0; last_build=(Get-Date -Format "yyyy-MM-ddTHH:mm:ss.ffffff")}
            } else {
                Write-Host "FAILED: `$moduleName build failed" -ForegroundColor Red
                `$result = @{name=`$moduleName; status="failed"; age=0; last_build=(Get-Date -Format "yyyy-MM-ddTHH:mm:ss.ffffff")}
            }
        }
        catch {
            Write-Host "ERROR: Exception during `$moduleName build" -ForegroundColor Red
            `$result = @{name=`$moduleName; status="error"; age=0; last_build=(Get-Date -Format "yyyy-MM-ddTHH:mm:ss.ffffff")}
        }

        `$result | ConvertTo-Json -Depth 3 | Set-Content "temp_result_`$moduleName.json"
"@

        $tempScriptPath = "temp_build_$moduleName.ps1"
        $tempScript | Set-Content $tempScriptPath

        # Start process in background
        $process = Start-Process powershell -ArgumentList "-File `"$tempScriptPath`"" -PassThru -WindowStyle Hidden
        $processes += $process
        $moduleResults[$moduleName] = $module
    } else {
        Write-Host "Module $moduleName already built, skipping..." -ForegroundColor Blue
        $moduleResults[$moduleName] = $module
    }
}

# Wait for all processes to complete
Write-Host "Waiting for all parallel builds to complete..." -ForegroundColor Cyan

foreach ($process in $processes) {
    $process | Wait-Process
}

# Collect results from temporary files
foreach ($module in $state.modules) {
    $moduleName = $module.name
    $tempFile = "temp_result_$moduleName.json"

    if (Test-Path $tempFile) {
        $result = Get-Content $tempFile | ConvertFrom-Json
        $moduleResults[$moduleName] = $result
        Remove-Item $tempFile -ErrorAction SilentlyContinue
    }

    # Clean up temporary script
    $tempScript = "temp_build_$moduleName.ps1"
    Remove-Item $tempScript -ErrorAction SilentlyContinue
}

# Update state
$state.modules = $moduleResults.Values
$state.last_updated = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.ffffff"
$state | ConvertTo-Json -Depth 3 | Set-Content $stateFile

# Final status check
$builtCount = ($updatedModules | Where-Object { $_.status -eq "built" }).Count
$totalCount = $updatedModules.Count
$failedCount = ($updatedModules | Where-Object { $_.status -eq "failed" }).Count
$errorCount = ($updatedModules | Where-Object { $_.status -eq "error" }).Count

Write-Host ""
Write-Host "PARALLEL BUILD COMPLETION SUMMARY:" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Total modules: $totalCount" -ForegroundColor White
Write-Host "Successfully built: $builtCount" -ForegroundColor Green
Write-Host "Failed: $failedCount" -ForegroundColor Red
Write-Host "Errors: $errorCount" -ForegroundColor Red
if ($totalCount -gt 0) {
    Write-Host "Build completion rate: $(($builtCount / $totalCount) * 100)%" -ForegroundColor White
} else {
    Write-Host "Build completion rate: 0%" -ForegroundColor White
}

if ($failedCount -eq 0 -and $errorCount -eq 0) {
    Write-Host "All modules built successfully in parallel!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Test platform: python omni_build_runner.py" -ForegroundColor White
    Write-Host "2. Launch desktop app: .\deployment-packages\omni-desktop-v1.0.0\win-unpacked\OMNI AI Dashboard.exe" -ForegroundColor White
    Write-Host "3. Check status: python omni_build_monitor.py" -ForegroundColor White
} else {
    Write-Host "Some modules failed to build. Check errors above." -ForegroundColor Red
    Write-Host ""
    Write-Host "Failed modules:" -ForegroundColor Red
    $updatedModules | Where-Object { $_.status -ne "built" } | ForEach-Object {
        Write-Host "  - $($_.name): $($_.status)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Build state saved to: $stateFile" -ForegroundColor Blue