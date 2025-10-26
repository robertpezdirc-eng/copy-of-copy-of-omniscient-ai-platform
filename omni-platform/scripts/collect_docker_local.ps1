param(
  [Parameter(Mandatory=$false)][string]$DestRoot = "external/docker"
)
$ErrorActionPreference = 'SilentlyContinue'

function Ensure-Dir($path) {
  if (-not (Test-Path $path)) { New-Item -ItemType Directory -Path $path | Out-Null }
}

Ensure-Dir $DestRoot
$metaDir = Join-Path $DestRoot 'meta'
$imagesDir = Join-Path $DestRoot 'saved_images'
$containersDir = Join-Path $DestRoot 'exported_containers'
$configDir = Join-Path $DestRoot 'local_config'
$projDir = Join-Path $DestRoot 'project_artifacts'

Ensure-Dir $metaDir; Ensure-Dir $imagesDir; Ensure-Dir $containersDir; Ensure-Dir $configDir; Ensure-Dir $projDir

# Collect docker metadata (graceful on failure)
Write-Host 'Collecting Docker metadata...'
try { & docker version | Out-File -FilePath (Join-Path $metaDir 'docker_version.txt') -Encoding utf8 } catch {}
try { & docker info | Out-File -FilePath (Join-Path $metaDir 'docker_info.txt') -Encoding utf8 } catch {}
try { & docker context ls | Out-File -FilePath (Join-Path $metaDir 'docker_contexts.txt') -Encoding utf8 } catch {}
try { & docker images --digests --no-trunc | Out-File -FilePath (Join-Path $metaDir 'docker_images.txt') -Encoding utf8 } catch {}
try { & docker images --format '{{json .}}' | Out-File -FilePath (Join-Path $metaDir 'docker_images.json') -Encoding utf8 } catch {}
try { & docker ps -a | Out-File -FilePath (Join-Path $metaDir 'docker_ps.txt') -Encoding utf8 } catch {}
try { & docker ps -a --format '{{json .}}' | Out-File -FilePath (Join-Path $metaDir 'docker_ps.json') -Encoding utf8 } catch {}
try { & docker volume ls | Out-File -FilePath (Join-Path $metaDir 'docker_volumes.txt') -Encoding utf8 } catch {}

# Attempt to save images and inspect
Write-Host 'Saving images and inspect (if Docker engine available)...'
$images = @()
try {
  $images = & docker images --format '{{.Repository}}:{{.Tag}}|{{.ID}}|{{.Digest}}'
} catch { $images = @() }
foreach ($line in $images) {
  $parts = $line -split '\|'
  if ($parts.Length -ge 2) {
    $tag = $parts[0]
    $id = $parts[1]
    if ([string]::IsNullOrWhiteSpace($tag) -or $tag -like '*<none>*') { continue }
    $safe = ($tag -replace '[^a-zA-Z0-9_.-]', '_')
    $inspectPath = Join-Path $imagesDir ("$safe.inspect.json")
    $tarPath = Join-Path $imagesDir ("$safe.tar")
    try { & docker inspect $tag | Out-File -FilePath $inspectPath -Encoding utf8 } catch {}
    try { & docker save -o $tarPath $tag } catch {}
  }
}

# Attempt to export containers
Write-Host 'Exporting containers (if Docker engine available)...'
$containers = @()
try { $containers = & docker ps -a --format '{{.ID}}|{{.Names}}' } catch { $containers = @() }
foreach ($c in $containers) {
  $cparts = $c -split '\|'
  if ($cparts.Length -ge 2) {
    $cid = $cparts[0]; $cname = $cparts[1]
    $safeName = ($cname -replace '[^a-zA-Z0-9_.-]', '_')
    $tarC = Join-Path $containersDir ("$safeName-$cid.tar")
    try { & docker export -o $tarC $cid } catch {}
  }
}

# Copy local Docker config if exists
Write-Host 'Copying local Docker config (if exists)...'
$cfg = Join-Path $env:USERPROFILE ".docker\config.json"
if (Test-Path $cfg) { Copy-Item -Path $cfg -Destination (Join-Path $configDir 'config.json') -Force }

# Collect project Dockerfiles and compose manifests
Write-Host 'Collecting project Dockerfiles/compose manifests...'
$workspace = (Get-Location).Path
$dockerFiles = Get-ChildItem -Path $workspace -Recurse -File -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -like 'Dockerfile*' -or $_.Name -like 'docker-compose*.yml' -or $_.Name -like 'docker-compose*.yaml' }
foreach ($df in $dockerFiles) {
  $rel = $df.FullName.Substring($workspace.Length).TrimStart('\')
  $dest = Join-Path $projDir ($rel -replace '[\\/]', '_')
  try { Copy-Item -Path $df.FullName -Destination $dest -Force } catch {}
}

Write-Host 'Done. Outputs in' $DestRoot