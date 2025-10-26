# Build distribution package for UltimateOmniPackage
$ErrorActionPreference = "Stop"
$root = (Resolve-Path "..").Path
$distRoot = Join-Path $root "deployment-packages"
if (!(Test-Path $distRoot)) { New-Item -ItemType Directory -Path $distRoot | Out-Null }

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$distName = "UltimateOmniPackage_$timestamp"
$distPath = Join-Path $distRoot $distName
New-Item -ItemType Directory -Path $distPath | Out-Null

# Apply branding before packaging
python "$root\UltimateOmniPackage\automation\apply_branding.py"

# Include web, docs, and config
Copy-Item -Recurse -Force "$root\UltimateOmniPackage\web" "$distPath\web"
Copy-Item -Recurse -Force "$root\UltimateOmniPackage\docs" "$distPath\docs"
Copy-Item -Recurse -Force "$root\UltimateOmniPackage\config" "$distPath\config"

# Optional: include code skeletons
Copy-Item -Recurse -Force "$root\UltimateOmniPackage\code" "$distPath\code"

# Create ZIP
$zipFile = Join-Path $distRoot "$distName.zip"
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($distPath, $zipFile)
Write-Host "Distribution package created -> $zipFile"