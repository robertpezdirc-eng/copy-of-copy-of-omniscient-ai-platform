param(
  [Parameter(Mandatory=$true)] [string]$ProjectId,
  [Parameter(Mandatory=$true)] [string]$ServiceName,
  [string]$Region = "europe-west1",
  [int]$ErrorsThreshold = 5,
  [int]$P95LatencyMs = 1500,
  [int]$WindowMin = 5,
  [int]$AlignmentSec = 60,
  [string]$NotificationChannelIds = "", # Comma-separated list of channel IDs (e.g., projects/XYZ/notificationChannels/123)
  [string]$ImpersonateServiceAccount = ""  # Optional: service account email to impersonate for gcloud auth and API calls
)

$ErrorActionPreference = "Stop"

Write-Host "Applying Cloud Monitoring alert policies for service '$ServiceName' in project '$ProjectId'..." -ForegroundColor Cyan

# Build JSON array for notification channels
$channelsJson = ""
if ([string]::IsNullOrWhiteSpace($NotificationChannelIds)) {
  $channelsJson = ""
} else {
  $ids = $NotificationChannelIds.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ }
  $quoted = $ids | ForEach-Object { '"' + $_ + '"' }
  $channelsJson = ($quoted -join ', ')
}

# Ensure gcloud project
& gcloud config set project $ProjectId | Out-Null

# Determine available gcloud monitoring command group
$monitoringPrefixArgs = @('monitoring')
& gcloud monitoring --help | Out-Null
if ($LASTEXITCODE -ne 0) {
  $monitoringPrefixArgs = @('alpha','monitoring')
}
Write-Host "Using command group: gcloud $($monitoringPrefixArgs -join ' ')" -ForegroundColor DarkGray

function Invoke-Gcloud {
  param([string[]]$Args)
  $globalArgs = @()
  if ($ImpersonateServiceAccount) { $globalArgs += @('--impersonate-service-account', $ImpersonateServiceAccount) }
  Write-Host ("  > gcloud {0} {1} {2}" -f ($globalArgs -join ' '), ($monitoringPrefixArgs -join ' '), ($Args -join ' ')) -ForegroundColor DarkGray
  & gcloud @globalArgs @monitoringPrefixArgs @Args
  if ($LASTEXITCODE -ne 0) {
    throw ("Command failed ({0}): gcloud {1} {2} {3}" -f $LASTEXITCODE, ($globalArgs -join ' '), ($monitoringPrefixArgs -join ' '), ($Args -join ' '))
  }
}

# REST API fallback helpers
function Get-AccessToken {
  $cmd = @('auth','print-access-token')
  if ($ImpersonateServiceAccount) { $cmd += @('--impersonate-service-account', $ImpersonateServiceAccount) }
  $tok = (& gcloud @cmd).Trim()
  if (-not $tok) { throw "Failed to obtain access token via gcloud auth print-access-token" }
  return $tok
}

function Invoke-MonApi {
  param(
    [ValidateSet('GET','POST','PATCH','DELETE')][string]$Method,
    [string]$Path,
    [string]$BodyJson
  )
  $base = 'https://monitoring.googleapis.com/v3'
  $uri = "$base$Path"
  $hdr = @{ Authorization = "Bearer $(Get-AccessToken)"; 'Content-Type' = 'application/json' }
  Write-Host ("  > REST {0} {1}" -f $Method, $uri) -ForegroundColor DarkGray
  if ($BodyJson -and $Method -ne 'GET') { Write-Host ("    body: {0}" -f ($BodyJson.Substring(0, [Math]::Min($BodyJson.Length, 200)))) -ForegroundColor DarkGray }
  try {
    if ($Method -eq 'GET') {
      return Invoke-RestMethod -Method $Method -Uri $uri -Headers $hdr -ErrorAction Stop
    } elseif ($BodyJson) {
      return Invoke-RestMethod -Method $Method -Uri $uri -Headers $hdr -Body $BodyJson -ErrorAction Stop
    } else {
      return Invoke-RestMethod -Method $Method -Uri $uri -Headers $hdr -ErrorAction Stop
    }
  } catch {
    $we = $_.Exception
    $status = ''
    $body = ''
    if ($we -and $we.Response) {
      try { $status = $we.Response.StatusCode.Value__ } catch {}
      try { $sr = New-Object System.IO.StreamReader($we.Response.GetResponseStream()); $body = $sr.ReadToEnd(); $sr.Close() } catch {}
    }
    Write-Host ("REST error {0}: {1}" -f $status, $body) -ForegroundColor Red
    throw
  }
}

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path "$Root\.." | Select-Object -ExpandProperty Path
$TplDir = Join-Path $RepoRoot "infra\monitoring\policies"
$OutDir = Join-Path $RepoRoot "infra\monitoring\compiled"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function Render-Template {
  param([string]$TemplatePath, [string]$OutPath)
  Write-Host "Rendering template: $TemplatePath" -ForegroundColor DarkGray
  $content = Get-Content -Raw -Path $TemplatePath
  try {
    Write-Host " - Replace SERVICE_NAME" -ForegroundColor DarkGray
    $content = $content.Replace('${SERVICE_NAME}', $ServiceName)
    Write-Host " - Replace PROJECT_ID" -ForegroundColor DarkGray
    $content = $content.Replace('${PROJECT_ID}', $ProjectId)
    Write-Host " - Replace ERRORS_THRESHOLD" -ForegroundColor DarkGray
    $content = $content.Replace('${ERRORS_THRESHOLD}', "$ErrorsThreshold")
    Write-Host " - Replace P95_MS" -ForegroundColor DarkGray
    $content = $content.Replace('${P95_MS}', "$P95LatencyMs")
    Write-Host " - Replace WINDOW_MIN" -ForegroundColor DarkGray
    $content = $content.Replace('${WINDOW_MIN}', "$WindowMin")
    Write-Host " - Replace ALIGNMENT_SEC" -ForegroundColor DarkGray
    $content = $content.Replace('${ALIGNMENT_SEC}', "$AlignmentSec")
    if ($channelsJson) {
      Write-Host " - Replace NOTIFICATION_CHANNELS (provided)" -ForegroundColor DarkGray
      $content = $content.Replace('${NOTIFICATION_CHANNELS}', $channelsJson)
    } else {
      Write-Host " - Replace NOTIFICATION_CHANNELS (empty)" -ForegroundColor DarkGray
      $content = $content.Replace('${NOTIFICATION_CHANNELS}', "")
    }
  } catch {
    Write-Host "Template rendering failed: $_" -ForegroundColor Red
    throw
  }
  Set-Content -Path $OutPath -Value $content -Encoding UTF8
}

$templates = @(
  @{ name = "error-rate"; file = "error-rate.json.tpl" },
  @{ name = "latency-p95"; file = "latency-p95.json.tpl" },
  @{ name = "availability-low-traffic"; file = "availability-low-traffic.json.tpl" }
)

# Capability probe: do we have 'policies' group?
$hasPoliciesCli = $false
try {
  & gcloud @monitoringPrefixArgs 'policies' 'list' '--limit=1' '--format=value(name)' | Out-Null
  if ($LASTEXITCODE -eq 0) { $hasPoliciesCli = $true }
} catch { $hasPoliciesCli = $false }
Write-Host ("Policies CLI available: {0}" -f $hasPoliciesCli) -ForegroundColor DarkGray

foreach ($t in $templates) {
  $src = Join-Path $TplDir $t.file
  $dst = Join-Path $OutDir ($t.name + ".json")
  Render-Template -TemplatePath $src -OutPath $dst
  Write-Host "Rendered: $dst" -ForegroundColor Gray

  if ($hasPoliciesCli) {
    # Create or update using gcloud CLI
    try {
      Invoke-Gcloud -Args @('policies','create',"--policy-from-file=$dst") | Out-Null
      Write-Host "Created policy: $($t.name)" -ForegroundColor Green
    } catch {
      Write-Host "Policy may already exist or create failed; trying update: $($t.name)" -ForegroundColor Yellow
      try {
        $displayName = (Get-Content -Raw -Path $dst | ConvertFrom-Json).displayName
        $filter = ('displayName="{0}"' -f $displayName)
        $policyId = (& gcloud @monitoringPrefixArgs 'policies' 'list' '--format=value(name)' '--filter' $filter)
        if (-not $policyId) { throw "Policy not found by display name: $displayName" }
        Invoke-Gcloud -Args @('policies','update',$policyId,"--policy-from-file=$dst") | Out-Null
        Write-Host "Updated policy: $displayName" -ForegroundColor Green
      } catch {
        Write-Host "Failed to create/update policy $($t.name): $_" -ForegroundColor Red
      }
    }
  } else {
    # REST fallback
    try {
      $jsonObj = Get-Content -Raw -Path $dst | ConvertFrom-Json
      $displayName = $jsonObj.displayName
      # Try to find existing policy by display_name
      $filter = [System.Uri]::EscapeDataString('display_name="' + $displayName + '"')
      $listPath = "/projects/$ProjectId/alertPolicies?filter=$filter"
      $listResp = Invoke-MonApi -Method GET -Path $listPath -BodyJson $null
      $existing = $null
      if ($listResp.alertPolicies) {
        $existing = $listResp.alertPolicies | Select-Object -First 1
      }
      if ($existing) {
        Write-Host "Updating existing policy via REST: $displayName" -ForegroundColor Yellow
        $jsonObj | Add-Member -NotePropertyName name -NotePropertyValue $existing.name -Force
        # Compute update mask for common fields
        $mask = @()
        foreach ($k in @('display_name','documentation','user_labels','conditions','combiner','enabled','notification_channels')) {
          $prop = $k -replace '_([a-z])', { ($args[0].Groups[1].Value).ToUpper() }
          if ($jsonObj.PSObject.Properties.Name -contains $prop) { $mask += $k }
        }
        $updateMask = ($mask -join ',')
        $body = ($jsonObj | ConvertTo-Json -Depth 20)
        $name = $existing.name
        $path = "/$name?updateMask=$([System.Uri]::EscapeDataString($updateMask))"
        $null = Invoke-MonApi -Method PATCH -Path $path -BodyJson $body
        Write-Host "Updated (REST) policy: $displayName" -ForegroundColor Green
      } else {
        Write-Host "Creating new policy via REST: $displayName" -ForegroundColor Yellow
        $body = (Get-Content -Raw -Path $dst)
        $null = Invoke-MonApi -Method POST -Path "/projects/$ProjectId/alertPolicies" -BodyJson $body
        Write-Host "Created (REST) policy: $displayName" -ForegroundColor Green
      }
    } catch {
      Write-Host "REST create/update failed for $($t.name): $_" -ForegroundColor Red
      if ($_.Exception -and $_.Exception.Response -and $_.Exception.Response.StatusCode -eq 403) {
        Write-Host "Hint: Ensure your active account or the impersonated service account has roles/monitoring.editor (or monitoring.admin) on project $ProjectId." -ForegroundColor Yellow
      }
    }
  }
}

Write-Host "Done." -ForegroundColor Cyan