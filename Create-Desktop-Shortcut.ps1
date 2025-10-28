# Ustvari bližnjico na namizju za Omni Platform Demo
# Avtor: Trae AI Assistant

$currentDir = Get-Location
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "🎬 Omni Platform Demo.lnk"

# Ustvari WScript.Shell objekt
$WScriptShell = New-Object -ComObject WScript.Shell

# Ustvari bližnjico
$shortcut = $WScriptShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$currentDir\Launch-Omni-Demo.ps1`""
$shortcut.WorkingDirectory = $currentDir
$shortcut.Description = "Omni Platform Demo Launcher - 1-Click Recording"
$shortcut.IconLocation = "shell32.dll,21"  # Video camera icon
$shortcut.WindowStyle = 1  # Normal window

# Shrani bližnjico
$shortcut.Save()

Write-Host "✅ Bližnjica ustvarjena na namizju: '🎬 Omni Platform Demo'" -ForegroundColor Green
Write-Host "🎯 Lokacija: $shortcutPath" -ForegroundColor Gray
Write-Host ""
Write-Host "💡 Uporaba:" -ForegroundColor Cyan
Write-Host "   1. Dvoklikni bližnjico na namizju" -ForegroundColor Gray
Write-Host "   2. Preveri strežnike" -ForegroundColor Gray
Write-Host "   3. Avtomatski zagon demo + OBS" -ForegroundColor Gray
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor DarkGray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")