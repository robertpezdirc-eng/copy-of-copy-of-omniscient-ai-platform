# Omni Agent: Full Build & Deploy

This guide and scripts let an agent (or you) build and deploy all main services to Google Cloud Run, using Cloud Build and basic health checks.

## 1) What the agent understands

Natural-language instruction example the agent can execute:

> Zgradi in deployaj vse komponente iz GitHuba na Google Cloud (Build + Run + Storage). Poveži backend, frontend, modele in dashboarde, preveri zdravje storitev in popravi napake.

Behind the scenes, we provide a config file and a PowerShell orchestration script that runs the exact steps.

## 2) Access required

- GitHub: Personal Access Token (classic) with scopes: `repo`, `workflow` (only if your agent needs to clone/push)
- Google Cloud: Service Account Key (JSON) with roles:
  - roles/run.admin
  - roles/cloudbuild.builds.editor
  - roles/storage.admin
  - roles/iam.serviceAccountUser

Store the key as `gcp-key.json` for the agent or local use.

## 3) Config file

See `agent-config.json`:

```json
{
  "task": "full_build_and_deploy",
  "github_repo": "https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform",
  "cloud_region": "europe-west1",
  "project_id": "refined-graph-471712-n9",
  "services": ["backend", "frontend", "gateway", "ollama"],
  "build": { "use_cloud_build": true, "triggers": "on_push" },
  "deploy": { "platform": "cloud_run", "memory": "4Gi", "cpu": 2, "keep_alive": "5m" },
  "verify": { "check_health_endpoints": true },
  "credentials": { "github_token": "GITHUB_PAT", "gcp_service_account": "gcp-key.json" }
}
```

## 4) Orchestration script

Use `omni-agent-build-deploy.ps1` to build & deploy services end-to-end.

### Parameters
- `-PROJECT_ID` (required) GCP project id
- `-REGION` (default `europe-west1`)
- `-GCP_KEY_FILE` path to service account JSON (optional if already authenticated)
- `-SERVICES` array: any of `backend,frontend,gateway,ollama,ai-worker,backup` (default: all)
- `-SKIP_BUILD` switch to skip building (only deploy)

### Example runs (PowerShell)

```powershell
# Full build & deploy using a service account key
./omni-agent-build-deploy.ps1 -PROJECT_ID "refined-graph-471712-n9" -REGION "europe-west1" -GCP_KEY_FILE ".\gcp-key.json"

# Only deploy backend and gateway
./omni-agent-build-deploy.ps1 -PROJECT_ID "refined-graph-471712-n9" -SERVICES backend,gateway -SKIP_BUILD

# Deploy AI Worker and Backup Service only
./omni-agent-build-deploy.ps1 -PROJECT_ID "refined-graph-471712-n9" -SERVICES ai-worker,backup
```

## 5) What it does
- Ollama: deploys or reuses a Cloud Run service (`ollama`), tests `/api/tags`
- Backend: Cloud Build submit (reduced context via `.gcloudignore`), deploys to `omni-ultra-backend`, tests `/api/health`
- Gateway: deploys `ai-gateway` with `UPSTREAM_URL` pointing to backend
- Frontend: uses `deploy-frontend.ps1`’s Cloud Build pipeline and prints service URL
- AI Worker: deploys `omni-ai-worker` from `ai-worker/` and checks `/health`
- Backup Service: deploys `omni-backup-service` from `backup-service/`, auto-creates `gs://omni-unified-backups-<project>` and checks `/health`

## 6) Health checks
- Backend: `GET /api/health` (200 expected)
- Ollama: `GET /api/tags` (200 expected)
- Gateway: root/health depending on gateway routes (script prints URL)
- Frontend: prints URL (static)

## Notes
- `.gcloudignore` is tuned to keep backend build context small
- If you need persistent Ollama models, redeploy with a Cloud Storage volume mount (requires supported features)
- For BI/WebSocket features, redeploy backend after merging changes to ensure routes are live

