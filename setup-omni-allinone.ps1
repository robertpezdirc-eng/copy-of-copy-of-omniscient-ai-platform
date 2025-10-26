# =========================================
# OMNI Platform – All-in-One Setup (robust)
# =========================================

#requires -version 5.1
$ErrorActionPreference = 'Stop'

# --- 1. Nastavi poti ---
$sourceDir  = "C:\Users\admin\Downloads\copy-of-copy-of-omniscient-ai-platform"
$targetDir  = "C:\Users\admin\Downloads\OMNI-Platform"
$backendDir = Join-Path $targetDir 'backend'
$frontendDir= Join-Path $targetDir 'frontend'
$modulesDir = Join-Path $targetDir 'modules'
$scriptsDir = Join-Path $targetDir 'scripts'
$envFile    = Join-Path $targetDir '.env'

function Ensure-Dir([string]$path) {
  if (-not (Test-Path $path -PathType Container)) { New-Item -ItemType Directory -Path $path | Out-Null }
}

Write-Host "Ustvarjam strukturo map..."
Ensure-Dir $targetDir
Ensure-Dir $backendDir
Ensure-Dir $frontendDir
Ensure-Dir (Join-Path $frontendDir 'src')
Ensure-Dir (Join-Path $frontendDir 'public')
Ensure-Dir $modulesDir
Ensure-Dir $scriptsDir

# --- 3. Premakni backend datoteke ---
Write-Host "Premikam backend datoteke..."
Get-ChildItem -Path $sourceDir -Filter *.py -File -ErrorAction SilentlyContinue | ForEach-Object {
  Move-Item $_.FullName -Destination $backendDir -Force -ErrorAction SilentlyContinue
}
if (Test-Path (Join-Path $sourceDir 'requirements.txt')) {
  Move-Item (Join-Path $sourceDir 'requirements.txt') (Join-Path $backendDir 'requirements.txt') -Force -ErrorAction SilentlyContinue
}

# Ustvari minimalni main.py, če manjka
$mainPy = Join-Path $backendDir 'main.py'
if (-not (Test-Path $mainPy)) {
  @"
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Optional: dodaj pot do AI modula, če obstaja
sys.path.append('../modules/omni-brain-maxi-ultra')

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return JSONResponse({"status": "ok"})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
"@ | Out-File -Encoding UTF8 $mainPy
}

# Minimal requirements, če manjka
$reqFile = Join-Path $backendDir 'requirements.txt'
if (-not (Test-Path $reqFile)) {
  @"
fastapi
uvicorn
"@ | Out-File -Encoding UTF8 $reqFile
}

# --- 4. Premakni frontend datoteke ---
Write-Host "Premikam frontend datoteke..."
# Datoteke
foreach ($f in @('package.json','package-lock.json','vite.config.js')) {
  $srcPath = Join-Path $sourceDir $f
  if (Test-Path $srcPath -PathType Leaf) {
    Move-Item $srcPath (Join-Path $frontendDir $f) -Force -ErrorAction SilentlyContinue
  }
}
# Mape src/public (robustno z robocopy)
foreach ($d in @('src','public')) {
  $srcD = Join-Path $sourceDir $d
  $dstD = Join-Path $frontendDir $d
  if (Test-Path $srcD -PathType Container) {
    Ensure-Dir $dstD
    $null = & robocopy $srcD $dstD /E /NFL /NDL /NJH /NJS /NP
    try { Remove-Item $srcD -Recurse -Force -ErrorAction SilentlyContinue } catch {}
  }
}

# --- 5. Premakni AI module ---
Write-Host "Premikam AI module..."
foreach ($mod in @('omni-brain-maxi-ultra')) {
  $modPath = Join-Path $sourceDir $mod
  if (Test-Path $modPath) {
    Move-Item $modPath (Join-Path $modulesDir $mod) -Force -ErrorAction SilentlyContinue
  }
}

# --- 6. Premakni skripte in Docker ---
Write-Host "Premikam skripte in Docker..."
foreach ($item in @('scripts','docker-compose.yml','README.md')) {
  $srcPath = Join-Path $sourceDir $item
  if (Test-Path $srcPath) {
    Move-Item $srcPath (Join-Path $targetDir ([System.IO.Path]::GetFileName($srcPath))) -Force -ErrorAction SilentlyContinue
  }
}

# --- 7. Ustvari virtualno okolje in namesti pakete ---
Write-Host "Ustvarjam virtualno okolje in nameščam Python pakete..."
Set-Location $backendDir
try {
  if (-not (Test-Path (Join-Path $backendDir '.venv'))) { python -m venv .venv }
  $activate = Join-Path $backendDir '.venv\Scripts\Activate.ps1'
  if (Test-Path $activate) { & $activate }
  if (Test-Path $reqFile) {
    pip install --upgrade pip
    pip install -r $reqFile
  }
} catch {
  Write-Warning "Ustvarjanje venv ali namestitev paketov ni uspela: $($_.Exception.Message)"
}

# --- 8. Namesti frontend pakete ---
Write-Host "Namestitev frontend paketov..."
Set-Location $frontendDir
if (Test-Path (Join-Path $frontendDir 'package.json')) {
  try { npm install } catch { Write-Warning "npm install ni uspel: $($_.Exception.Message)" }
} else {
  Write-Warning "package.json ni najden v $frontendDir — preskočim npm install."
}

# --- 9. Ustvari .env datoteko ---
if (-Not (Test-Path $envFile)) {
  Write-Host "Ustvarjam .env datoteko..."
  @"
# API Keys
OPENAI_API_KEY=sk-your_openai_key_here
GEMINI_API_KEY=your_gemini_key_here
GOOGLE_API_KEY=your_google_key_here

# Backend URL
BACKEND_URL=http://localhost:8000
"@ | Out-File -Encoding UTF8 $envFile
} else {
  Write-Host ".env že obstaja, preskočim ustvarjanje."
}

# --- 10. Nastavi frontend config ---
$frontendConfig = Join-Path $frontendDir 'src\config.js'
Write-Host "Nastavljam frontend config za povezavo z backendom..."
Ensure-Dir (Split-Path $frontendConfig -Parent)
@"
export const API_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
"@ | Out-File -Encoding UTF8 $frontendConfig

# --- 11. Zaključek ---
Write-Host "`n==================================="
Write-Host "OMNI Platform je pripravljena!"
Write-Host "Backend: $backendDir"
Write-Host "Frontend: $frontendDir"
Write-Host "Moduli: $modulesDir"
Write-Host ".env in frontend config sta pripravljena."
Write-Host "Zaženi backend: cd $backendDir -> .\\.venv\\Scripts\\Activate.ps1 -> python main.py"
Write-Host "Zaženi frontend: cd $frontendDir -> npm run dev"
Write-Host "==================================="