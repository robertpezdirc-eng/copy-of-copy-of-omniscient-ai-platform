param(
  [string[]]$Roots = @("C:\\Users\\admin\\Downloads", "C:\\Users\\admin\\Documents", "C:\\Users\\admin\\Desktop", "E:\\"),
  [string]$DestRoot = "external/local",
  [int]$MaxDepth = 3,
  [int]$MaxFileMB = 5
)

function Write-Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Ok($m){ Write-Host "[OK]   $m" -ForegroundColor Green }
function Write-Err($m){ Write-Host "[ERR]  $m" -ForegroundColor Red }

$ErrorActionPreference = 'SilentlyContinue'
$null = New-Item -ItemType Directory -Path $DestRoot -Force

$patterns = @('omni','OMNIBOT','dashboard','cloudrun','gcp','vertex','firebase','cloud')
$exts = @('.json','.yaml','.yml','.sh','.ps1','.py','.html','.htm','.md','.conf','.txt','.js','.ts','.jsx','.tsx')
$maxBytes = $MaxFileMB * 1MB

foreach($root in $Roots){
  Write-Info "Scanning $root"
  if (-not (Test-Path $root)) { Write-Err "Path not found: $root"; continue }

  $dirs = Get-ChildItem -Path $root -Directory -Recurse -Depth $MaxDepth -ErrorAction SilentlyContinue
  foreach($d in $dirs){
    $match = $false
    foreach($p in $patterns){ if ($d.Name -like "*${p}*") { $match = $true; break } }
    if (-not $match) { continue }

    Write-Info "Matched dir: $($d.FullName)"
    $files = Get-ChildItem -Path $d.FullName -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Extension -in $exts -and $_.Length -le $maxBytes }
    if ($files.Count -eq 0) { continue }

    $rel = $d.FullName.Replace(':','').Replace('\\','__')
    $outDir = Join-Path $DestRoot $rel
    $null = New-Item -ItemType Directory -Path $outDir -Force

    foreach($f in $files){
      try {
        $dest = Join-Path $outDir $f.Name
        Copy-Item -Path $f.FullName -Destination $dest -Force
      } catch { Write-Err "Copy failed: $($f.FullName) -> $dest : $($_.Exception.Message)" }
    }
    Write-Ok "Copied $($files.Count) files to $outDir"
  }
}

Write-Ok "Local artefact collection completed"