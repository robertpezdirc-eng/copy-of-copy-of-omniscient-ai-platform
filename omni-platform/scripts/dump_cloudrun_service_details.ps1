param(
  [Parameter(Mandatory=$true)][string]$ProjectId,
  [Parameter(Mandatory=$true)][string[]]$Regions,
  [Parameter(Mandatory=$false)][string]$DestRoot = "external/cloudrun"
)
$ErrorActionPreference = 'Stop'

function Ensure-Dir($path) {
  if (-not (Test-Path $path)) { New-Item -ItemType Directory -Path $path | Out-Null }
}

Ensure-Dir $DestRoot

foreach ($region in $Regions) {
  Write-Host "Listing services in $ProjectId / $region" -ForegroundColor Cyan
  $listPath = Join-Path $DestRoot "services-$ProjectId-$region.json"
  $servicesJson = & gcloud run services list --platform=managed --project=$ProjectId --region=$region --format=json 2>$null
  if (-not $servicesJson) { Write-Warning "No services output for $region"; continue }
  $servicesJson | Out-File -FilePath $listPath -Encoding utf8
  try { $services = $servicesJson | ConvertFrom-Json } catch { Write-Warning "Failed to parse services json for $region"; continue }

  foreach ($svc in $services) {
    $name = $svc.metadata.name
    $svcDir = Join-Path $DestRoot $name
    Ensure-Dir $svcDir
    $descPath = Join-Path $svcDir "service-$ProjectId-$region.json"
    $desc = & gcloud run services describe $name --platform=managed --project=$ProjectId --region=$region --format=json 2>$null
    if ($desc) { $desc | Out-File -FilePath $descPath -Encoding utf8 }
    $envPath = Join-Path $svcDir "env-$ProjectId-$region.json"
    try {
      $obj = $desc | ConvertFrom-Json
      $env = $obj.spec.template.spec.containers[0].env
      $statusUrl = $obj.status.url
      $envOut = [PSCustomObject]@{ env = $env; statusUrl = $statusUrl; region = $region; project = $ProjectId }
      $envOut | ConvertTo-Json -Depth 6 | Out-File -FilePath $envPath -Encoding utf8
    } catch {
      Write-Warning "Failed to extract env/status for $name in $region"
    }
  }
}