# PowerShell verzija (build_auto.ps1)
# Aktiviraj virtualno okolje
$venvPath = ".\OMNIBOT13\.venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    . $venvPath
    Write-Host "Virtualno okolje aktivirano" -ForegroundColor Green
} else {
    Write-Host "Virtualno okolje ne najdem na $venvPath" -ForegroundColor Red
    Write-Host "Poskusam nadaljevati brez aktivacije..." -ForegroundColor Yellow
}

# Naloži stanje gradnje
$stateFile = ".\omni_build_state.json"
if (-Not (Test-Path $stateFile)) {
    Write-Host "Stanje gradnje ne obstaja, ustvarjam novo..." -ForegroundColor Yellow
    $state = @{
        modules = @()
        last_updated = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.ffffff"
    } | ConvertTo-Json -Depth 3
    $state | Set-Content $stateFile -Encoding UTF8
    Write-Host "Novo stanje gradnje ustvarjeno" -ForegroundColor Green
}

# Preberi stanje
try {
    $state = Get-Content $stateFile -Encoding UTF8 | ConvertFrom-Json
} catch {
    Write-Host "Napaka pri branju stanja, ustvarjam novo..." -ForegroundColor Yellow
    $state = @{
        modules = @()
        last_updated = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.ffffff"
    }
}

Write-Host "OMNI Advanced Build System - Automated Build Script" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Funkcija za gradnjo modula
function Build-Module($moduleName) {
    Write-Host "🔨 Gradim modul: $moduleName" -ForegroundColor Cyan
    Write-Host "-" * 40 -ForegroundColor DarkCyan

    $startTime = Get-Date

    try {
        # Preveri če je modul že zgrajen
        $existingModule = $state.modules | Where-Object { $_.name -eq $moduleName }

        if ($existingModule -and $existingModule.status -eq "built") {
            Write-Host "⏭️ Modul $moduleName že zgrajen (nazadnje: $($existingModule.last_build)), preskočim..." -ForegroundColor Blue
            return $true
        }

        Write-Host "🏗️ Začenjam gradnjo modula $moduleName..." -ForegroundColor Yellow

        # Izvedi gradnjo
        $buildCommand = "python build_module.py --module `"$moduleName`""
        $buildOutput = Invoke-Expression $buildCommand 2>&1

        if ($LASTEXITCODE -eq 0) {
            $endTime = Get-Date
            $buildDuration = $endTime - $startTime

            Write-Host "✅ Modul $moduleName zgrajen uspešno!" -ForegroundColor Green
            Write-Host "⏱️ Čas gradnje: $($buildDuration.TotalSeconds)s" -ForegroundColor Green

            # Posodobi stanje
            $moduleInfo = @{
                name = $moduleName
                status = "built"
                last_build = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.ffffff"
                build_time_seconds = $buildDuration.TotalSeconds
                build_output = $buildOutput
            }

            # Odstrani star vnos če obstaja
            $state.modules = $state.modules | Where-Object { $_.name -ne $moduleName }

            # Dodaj nov vnos
            $state.modules += $moduleInfo
            $state.last_updated = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.ffffff"

            $state | ConvertTo-Json -Depth 3 | Set-Content $stateFile -Encoding UTF8

            return $true
        } else {
            $endTime = Get-Date
            $buildDuration = $endTime - $startTime

            Write-Host "❌ Modul $moduleName ni bil zgrajen!" -ForegroundColor Red
            Write-Host "⏱️ Čas poskusa: $($buildDuration.TotalSeconds)s" -ForegroundColor Red
            Write-Host "📄 Izhod:" -ForegroundColor Red
            Write-Host $buildOutput -ForegroundColor Red

            # Posodobi stanje z napako
            $moduleInfo = @{
                name = $moduleName
                status = "failed"
                last_build = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.ffffff"
                build_time_seconds = $buildDuration.TotalSeconds
                error_message = $buildOutput
            }

            # Odstrani star vnos če obstaja
            $state.modules = $state.modules | Where-Object { $_.name -ne $moduleName }

            # Dodaj nov vnos
            $state.modules += $moduleInfo
            $state.last_updated = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.ffffff"

            $state | ConvertTo-Json -Depth 3 | Set-Content $stateFile -Encoding UTF8

            return $false
        }

    } catch {
        $endTime = Get-Date
        $buildDuration = $endTime - $startTime

        Write-Host "💥 Izjema pri gradnji modula $moduleName" -ForegroundColor Red
        Write-Host "⏱️ Čas poskusa: $($buildDuration.TotalSeconds)s" -ForegroundColor Red
        Write-Host "❗ Napaka: $($_.Exception.Message)" -ForegroundColor Red

        # Posodobi stanje z izjemo
        $moduleInfo = @{
            name = $moduleName
            status = "error"
            last_build = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.ffffff"
            build_time_seconds = $buildDuration.TotalSeconds
            error_message = $_.Exception.Message
        }

        # Odstrani star vnos če obstaja
        $state.modules = $state.modules | Where-Object { $_.name -ne $moduleName }

        # Dodaj nov vnos
        $state.modules += $moduleInfo
        $state.last_updated = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.ffffff"

        $state | ConvertTo-Json -Depth 3 | Set-Content $stateFile -Encoding UTF8

        return $false
    }
}

# Vsi razpoložljivi moduli
$allModules = @(
    "omni-platform-v1.0.0",
    "omni-desktop-v1.0.0",
    "omni-frontend-v1.0.0"
)

Write-Host "📋 Razpoložljivi moduli za gradnjo:" -ForegroundColor White
for ($i = 0; $i -lt $allModules.Count; $i++) {
    $module = $allModules[$i]
    $existingModule = $state.modules | Where-Object { $_.name -eq $module }

    if ($existingModule) {
        $status = $existingModule.status
        $lastBuild = $existingModule.last_build
        Write-Host "  $($i+1). $module - $status (nazadnje: $lastBuild)" -ForegroundColor Blue
    } else {
        Write-Host "  $($i+1). $module - ni zgrajen" -ForegroundColor Yellow
    }
}

# Poišči module, ki še niso zgrajeni ali so spodleteli
$modulesToBuild = @()
foreach ($module in $allModules) {
    $existingModule = $state.modules | Where-Object { $_.name -eq $module }

    if (-not $existingModule -or $existingModule.status -ne "built") {
        $modulesToBuild += $module
    }
}

Write-Host ""
Write-Host "🚀 Začenjam gradnjo modulov..." -ForegroundColor Magenta
Write-Host "=" * 60 -ForegroundColor Magenta

$successfulBuilds = 0
$failedBuilds = 0
$totalBuildTime = 0

# Gradnja vseh neizgrajenih modulov
foreach ($module in $modulesToBuild) {
    Write-Host ""
    $buildSuccess = Build-Module $module

    if ($buildSuccess) {
        $successfulBuilds++
    } else {
        $failedBuilds++
    }
}

# Končno poročilo
Write-Host ""
Write-Host "📊 KONČNO POROČILO GRADNJE" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "✅ Uspešno zgrajenih modulov: $successfulBuilds" -ForegroundColor Green
Write-Host "❌ Spodletelih modulov: $failedBuilds" -ForegroundColor Red
Write-Host "📈 Uspešnost: $(($successfulBuilds / $allModules.Count) * 100)%" -ForegroundColor White

if ($failedBuilds -eq 0) {
    Write-Host ""
    Write-Host "🎉 VSE GRADNJE USPŠEŠNE! 🎉" -ForegroundColor Green
    Write-Host ""
    Write-Host "Naslednji koraki:" -ForegroundColor Cyan
    Write-Host "1. Test platforme: python omni_build_runner.py" -ForegroundColor White
    Write-Host "2. Zaženi desktop app: .\deployment-packages\omni-desktop-v1.0.0\win-unpacked\OMNI AI Dashboard.exe" -ForegroundColor White
    Write-Host "3. Preveri status: python omni_build_monitor.py" -ForegroundColor White
    Write-Host "4. Napredna analitika: python omni_real_time_build_analytics.py" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "⚠️ Nekatere gradnje so spodletle. Preveri napake zgoraj." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Za pomoč:" -ForegroundColor Cyan
    Write-Host "1. Preveri detajle napak" -ForegroundColor White
    Write-Host "2. Poskusi ročno gradnjo: python build_module.py --module <module_name>" -ForegroundColor White
    Write-Host "3. Aktiviraj samozdravljenje: python omni_self_healing_build_system.py" -ForegroundColor White
}

Write-Host ""
Write-Host "💾 Stanje gradnje shranjeno v: $stateFile" -ForegroundColor Blue
Write-Host "🔄 Za nadaljevanje gradnje samo poženite ta skript ponovno" -ForegroundColor Blue

# Shrani končno stanje
$state.last_updated = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.ffffff"
$state | ConvertTo-Json -Depth 3 | Set-Content $stateFile -Encoding UTF8

Write-Host ""
Write-Host "✅ Avtomatizirana gradnja dokončana!" -ForegroundColor Green