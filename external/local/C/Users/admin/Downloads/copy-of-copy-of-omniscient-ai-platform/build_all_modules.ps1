# PowerShell script for automated sequential building of all Omni modules

# Activate virtual environment
$venv = "C:\Users\admin\Downloads\copy-of-copy-of-omniscient-ai-platform\OMNIBOT13\.venv\Scripts\Activate.ps1"
if (Test-Path $venv) {
    . $venv
    Write-Host "Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "Virtual environment not found at $venv" -ForegroundColor Red
    exit 1
}

# Path to state file
$stateFile = "omni_build_state.json"

# Initialize state if it doesn't exist
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

# Load current state
$state = Get-Content $stateFile | ConvertFrom-Json
$modules = $state.modules

Write-Host "Starting sequential build of all Omni modules..." -ForegroundColor Cyan
Write-Host "=" * 60

# Build each module sequentially
foreach ($module in $modules) {
    $moduleName = $module.name
    $moduleStatus = $module.status

    if ($moduleStatus -ne "built") {
        Write-Host "Building module: $moduleName" -ForegroundColor Yellow
        Write-Host "-" * 40

        # Run build command for specific module
        $buildCommand = "python build_module.py --module $moduleName"

        try {
            # Execute build
            $buildResult = Invoke-Expression $buildCommand 2>&1

            if ($LASTEXITCODE -eq 0) {
                Write-Host "SUCCESS: $moduleName built successfully" -ForegroundColor Green

                # Update module status
                $module.status = "built"
                $module.age = 0
                $module.last_build = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

                # Save updated state
                $state.modules = $modules
                $state | ConvertTo-Json -Depth 3 | Set-Content $stateFile

            } else {
                Write-Host "FAILED: $moduleName build failed" -ForegroundColor Red
                Write-Host "Error details: $buildResult" -ForegroundColor Red
                Write-Host "Continuing with next module..." -ForegroundColor Yellow
            }

        } catch {
            Write-Host "ERROR: Exception during $moduleName build" -ForegroundColor Red
            Write-Host $_.Exception.Message -ForegroundColor Red
            Write-Host "Continuing with next module..." -ForegroundColor Yellow
        }

    } else {
        Write-Host "SKIPPING: Module $moduleName already built (last build: $($module.last_build))" -ForegroundColor Blue
    }

    Write-Host ""
}

# Final status check
$builtCount = ($modules | Where-Object { $_.status -eq "built" }).Count
$totalCount = $modules.Count

Write-Host "BUILD COMPLETION SUMMARY:" -ForegroundColor Cyan
Write-Host "=" * 60
Write-Host "Total modules: $totalCount" -ForegroundColor White
Write-Host "Successfully built: $builtCount" -ForegroundColor Green
Write-Host "Build completion rate: $(($builtCount / $totalCount) * 100)%" -ForegroundColor White

if ($builtCount -eq $totalCount) {
    Write-Host "All modules built successfully! ✅" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Test platform: python omni_build_runner.py" -ForegroundColor White
    Write-Host "2. Launch desktop app: .\deployment-packages\omni-desktop-v1.0.0\win-unpacked\OMNI AI Dashboard.exe" -ForegroundColor White
    Write-Host "3. Check status: python omni_build_monitor.py" -ForegroundColor White
} else {
    Write-Host "Some modules failed to build. Check errors above." -ForegroundColor Red
}

Write-Host ""
Write-Host "Build state saved to: $stateFile" -ForegroundColor Blue