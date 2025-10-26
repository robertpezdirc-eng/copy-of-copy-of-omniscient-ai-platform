param(
  [string]$ProjectId = "refined-graph-471712-n9",
  [string]$Region = "europe-west1",
  [string]$Repository = "cloud-run-source-deploy",
  [string]$ImagePath = "omni-dashboard/frontend",
  [string]$Digest = "sha256:d9717656fd7c618476508fe298c8fe4fdfed9830798ee92a202f426e8d139652",
  [string]$DestRoot = "external/docker"
)

function Write-Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Ok($m){ Write-Host "[OK]   $m" -ForegroundColor Green }
function Write-Err($m){ Write-Host "[ERR]  $m" -ForegroundColor Red }

$ErrorActionPreference = 'Stop'

# Ensure destination directories
$destDir = Join-Path -Path $DestRoot -ChildPath "omni-dashboard-frontend"
$null = New-Item -ItemType Directory -Path $destDir -Force

# Save metadata
$metaPath = Join-Path $destDir 'artifact_info.txt'
@(
  "Project: $ProjectId",
  "Region: $Region",
  "Repository: $Repository",
  "Image: $ImagePath",
  "Digest: $Digest"
) | Set-Content -Path $metaPath
Write-Ok "Saved metadata to $metaPath"

# Describe image via gcloud
try {
  $fullRef = "$Region-docker.pkg.dev/$ProjectId/$Repository/$ImagePath@$Digest"
  Write-Info "Describing image: $fullRef"
  $desc = & gcloud artifacts docker images describe $fullRef --format json
  if ($LASTEXITCODE -eq 0 -and $desc) {
    $descPath = Join-Path $destDir 'describe.json'
    $desc | Set-Content -Path $descPath
    Write-Ok "Saved describe.json"
  } else { Write-Err "Describe failed or empty output" }
} catch { Write-Err "Describe error: $($_.Exception.Message)" }

# Configure Docker auth for Artifact Registry
try {
  Write-Info "Configuring Docker auth for $Region-docker.pkg.dev"
  & gcloud auth configure-docker $Region-docker.pkg.dev --quiet | Out-Null
  Write-Ok "Docker auth configured"
} catch { Write-Err "Docker auth failed: $($_.Exception.Message)" }

# Attempt docker pull
$pulled = $false
try {
  $fullRef = "$Region-docker.pkg.dev/$ProjectId/$Repository/$ImagePath@$Digest"
  Write-Info "Pulling image: $fullRef"
  & docker pull $fullRef
  if ($LASTEXITCODE -eq 0) { $pulled = $true; Write-Ok "Image pulled" } else { Write-Err "Docker pull failed ($LASTEXITCODE)" }
} catch { Write-Err "Docker pull error: $($_.Exception.Message)" }

# Save and extract image if pulled
if ($pulled) {
  try {
    $tarPath = Join-Path $destDir 'omni-dashboard-frontend.tar'
    Write-Info "Saving image to $tarPath"
    & docker image save $fullRef -o $tarPath
    if ($LASTEXITCODE -ne 0) { Write-Err "docker image save failed" } else { Write-Ok "Image saved to tar" }

    $extractDir = Join-Path $destDir 'extracted'
    $null = New-Item -ItemType Directory -Path $extractDir -Force
    Write-Info "Extracting layers to $extractDir"
    # PowerShell extraction for tar (Windows may require tar.exe)
    & tar -xf $tarPath -C $extractDir
    if ($LASTEXITCODE -ne 0) { Write-Err "tar extraction failed" } else { Write-Ok "Layers extracted" }

    # Save docker inspect
    Write-Info "Inspecting image config"
    $inspect = & docker inspect $fullRef
    if ($LASTEXITCODE -eq 0 -and $inspect) { $inspect | Set-Content (Join-Path $destDir 'inspect.json'); Write-Ok "Saved inspect.json" }
  } catch { Write-Err "Error saving/extracting image: $($_.Exception.Message)" }
}

Write-Ok "Artifact Registry pull script completed"