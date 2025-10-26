param(
  [string]$ProjectId = "refined-graph-471712-n9",
  [string]$ProjectNumber = "661612368188",
  [string[]]$OwnerRepos = @("robertpezdirc/omniscient-ai-platform"),
  [string]$PoolId = "github",
  [string]$ProviderId = "github",
  [string]$ServiceAccountEmail = "ci-deployer@refined-graph-471712-n9.iam.gserviceaccount.com",
  [string]$FirebaseProjectId = "omni-platform-244c6"
)

Write-Host "Configuring Workload Identity Federation (OIDC) for repos: $($OwnerRepos -join ', ') in project $ProjectId ($ProjectNumber)" -ForegroundColor Cyan

# 1) Create Workload Identity Pool (idempotent)
Write-Host "Creating Workload Identity Pool '$PoolId' (if not exists)..."
$poolExists = $(gcloud iam workload-identity-pools describe $PoolId --location=global --project=$ProjectId --format="value(name)" 2>$null)
if (-not $poolExists) {
  gcloud iam workload-identity-pools create $PoolId `
    --location=global `
    --project=$ProjectId `
    --display-name="GitHub Pool"
} else {
  Write-Host "Pool already exists: $poolExists"
}

# 2) Create OIDC Provider (idempotent)
Write-Host "Creating OIDC Provider '$ProviderId' (if not exists)..."
$providerExists = $(
  gcloud iam workload-identity-pools providers describe $ProviderId `
  --location=global `
  --project=$ProjectId `
  --workload-identity-pool=$PoolId `
  --format="value(name)" 2>$null
)
if (-not $providerExists) {
  gcloud iam workload-identity-pools providers create-oidc $ProviderId `
    --project=$ProjectId `
    --location=global `
    --workload-identity-pool=$PoolId `
    --display-name="GitHub Provider" `
    --issuer-uri="https://token.actions.githubusercontent.com" `
    --attribute-mapping='google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.workflow=assertion.workflow'
} else {
  Write-Host "Provider already exists: $providerExists"
}

# 3) Create CI deploy Service Account (idempotent)
Write-Host "Ensuring service account exists: $ServiceAccountEmail"
$saName = $ServiceAccountEmail.Split("@")[0]
$saExists = $(gcloud iam service-accounts describe $ServiceAccountEmail --project=$ProjectId --format="value(email)" 2>$null)
if (-not $saExists) {
  gcloud iam service-accounts create $saName `
    --project=$ProjectId `
    --display-name="CI/CD Deployer for Firebase Hosting"
} else {
  Write-Host "Service account already exists: $saExists"
}

# 4) Grant minimum roles to the deploy SA on source (OIDC) project
Write-Host "Granting roles on source project $ProjectId to $ServiceAccountEmail"
gcloud projects add-iam-policy-binding $ProjectId `
  --member="serviceAccount:$ServiceAccountEmail" `
  --role="roles/serviceusage.serviceUsageConsumer"

# 4b) Grant roles on Firebase Hosting project (target deploy project)
if ($FirebaseProjectId) {
  Write-Host "Granting roles on Firebase project $FirebaseProjectId to $ServiceAccountEmail"
  gcloud projects add-iam-policy-binding $FirebaseProjectId `
    --member="serviceAccount:$ServiceAccountEmail" `
    --role="roles/firebase.admin"

  gcloud projects add-iam-policy-binding $FirebaseProjectId `
    --member="serviceAccount:$ServiceAccountEmail" `
    --role="roles/storage.admin"

  gcloud projects add-iam-policy-binding $FirebaseProjectId `
    --member="serviceAccount:$ServiceAccountEmail" `
    --role="roles/serviceusage.serviceUsageConsumer"
}

# 5) Allow GitHub repos to impersonate the SA via WIF
foreach ($repo in $OwnerRepos) {
  Write-Host "Binding WorkloadIdentityUser for repo $repo"
  gcloud iam service-accounts add-iam-policy-binding $ServiceAccountEmail `
    --project=$ProjectId `
    --role="roles/iam.workloadIdentityUser" `
    --member="principalSet://iam.googleapis.com/projects/$ProjectNumber/locations/global/workloadIdentityPools/$PoolId/attribute.repository/$repo"
}

Write-Host "Completed WIF setup for repos: $($OwnerRepos -join ', ')" -ForegroundColor Green