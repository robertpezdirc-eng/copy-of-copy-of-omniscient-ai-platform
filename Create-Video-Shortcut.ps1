# Ustvari namizno bližnjico za kompletno video avtomatizacijo

$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$([Environment]::GetFolderPath('Desktop'))\Omni Video Automation.lnk")

$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PWD\Create-Complete-Video.ps1`""
$Shortcut.WorkingDirectory = $PWD.Path
$Shortcut.Description = "Omni Platform - Kompletna Video Avtomatizacija (1-klik)"
$Shortcut.IconLocation = "shell32.dll,21"

$Shortcut.Save()

Write-Host "Namizna bližnjica ustvarjena: Omni Video Automation" -ForegroundColor Green
Write-Host "Lokacija: $([Environment]::GetFolderPath('Desktop'))" -ForegroundColor Cyan