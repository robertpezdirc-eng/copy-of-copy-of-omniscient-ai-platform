# Monitoring Policy Switch Scripts

This folder contains cross-platform scripts to enable/disable Cloud Monitoring alert policies by displayName using a safe, idempotent pattern (describe → edit JSON → update), with support for regex filters, dry-run, and non-interactive mode.

Contents
- enable_policy.sh / disable_policy.sh (Bash)
- Enable-Policy.ps1 / Disable-Policy.ps1 (PowerShell)

Common features
- Filter policies by displayName using regex (default) or exact match (--exact / -Exact)
- Project selection (-p/--project or -ProjectId), or use the default gcloud project
- Dry-run mode to preview matched policies without changes
- Non-interactive mode (-y / -Yes) for CI/CD
- Safe updates via: gcloud alpha monitoring policies describe | modify | gcloud alpha monitoring policies update
- Exclude patterns support to avoid disabling/targeting specific policies (Bash: -x/--exclude repeatable; PowerShell: -ExcludePatterns)

Prerequisites
- gcloud CLI, authenticated and authorized for Monitoring Admin on the target project
- For Bash: jq is required (installed by default in Cloud Shell). For PowerShell scripts, no jq is needed.

Bash usage
Make scripts executable:

```
chmod +x infra/monitoring/scripts/*.sh
```

Show help:
```
./infra/monitoring/scripts/enable_policy.sh --help
./infra/monitoring/scripts/disable_policy.sh --help
```

Examples:
```
# Enable policies matching regex
./infra/monitoring/scripts/enable_policy.sh -p omni-dev-420223 -f "Uptime Check Failed" -y

# Disable a specific policy by exact displayName
./infra/monitoring/scripts/disable_policy.sh -p omni-dev-420223 -f "OMNI Dashboard - Uptime Check (MQL Multi-Region)" --exact -y

# Disable all uptime policies except the MQL version (exclude via -x)
./infra/monitoring/scripts/disable_policy.sh -p omni-dev-420223 -f "^OMNI Dashboard - Uptime Check" -x "OMNI Dashboard - Uptime Check (MQL Multi-Region)" -y

# Dry-run (no changes)
./infra/monitoring/scripts/disable_policy.sh -f "^Cloud Run P95 Latency" -n

# Use default gcloud project
./infra/monitoring/scripts/enable_policy.sh -f "Uptime Check Failed"
```

PowerShell usage
Run from PowerShell (pwsh/Windows PowerShell):
```
./infra/monitoring/scripts/Enable-Policy.ps1 -ProjectId omni-dev-420223 -Filter "OMNI Dashboard - Uptime Check (MQL Multi-Region)" -Exact -Yes
./infra/monitoring/scripts/Disable-Policy.ps1 -ProjectId omni-dev-420223 -Filter "^OMNI Dashboard - Uptime Check" -ExcludePatterns "OMNI Dashboard - Uptime Check (MQL Multi-Region)" -Yes
```

Notes on quoting (PowerShell):
- Prefer double quotes for the -Filter value; embedded quotes are handled by the script when building the gcloud filter.
- If your regex contains special characters, you can also wrap the entire --filter in single quotes when calling gcloud directly, e.g.:
```
gcloud monitoring policies list --filter 'displayName ~ "OMNI Dashboard - Uptime Check" AND NOT displayName ~ "MQL Multi-Region"'
```

One-liner: disable old + keep MQL (Bash)
```
PROJECT_ID="omni-dev-420223"
for PID in $(gcloud monitoring policies list \
  --project="$PROJECT_ID" \
  --filter='displayName ~ "OMNI Dashboard - Uptime Check" AND NOT displayName ~ "MQL Multi-Region"' \\
  --format='value(name)'); do
  echo "Disabling $PID ..."
  gcloud alpha monitoring policies describe "$PID" --project="$PROJECT_ID" --format=json \
    | jq '.enabled=false' \
    | gcloud alpha monitoring policies update --project="$PROJECT_ID" --policy-from-file=-
 done
```

One-liner: disable old + keep MQL (PowerShell)
```
$ProjectId = "omni-dev-420223"
$policyIds = gcloud monitoring policies list `
  --project="$ProjectId" `
  --filter 'displayName ~ "OMNI Dashboard - Uptime Check" AND NOT displayName ~ "MQL Multi-Region"' `
  --format='value(name)'

foreach ($pid in $policyIds) {
  Write-Host "Disabling $pid ..."
  $json = gcloud alpha monitoring policies describe $pid --project="$ProjectId" --format=json | ConvertFrom-Json
  $json.enabled = $false
  $tmp = [System.IO.Path]::GetTempFileName()
  $json | ConvertTo-Json -Depth 100 | Set-Content -Path $tmp -Encoding utf8
  gcloud alpha monitoring policies update --project="$ProjectId" --policy-from-file="$tmp" | Out-Null
}

# Verify
 gcloud monitoring policies list --project="$ProjectId" `
  --filter 'displayName ~ "OMNI Dashboard - Uptime Check"' `
  --format='table(name,displayName,enabled)'
```

Return codes and CI tips
- Both Bash and PowerShell scripts exit 1 when no policies match, which is useful to catch mis-typed filters in CI.
- Use -n/--dry-run or -DryRun to preview effects without making changes.
- Use -y or -Yes to run non-interactively.

Troubleshooting
- Ensure your gcloud account has Monitoring Admin (roles/monitoring.admin) or equivalent permissions.
- Verify the correct project with `gcloud config get-value project` or pass -p/--project / -ProjectId.
- If regex doesn’t match, test it first with:
```
gcloud monitoring policies list --filter 'displayName ~ "<your regex>"' --format='table(name,displayName)'
```

RE2 regex limitations note
- Google Cloud's RE2 engine does not support lookaheads/lookbehinds. Avoid patterns like (?!...) or (?<=...).
- Use the built-in exclude flags instead of negative lookaheads:
  - Bash: add -x/--exclude for each pattern to exclude
  - PowerShell: use -ExcludePatterns @("pattern1","pattern2")

CI/CD Examples

GitHub Actions (Ubuntu, Bash)
Use Workload Identity Federation (recommended) or a Service Account key secret to authenticate, then run the scripts and/or the one-liner to keep the MQL policy enabled while disabling legacy ones.

Example workflow:

```
name: Monitoring Policy Switch
on:
  workflow_dispatch:
  push:
    branches: [ main ]

jobs:
  switch-policies:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write   # for workload identity federation
    steps:
      - uses: actions/checkout@v4

      # Auth (Option A: Workload Identity Federation)
      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}

      # Auth (Option B: SA key; less secure). Uncomment if you use SA key JSON.
      # - uses: google-github-actions/auth@v2
      #   with:
      #     credentials_json: ${{ secrets.GCP_SA_KEY }}

      - uses: google-github-actions/setup-gcloud@v2

      - name: Enable MQL policy and disable legacy policies
        env:
          PROJECT_ID: omni-dev-420223
        run: |
          chmod +x infra/monitoring/scripts/*.sh
          # 1) Ensure MQL policy is enabled (exact name)
          ./infra/monitoring/scripts/enable_policy.sh -p "$PROJECT_ID" -f "OMNI Dashboard - Uptime Check (MQL Multi-Region)" --exact -y

          # 2) Disable all non-MQL uptime policies using the new exclude flag
          ./infra/monitoring/scripts/disable_policy.sh -p "$PROJECT_ID" -f "^OMNI Dashboard - Uptime Check" -x "OMNI Dashboard - Uptime Check (MQL Multi-Region)" -y

      - name: Verify policies
        env:
          PROJECT_ID: omni-dev-420223
        run: |
          gcloud monitoring policies list --project="$PROJECT_ID" \
            --filter='displayName ~ "OMNI Dashboard - Uptime Check"' \
            --format='table(name,displayName,enabled)'
```

GitHub Actions (Windows, PowerShell)
Runs on windows-latest with PowerShell; uses the PowerShell one-liner to disable legacy policies and the script to enable the MQL policy by exact name.

```
name: Monitoring Policy Switch (Windows)
on:
  workflow_dispatch:

jobs:
  switch-policies-win:
    runs-on: windows-latest
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4

      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}

      - uses: google-github-actions/setup-gcloud@v2

      - name: Enable MQL policy (exact)
        shell: pwsh
        env:
          PROJECT_ID: omni-dev-420223
        run: |
          ./infra/monitoring/scripts/Enable-Policy.ps1 -ProjectId $env:PROJECT_ID -Filter "OMNI Dashboard - Uptime Check (MQL Multi-Region)" -Exact -Yes

      - name: Disable legacy policies (PowerShell one-liner)
        shell: pwsh
        env:
          PROJECT_ID: omni-dev-420223
        run: |
          $policyIds = gcloud monitoring policies list `
            --project="$env:PROJECT_ID" `
            --filter 'displayName ~ "OMNI Dashboard - Uptime Check" AND NOT displayName ~ "MQL Multi-Region"' `
            --format='value(name)'
          foreach ($pid in $policyIds) {
            Write-Host "Disabling $pid ..."
            $json = gcloud alpha monitoring policies describe $pid --project="$env:PROJECT_ID" --format=json | ConvertFrom-Json
            $json.enabled = $false
            $tmp = [System.IO.Path]::GetTempFileName()
            $json | ConvertTo-Json -Depth 100 | Set-Content -Path $tmp -Encoding utf8
            gcloud alpha monitoring policies update --project="$env:PROJECT_ID" --policy-from-file="$tmp" | Out-Null
          }

      - name: Verify policies
        shell: pwsh
        env:
          PROJECT_ID: omni-dev-420223
        run: |
          gcloud monitoring policies list --project="$env:PROJECT_ID" `
            --filter 'displayName ~ "OMNI Dashboard - Uptime Check"' `
            --format='table(name,displayName,enabled)'
```

Cloud Build (cloudbuild.yaml)
Uses Cloud SDK image, installs jq, then enables the MQL policy and disables legacy ones. PROJECT_ID env var is provided by Cloud Build automatically.

```
steps:
  - name: gcr.io/google.com/cloudsdktool/cloud-sdk:slim
    entrypoint: bash
    args:
      - -c
      - |
        set -euo pipefail
        apt-get update && apt-get install -y jq
        gcloud config set project "$PROJECT_ID"
        chmod +x infra/monitoring/scripts/*.sh
        # 1) Enable MQL policy by exact name
        ./infra/monitoring/scripts/enable_policy.sh -p "$PROJECT_ID" -f "OMNI Dashboard - Uptime Check (MQL Multi-Region)" --exact -y
        # 2) Disable legacy uptime policies with AND NOT filter
        for PID in $(gcloud monitoring policies list \
          --project="$PROJECT_ID" \
          --filter='displayName ~ "OMNI Dashboard - Uptime Check" AND NOT displayName ~ "MQL Multi-Region"' \
          --format='value(name)'); do
          echo "Disabling $PID ..."
          gcloud alpha monitoring policies describe "$PID" --project="$PROJECT_ID" --format=json \
            | jq '.enabled=false' \
            | gcloud alpha monitoring policies update --project="$PROJECT_ID" --policy-from-file=-
        done
        # Verify
        gcloud monitoring policies list --project="$PROJECT_ID" \
          --filter='displayName ~ "OMNI Dashboard - Uptime Check"' \
          --format='table(name,displayName,enabled)'
```

Notes
- If you use a different displayName for the MQL policy, update the exact name accordingly in the examples.
- Workload Identity Federation is recommended in GitHub Actions for keyless auth; service account keys should be used only if necessary.
- The disable step uses the one-liner with AND NOT to avoid turning off the MQL policy; the Bash/PowerShell scripts currently do not implement a negative match flag.

Uptime Smoke Test
Quick post-deploy smoke test to validate that the service is reachable and returns HTTP 200 on /health. Includes retries and basic diagnostics.

GitHub Actions (Ubuntu, Bash)
```
- name: Uptime Smoke Test (Bash)
  env:
    SERVICE_URL: ${{ vars.SERVICE_URL }}   # optional; set at repo/environment level
    SERVICE_NAME: omni-dashboard           # fallback resolution by service name
    REGION: europe-west1                   # fallback resolution region
  run: |
    set -euo pipefail
    # Resolve URL if not provided explicitly
    if [[ -z "${SERVICE_URL:-}" ]]; then
      if [[ -z "${SERVICE_NAME:-}" || -z "${REGION:-}" ]]; then
        echo "SERVICE_URL not provided and SERVICE_NAME/REGION not set." >&2
        exit 1
      fi
      SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format='value(status.url)')
    fi
    echo "Probing: ${SERVICE_URL}/health"

    success=false
    for i in {1..20}; do
      code=$(curl -sS -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "${SERVICE_URL}/health" || echo 000)
      echo "Attempt $i -> HTTP $code"
      if [[ "$code" == "200" ]]; then
        success=true
        break
      fi
      sleep 5
    done

    if ! $success; then
      echo "Smoke test failed. Fetching quick diagnostics..." >&2
      # Optional: recent error logs from Cloud Run (requires roles/logging.viewer)
      if [[ -n "${SERVICE_NAME:-}" && -n "${REGION:-}" ]]; then
        echo "Recent error logs (last 5m):"
        gcloud logging read \
          "resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME} AND resource.labels.location=${REGION} AND severity>=ERROR" \
          --freshness=5m --limit=50 --format='value(textPayload)' || true
      fi
      exit 1
    fi
    echo "Uptime smoke test passed."
```

GitHub Actions (Windows, PowerShell)
```
- name: Uptime Smoke Test (PowerShell)
  shell: pwsh
  env:
    SERVICE_URL: ${{ vars.SERVICE_URL }}   # optional
    SERVICE_NAME: omni-dashboard           # fallback
    REGION: europe-west1                   # fallback
  run: |
    $ErrorActionPreference = 'Stop'
    if (-not $env:SERVICE_URL) {
      if (-not $env:SERVICE_NAME -or -not $env:REGION) {
        Write-Error "SERVICE_URL not provided and SERVICE_NAME/REGION not set."
      }
      $env:SERVICE_URL = (gcloud run services describe $env:SERVICE_NAME --region $env:REGION --format 'value(status.url)')
    }
    Write-Host "Probing: $($env:SERVICE_URL)/health"

    $ok = $false
    for ($i = 1; $i -le 20; $i++) {
      try {
        $resp = Invoke-WebRequest -Uri "$($env:SERVICE_URL)/health" -Method GET -UseBasicParsing -TimeoutSec 10
        Write-Host "Attempt $i -> HTTP $($resp.StatusCode)"
        if ([int]$resp.StatusCode -eq 200) { $ok = $true; break }
      } catch {
        Write-Host "Attempt $i -> error: $($_.Exception.Message)"
      }
      Start-Sleep -Seconds 5
    }

    if (-not $ok) {
      Write-Host "Smoke test failed. Fetching quick diagnostics..." -ForegroundColor Red
      if ($env:SERVICE_NAME -and $env:REGION) {
        gcloud logging read `
          "resource.type=cloud_run_revision AND resource.labels.service_name=$($env:SERVICE_NAME) AND resource.labels.location=$($env:REGION) AND severity>=ERROR" `
          --freshness=5m --limit=50 --format='value(textPayload)' | Out-Host
      }
      exit 1
    }
    Write-Host "Uptime smoke test passed." -ForegroundColor Green
```

Cloud Build (cloudbuild.yaml)
```
- name: gcr.io/google.com/cloudsdktool/cloud-sdk:slim
  id: Uptime Smoke Test
  entrypoint: bash
  args:
    - -c
    - |
      set -euo pipefail
      apt-get update && apt-get install -y curl
      # Expect SERVICE_URL or SERVICE_NAME/REGION as substitutions or CB variables
      if [[ -z "${SERVICE_URL:-}" ]]; then
        if [[ -z "${SERVICE_NAME:-}" || -z "${REGION:-}" ]]; then
          echo "SERVICE_URL not provided and SERVICE_NAME/REGION not set." >&2
          exit 1
        fi
        SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format='value(status.url)')
      fi
      echo "Probing: ${SERVICE_URL}/health"
      success=false
      for i in {1..20}; do
        code=$(curl -sS -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "${SERVICE_URL}/health" || echo 000)
        echo "Attempt $i -> HTTP $code"
        if [[ "$code" == "200" ]]; then success=true; break; fi
        sleep 5
      done
      if ! $success; then
        echo "Smoke test failed (Cloud Build)." >&2
        exit 1
      fi
      echo "Uptime smoke test passed (Cloud Build)."
```

Notes for smoke tests
- The endpoint /health is assumed; adjust if your service uses /readyz or /.well-known/health.
- Increase attempts or delays if your rollout takes longer to warm up.
- Diagnostics section for GitHub Actions tries to print recent Cloud Run errors; ensure your runner identity has permission to read logs.

Reusable scripts: smoke_test.sh and Smoke-Test.ps1
Two cross-platform scripts are included for DRY reuse across CI/CD pipelines and local checks.

Bash: smoke_test.sh
- Resolves base URL from priority chain: --url > --url-file (cloudrun-url.json) > gcloud run describe (--service/--region)
- Parameters:
  -u|--url, --url-file, -s|--service, -r|--region
  --paths CSV or repeatable --path
  --mode all|any (default all)
  --retries, --delay, --timeout
  --expect-status (default 200)
  --expect-contains <TEXT>
  --expect-json <jq expression>
- Exit code non-zero on failure; prints last HTTP status/body and recent Cloud Run ERROR logs (5m) if service/region known.

Examples (Bash):
```
# Basic
./infra/monitoring/scripts/smoke_test.sh --url-file cloudrun-url.json --path /health
# Multiple endpoints and content check
./infra/monitoring/scripts/smoke_test.sh --service omni-dashboard --region europe-west1 \
  --paths /health,/readyz --mode all --expect-status 200 --expect-contains ok
# JSON validation with jq filter
./infra/monitoring/scripts/smoke_test.sh --url-file cloudrun-url.json --path /health \
  --expect-json '.status=="ok" and .version != null'
```

PowerShell: Smoke-Test.ps1
- Resolves base URL from: -Url > -UrlFile (cloudrun-url.json) > gcloud run describe (-ServiceName/-Region)
- Parameters:
  -Url, -UrlFile, -ServiceName, -Region
  -Paths array, -Mode All|Any
  -Retries, -DelaySec, -TimeoutSec
  -ExpectedStatus (default 200)
  -ExpectContains <TEXT>
  -ExpectJsonPath <dot.path>, -ExpectJsonEquals <value>
- Exit code non-zero on failure; prints last HTTP status/body and recent Cloud Run ERROR logs (5m) if service/region known.

Examples (PowerShell):
```
# Basic
./infra/monitoring/scripts/Smoke-Test.ps1 -UrlFile cloudrun-url.json -Paths /health
# Multiple endpoints and content check
./infra/monitoring/scripts/Smoke-Test.ps1 -ServiceName omni-dashboard -Region europe-west1 `
  -Paths '/health','/readyz' -Mode All -ExpectedStatus 200 -ExpectContains ok
# JSON key/value validation
./infra/monitoring/scripts/Smoke-Test.ps1 -UrlFile cloudrun-url.json -Paths /health -ExpectJsonPath status -ExpectJsonEquals ok
```

Integrating scripts into CI
- Replace the inline smoke test steps in the CI examples above with a call to the corresponding script and pass values via environment variables or matrix inputs.
- For GitHub Actions, consider setting SERVICE_URL as an org/repo/environment variable (vars.SERVICE_URL) for simplicity.

CI/CD examples using reusable scripts

GitHub Actions (Ubuntu, Bash)
Use the reusable scripts for policy switching and the smoke test.

```
name: Monitoring Policy Switch + Smoke Test (Bash)
on:
  workflow_dispatch:

jobs:
  policies-and-smoke:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4

      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}

      - uses: google-github-actions/setup-gcloud@v2

      - name: Enable MQL policy (exact) and disable legacy
        env:
          PROJECT_ID: omni-dev-420223
        run: |
          chmod +x infra/monitoring/scripts/*.sh
          ./infra/monitoring/scripts/enable_policy.sh -p "$PROJECT_ID" -f "OMNI Dashboard - Uptime Check (MQL Multi-Region)" --exact -y
          ./infra/monitoring/scripts/disable_policy.sh -p "$PROJECT_ID" -f "^OMNI Dashboard - Uptime Check" -x "OMNI Dashboard - Uptime Check (MQL Multi-Region)" -y

      - name: Uptime Smoke Test (via script)
        run: |
          sudo apt-get update && sudo apt-get install -y jq curl
          chmod +x infra/monitoring/scripts/smoke_test.sh
          # Option A: Use URL from file if present
          if [ -f cloudrun-url.json ]; then URL_ARG="--url-file cloudrun-url.json"; fi
          # Option B: Fallback to service/region if no file
          ./infra/monitoring/scripts/smoke_test.sh \
            ${URL_ARG:- --service "$SERVICE_NAME" --region "$REGION"} \
            --path /health \
            --retries 20 \
            --delay 5

          # Example: Multiple endpoints + JSON validation (mode=all)
          # ./infra/monitoring/scripts/smoke_test.sh \
          #   ${URL_ARG:- --service "$SERVICE_NAME" --region "$REGION"} \
          #   --paths /health,/readyz \
          #   --mode all \
          #   --expect-status 200 \
          #   --expect-json '.status=="ok" and .version != null'
```

GitHub Actions (Windows, PowerShell)
Use PowerShell variants for Windows runners and the reusable Smoke-Test.ps1.

```
name: Monitoring Policy Switch + Smoke Test (PowerShell)
on:
  workflow_dispatch:

jobs:
  policies-and-smoke-win:
    runs-on: windows-latest
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4

      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}

      - uses: google-github-actions/setup-gcloud@v2

      - name: Enable MQL policy (exact) and disable legacy (PowerShell)
        shell: pwsh
        env:
          PROJECT_ID: omni-dev-420223
        run: |
          ./infra/monitoring/scripts/Enable-Policy.ps1 -ProjectId $env:PROJECT_ID -Filter "OMNI Dashboard - Uptime Check (MQL Multi-Region)" -Exact -Yes
          ./infra/monitoring/scripts/Disable-Policy.ps1 -ProjectId $env:PROJECT_ID -Filter "^OMNI Dashboard - Uptime Check" -ExcludePatterns "OMNI Dashboard - Uptime Check (MQL Multi-Region)" -Yes

      - name: Uptime Smoke Test (PowerShell script)
        shell: pwsh
        run: |
          ./infra/monitoring/scripts/Smoke-Test.ps1 -UrlFile cloudrun-url.json -Paths /health -Retries 20 -DelaySec 5
```

Cloud Build (cloudbuild.yaml)
Invoke the reusable Bash scripts from Cloud Build steps.

```
steps:
  - name: gcr.io/google.com/cloudsdktool/cloud-sdk:slim
    id: Switch Policies
    entrypoint: bash
    args:
      - -c
      - |
        set -euo pipefail
        apt-get update && apt-get install -y jq curl
        chmod +x infra/monitoring/scripts/*.sh
        # Enable MQL and disable legacy
        ./infra/monitoring/scripts/enable_policy.sh -p "$PROJECT_ID" -f "OMNI Dashboard - Uptime Check (MQL Multi-Region)" --exact -y
        ./infra/monitoring/scripts/disable_policy.sh -p "$PROJECT_ID" -f "^OMNI Dashboard - Uptime Check" -x "OMNI Dashboard - Uptime Check (MQL Multi-Region)" -y

  - name: gcr.io/google.com/cloudsdktool/cloud-sdk:slim
    id: Uptime Smoke Test
    entrypoint: bash
    args:
      - -c
      - |
        set -euo pipefail
        chmod +x infra/monitoring/scripts/smoke_test.sh
        ./infra/monitoring/scripts/smoke_test.sh \
          --url-file cloudrun-url.json \
          --path /health \
          --retries 20 \
          --delay 5
```

Future extensions
- Add explicit --by-id mode to target exact policy name resource IDs.
- Add bulk confirmation details (e.g., print diff of the change) before apply.