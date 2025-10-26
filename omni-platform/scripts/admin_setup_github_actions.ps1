param(
  [string]$ProjectId = "refined-graph-471712-n9",
  [string]$Region    = "europe-west1",
  [string]$SaName    = "github-actions-deployer",
  [string]$Service   = "omni-dashboard"
)

Write-Host "== Google Cloud Admin Setup for GitHub Actions → Cloud Run =="

# Set project
gcloud config set project $ProjectId

Write-Host "Enabling required APIs..."
gcloud services enable `
  run.googleapis.com `
  iam.googleapis.com `
  containerregistry.googleapis.com `
  aiplatform.googleapis.com `
  generativelanguage.googleapis.com

$SaEmail = "$SaName@$ProjectId.iam.gserviceaccount.com"
Write-Host "Creating service account: $SaEmail (if not exists)"
gcloud iam service-accounts create $SaName `
  --display-name "GitHub Actions Deployer" 2>$null

Write-Host "Granting roles to $SaEmail..."
gcloud projects add-iam-policy-binding $ProjectId `
  --member "serviceAccount:$SaEmail" --role "roles/run.admin"
gcloud projects add-iam-policy-binding $ProjectId `
  --member "serviceAccount:$SaEmail" --role "roles/iam.serviceAccountUser"
gcloud projects add-iam-policy-binding $ProjectId `
  --member "serviceAccount:$SaEmail" --role "roles/storage.admin"
gcloud projects add-iam-policy-binding $ProjectId `
  --member "serviceAccount:$SaEmail" --role "roles/aiplatform.user"

$KeyFile = "sa-key.json"
Write-Host "Creating service account key: $KeyFile"
gcloud iam service-accounts keys create $KeyFile `
  --iam-account $SaEmail

Write-Host "If service exists, fetching Cloud Run URL..."
$ServiceUrl = ""
try {
  $ServiceUrl = gcloud run services describe $Service --region $Region --format "value(status.url)"
} catch {}

Write-Host "== NEXT STEPS =="
Write-Host "1) In your GitHub repo, add Secrets:"
Write-Host "   - GCP_SA_KEY: contents of $KeyFile"
Write-Host "   - GCP_PROJECT_ID: $ProjectId"
Write-Host "   - GCP_REGION: $Region"
Write-Host "   - CLOUD_RUN_SERVICE: $Service"
Write-Host "   - GOOGLE_API_KEY: (optional, for AI Studio REST)"
Write-Host "   - OPENAI_API_KEY: (optional)"
Write-Host "2) Commit .github/workflows/deploy-cloudrun-dashboard.yml to main."
Write-Host "3) Push to main and watch GitHub → Actions → Deploy Dashboard."
Write-Host "Cloud Run URL: $ServiceUrl"