param(
  [string]$ProjectId = $(gcloud config get-value project 2>$null),
  [string]$Region = "us-central1",
  [string]$RunRegion = "europe-west1",
  [string]$ServiceName = "omni-exec-api",
  [string]$Model = "gemini-1.5-flash-latest",
  [string]$HealthPath = "/healthz",
  [string]$LogFile = "vertex_connectivity_check.log",
  [switch]$PromptFix,
  [switch]$AssumeYes
)

function Write-Log {
  param([string]$Message)
  $timestamp = (Get-Date).ToString("s")
  $line = "[$timestamp] $Message"
  Write-Host $line
  Add-Content -Path $LogFile -Value $line
}

# Pre-checks
if (-not $ProjectId) {
  Write-Host "[ERROR] ProjectId ni nastavljen (gcloud config). Nastavi ga z: gcloud config set project <YOUR_PROJECT_ID>" -ForegroundColor Red
  exit 1
}

Write-Log "Projekt: $ProjectId | Region Vertex: $Region | Cloud Run Region: $RunRegion | Service: $ServiceName | Model: $Model"

# 1) Pridobi Service Account za Cloud Run storitev
Write-Log "Pridobivam Service Account za Cloud Run storitev '$ServiceName'..."
$ServiceAccount = ""
try {
  $ServiceAccount = gcloud run services describe $ServiceName --region $RunRegion --format "value(spec.template.spec.serviceAccountName)" 2>$null
} catch {
  Write-Log "Napaka pri opisovanju Cloud Run storitve. Preveri, da storitev obstaja v regiji $RunRegion."
}
if (-not $ServiceAccount) {
  Write-Log "Ni bilo mogoče najti Service Accounta za storitev '$ServiceName'. Nadaljujem, vendar IAM preverjanje bo omejeno."
} else {
  Write-Log "Service Account: $ServiceAccount"
}

# Status spremenljivke
$IamOk = $true
$HealthOk = $false
$GeminiOk = $false

# 2) IAM preverjanje ključnih vlog
if ($ServiceAccount) {
  Write-Log "Preverjam IAM vloge za SA ($ServiceAccount)..."
  $policy = gcloud projects get-iam-policy $ProjectId --format=json | ConvertFrom-Json
  $bindings = $policy.bindings | Where-Object { $_.members -contains "serviceAccount:$ServiceAccount" }
  $rolesNeeded = @(
    "roles/aiplatform.user",
    "roles/aiplatform.serviceAgent",
    "roles/storage.objectViewer",
    "roles/logging.logWriter"
  )
  $missingRoles = @()
  foreach ($r in $rolesNeeded) {
    $hasRole = $bindings | Where-Object { $_.role -eq $r }
    if ($hasRole) {
      Write-Log "OK: SA ima vlogo $r"
    } else {
      Write-Log "MANJKA: SA nima vloge $r"
      $missingRoles += $r
    }
  }
  if ($missingRoles.Count -gt 0) {
    $IamOk = $false
    if ($AssumeYes -or $PromptFix) {
      foreach ($r in $missingRoles) {
        $doFix = $false
        if ($AssumeYes) { $doFix = $true }
        elseif ($PromptFix) {
          $ans = Read-Host "Želiš dodati vlogo '$r' za $ServiceAccount? [y/N]"
          if ($ans -match '^(y|Y)$') { $doFix = $true }
        }
        if ($doFix) {
          Write-Log "Dodajam vlogo $r za $ServiceAccount ..."
          try {
            gcloud projects add-iam-policy-binding $ProjectId --member serviceAccount:$ServiceAccount --role $r | Out-Null
          } catch {
            Write-Log "Napaka pri dodajanju vloge $r: $($_.Exception.Message)"
          }
        } else {
          Write-Log "Preskočeno dodajanje vloge $r."
        }
      }
      # Ponovni pregled
      $policy2 = gcloud projects get-iam-policy $ProjectId --format=json | ConvertFrom-Json
      $bindings2 = $policy2.bindings | Where-Object { $_.members -contains "serviceAccount:$ServiceAccount" }
      $remainingMissing = @()
      foreach ($r in $rolesNeeded) {
        $hasRole2 = $bindings2 | Where-Object { $_.role -eq $r }
        if (-not $hasRole2) { $remainingMissing += $r }
      }
      if ($remainingMissing.Count -eq 0) {
        $IamOk = $true
        Write-Log "IAM popravek uspešen: vse potrebne vloge so prisotne."
      } else {
        $IamOk = $false
        Write-Log ("Še vedno manjkajo vloge: " + ($remainingMissing -join ", "))
      }
    }
  }
}

# 3) Preveri zdravje Cloud Run storitve (GET /healthz)
Write-Log "Preverjam Cloud Run URL za storitev..."
$RunUrl = ""
try {
  $RunUrl = gcloud run services describe $ServiceName --region $RunRegion --format "value(status.url)" 2>$null
} catch {}
if ($RunUrl) {
  $healthUrl = "$RunUrl$HealthPath"
  Write-Log "Kličem $healthUrl ..."
  try {
    $resp = Invoke-WebRequest -Uri $healthUrl -Method GET -TimeoutSec 30
    Write-Log "Health status code: $($resp.StatusCode) | Length: $($resp.Content.Length)"
    if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 300) { $HealthOk = $true }
  } catch {
    Write-Log "Napaka pri health klicu: $($_.Exception.Message)"
    $HealthOk = $false
  }
} else {
  Write-Log "Ni bilo mogoče pridobiti Cloud Run URL-ja za storitev."
}

# 4) Testni klic na Vertex AI / Gemini
$AccessToken = ""
try {
  $AccessToken = gcloud auth print-access-token 2>$null
} catch {}
if (-not $AccessToken) {
  Write-Log "Ni bilo mogoče pridobiti Access Token-a (gcloud). Prijavi se z: gcloud auth login"
  exit 1
}

$Endpoint = "https://$Region-aiplatform.googleapis.com/v1/projects/$ProjectId/locations/$Region/publishers/google/models/$Model:generateContent"
Write-Log "Vertex endpoint: $Endpoint"

# Minimal request body
$Body = @{
  contents = @(
    @{ role = "user"; parts = @(@{ text = "Say hello from connectivity check." }) }
  )
  generationConfig = @{ temperature = 0 }
} | ConvertTo-Json -Depth 6

Write-Log "Pošiljam testni zahtevek na Gemini..."
try {
  $response = Invoke-WebRequest -Uri $Endpoint -Method POST -Headers @{ Authorization = "Bearer $AccessToken"; "Content-Type" = "application/json" } -Body $Body -TimeoutSec 60
  Write-Log "Gemini status code: $($response.StatusCode)"
  if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300) { $GeminiOk = $true }
  # Poskusi izluščiti kratek povzetek
  $json = $response.Content | ConvertFrom-Json
  $text = $json.candidates[0].content.parts[0].text
  if ($text) {
    Write-Log "Gemini odgovor: $text"
  } else {
    Write-Log "Gemini odgovor prejet, vendar brez 'text' polja. Shrani celoten JSON v log."
    Add-Content -Path $LogFile -Value $response.Content
  }
} catch {
  Write-Log "Napaka pri klicu Gemini: $($_.Exception.Message)"
  if ($_.Exception.Response) {
    try {
      $errContent = (New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())).ReadToEnd()
      Write-Log "Gemini error body: $errContent"
    } catch {}
  }
  $GeminiOk = $false
}

# Povzetek in izhodna koda
$exitCode = 0
if (-not $IamOk) { $exitCode = 2 }
if (-not $HealthOk) { $exitCode = 3 }
if (-not $GeminiOk) { $exitCode = 4 }
if ($exitCode -ne 0) {
  Write-Log "Preflight neuspeh: IAM=$IamOk | Health=$HealthOk | Gemini=$GeminiOk"
  exit $exitCode
} else {
  Write-Log "Preflight OK: IAM=$IamOk | Health=$HealthOk | Gemini=$GeminiOk"
}

Write-Log "Končano. Rezultati zapisani v $LogFile"