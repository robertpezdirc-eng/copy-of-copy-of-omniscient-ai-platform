# Omni Platform Demo Launcher - PowerShell Wrapper
# Avtor: Trae AI Assistant
# Datum: $(Get-Date -Format "yyyy-MM-dd")

Write-Host "🎬 Omni Platform Demo Launcher" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Preveri, če tečejo potrebni strežniki
Write-Host "🔍 Preverjam strežnike..." -ForegroundColor Yellow

$servers = @(
    @{Name="Frontend"; Port=5175; URL="http://localhost:5175/"},
    @{Name="Assets"; Port=8009; URL="http://localhost:8009/"},
    @{Name="Backend"; Port=8004; URL="http://localhost:8004/api/health"}
)

$allRunning = $true
foreach ($server in $servers) {
    try {
        $response = Invoke-WebRequest -Uri $server.URL -TimeoutSec 3 -UseBasicParsing
        Write-Host "✅ $($server.Name) strežnik teče na portu $($server.Port)" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ $($server.Name) strežnik NE teče na portu $($server.Port)" -ForegroundColor Red
        $allRunning = $false
    }
}

if (-not $allRunning) {
    Write-Host "⚠️  Nekateri strežniki ne tečejo. Zaženi jih najprej:" -ForegroundColor Yellow
    Write-Host "   Frontend: cd omni-platform\frontend && npm run dev" -ForegroundColor Gray
    Write-Host "   Backend:  cd omni-platform\backend && python -m uvicorn main:app --host 0.0.0.0 --port 8004 --reload" -ForegroundColor Gray
    Write-Host "   Assets:   python -m http.server 8009" -ForegroundColor Gray
    Write-Host ""
    $continue = Read-Host "Želiš vseeno nadaljevati? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        exit 1
    }
}

Write-Host ""
Write-Host "🚀 Zaganjam demo..." -ForegroundColor Green

# Zaženi autoplay demo
try {
    & ".\Start-Autoplay-OBS.bat"
    Write-Host "✅ Demo uspešno zagnan!" -ForegroundColor Green
}
catch {
    Write-Host "❌ Napaka pri zagonu: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "💡 Poskusi ročno: .\Start-Autoplay-OBS.bat" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📋 Koristni URL-ji:" -ForegroundColor Cyan
Write-Host "   Autoplay Demo: http://localhost:8009/omni-platform/docs/overlays/demo_autoplay.html" -ForegroundColor Gray
Write-Host "   Frontend UI:   http://localhost:5175/" -ForegroundColor Gray
Write-Host "   Backend API:   http://localhost:8004/api/health" -ForegroundColor Gray
Write-Host ""
Write-Host "⌨️  OBS Hotkeys:" -ForegroundColor Cyan
Write-Host "   F1-F5: Preklapljanje scen | SPACE: Start | ESC: Stop" -ForegroundColor Gray
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor DarkGray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")