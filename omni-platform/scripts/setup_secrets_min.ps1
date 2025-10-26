param(
  [string]$ProjectId = "refined-graph-471712-n9",
  [string]$Region    = "europe-west1",
  [string]$RuntimeSa = "omni-dashboard-runtime",
  [string]$GoogleApiKey = $env:GOOGLE_API_KEY,
  [string]$OpenAiKey   = $env:OPENAI_API_KEY,
  [string]$OmniApiKey  = $env:OMNI_API_KEY,
  [string]$SecretKey   = $null,
  [string]$SlackWebhook= $null,
  [string]$SmtpUser    = $null,
  [string]$SmtpPass    = $null
)

Write-Host "== Minimal Secret Manager Setup =="

# If local file exists, prefer it for OpenAI key
if (Test-Path "openai key.txt") {
  try { $OpenAiKey = Get-Content -Raw "openai key.txt" } catch {}
}

function Ensure-Secret($Name) {
  try { gcloud secrets describe $Name 2>$null | Out-Null } catch { gcloud secrets create $Name --replication-policy="automatic" | Out-Null }
}
function Add-Version($Name, $Value) {
  if ([string]::IsNullOrWhiteSpace($Value)) { return }
  $tmp = [System.IO.Path]::GetTempFileName(); [System.IO.File]::WriteAllText($tmp, $Value)
  gcloud secrets versions add $Name --data-file=$tmp | Out-Null
  Remove-Item $tmp -Force
}

$RuntimeSaEmail = "$RuntimeSa@$ProjectId.iam.gserviceaccount.com"

gcloud config set project $ProjectId | Out-Null

$names = @(
  @{n='omni-dashboard-GOOGLE_API_KEY'; v=$GoogleApiKey},
  @{n='omni-dashboard-OPENAI_API_KEY'; v=$OpenAiKey},
  @{n='omni-dashboard-OMNI_API_KEY';   v=$OmniApiKey},
  @{n='omni-dashboard-SECRET_KEY';     v=$SecretKey},
  @{n='omni-dashboard-SLACK_WEBHOOK_URL'; v=$SlackWebhook},
  @{n='omni-dashboard-SMTP_USERNAME';  v=$SmtpUser},
  @{n='omni-dashboard-SMTP_PASSWORD';  v=$SmtpPass}
)

foreach ($s in $names) { Ensure-Secret $s.n; Add-Version $s.n $s.v }

# Ensure runtime SA and grant secret access
try { gcloud iam service-accounts describe $RuntimeSaEmail 2>$null | Out-Null } catch { gcloud iam service-accounts create $RuntimeSa --display-name "OMNI Dashboard Runtime" | Out-Null }

gcloud projects add-iam-policy-binding $ProjectId `
  --member "serviceAccount:$RuntimeSaEmail" --role "roles/secretmanager.secretAccessor" | Out-Null

Write-Host "Done. Runtime SA: $RuntimeSaEmail"