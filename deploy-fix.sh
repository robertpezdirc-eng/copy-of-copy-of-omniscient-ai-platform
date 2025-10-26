#!/usr/bin/env bash
set -euo pipefail

# Production Deploy Fix Pack
# - Poenoti regije
# - (Opcijsko) Migrira na Artifact Registry
# - Nastavi min-instances in concurrency
# - Preklopi na Secret Manager
# - Preveri health endpoint
# - (Opcijsko) Domain mapping

PROJECT_ID="${PROJECT_ID:-refined-graph-471712-n9}"
REGION="${REGION:-europe-west1}"
AR_REPO="${AR_REPO:-omni}"
AR_HOST="${REGION}-docker.pkg.dev"

info() { echo "[INFO] $*"; }
warn() { echo "[WARN] $*"; }
run()  { echo "> $*"; eval "$*"; }

info "Uporabljam PROJECT_ID=${PROJECT_ID}, REGION=${REGION}"

# 1) Poenoti regijo
info "Poenotenje regije za Cloud Run"
run "gcloud config set run/region ${REGION}"

# Ni globalne config lastnosti za Cloud Build lokacijo; uporabljaj --region v ukazih.
warn "Za Cloud Build uporabi --region ${REGION} v ukazih in triggerjih."

# 2) Artifact Registry (opcijsko)
info "Konfiguracija Artifact Registry Docker avtentikacije"
run "gcloud auth configure-docker ${AR_HOST} --quiet"

info "Ustvarjanje AR repozitorija, če ne obstaja"
if ! gcloud artifacts repositories describe "${AR_REPO}" --location="${REGION}" >/dev/null 2>&1; then
  run "gcloud artifacts repositories create ${AR_REPO} --repository-format=docker --location=${REGION} --description=\"Omni platform images\""
else
  info "AR repozitorij ${AR_REPO} že obstaja v ${REGION}"
fi

# 3) Cloud Build YAML (če obstaja)
if [[ -f cloudbuild.missing-services.yaml ]]; then
  info "Posodobitev image URL-jev v cloudbuild.missing-services.yaml (GCR -> AR)"
  run "sed -i.bak 's#gcr.io/${PROJECT_ID}#${AR_HOST}/${PROJECT_ID}/${AR_REPO}#g' cloudbuild.missing-services.yaml"
  info "Backup: cloudbuild.missing-services.yaml.bak"
else
  warn "Datoteka cloudbuild.missing-services.yaml ne obstaja. Preskakujem zamenjavo GCR referenc."
fi

# 4) Min instances in concurrency (ne bo uspešno, če storitve še ne obstajajo)
update_run() {
  local svc="$1"; shift
  if gcloud run services describe "$svc" --region "$REGION" >/dev/null 2>&1; then
    info "Posodobitev storitve $svc: $*"
    run "gcloud run services update $svc $* --region ${REGION}"
  else
    warn "Storitev $svc ni najdena v ${REGION}. Preskakujem posodobitev."
  fi
}

update_run omni-api-gateway "--min-instances 1 --concurrency 80"
update_run omni-singularity "--min-instances 1 --concurrency 40"

# 5) Secret Manager (primer za OPENAI_API_KEY)
info "Ustvarjanje OPENAI_API_KEY v Secret Manager (če še ne obstaja)"
if ! gcloud secrets describe OPENAI_API_KEY >/dev/null 2>&1; then
  if [[ -n "${OPENAI_API_KEY:-}" ]]; then
    info "Ustvarjanje skrivnosti iz okoljske spremenljivke OPENAI_API_KEY"
    printf "%s" "$OPENAI_API_KEY" | gcloud secrets create OPENAI_API_KEY --data-file=- --replication-policy=automatic
  else
    warn "OPENAI_API_KEY ni podan. Preskakujem ustvarjanje. Uporabi: printf 'VALUE' | gcloud secrets create ..."
  fi
else
  info "Skrivnost OPENAI_API_KEY že obstaja"
fi

# Povezava skrivnosti na storitev (primer omni-api)
if gcloud run services describe omni-api --region "$REGION" >/dev/null 2>&1; then
  info "Povezava skrivnosti OPENAI_API_KEY na omni-api"
  run "gcloud run services update omni-api --set-secrets OPENAI_API_KEY=projects/${PROJECT_ID}/secrets/OPENAI_API_KEY:latest --region ${REGION}"
else
  warn "Storitev omni-api ni najdena v ${REGION}. Preskakujem --set-secrets."
fi

# 6) Health endpoint preverba
HEALTH_URL="https://omni-api-gateway-guzjyv6gfa-ew.a.run.app/healthz"
info "Preverjam health endpoint: ${HEALTH_URL}"
if curl -s -o /dev/null -w "%{http_code}" "${HEALTH_URL}" | grep -q "^200$"; then
  info "Health endpoint vrne 200 OK"
else
  warn "Health endpoint ne vrne 200. Dodaj handler v FastAPI/Express: GET /healthz -> {status: 'ok'}"
fi

# 7) Domain mapping (opcijsko)
info "Domain mapping je opcijski. Primer ukaza:"
echo "gcloud run domain-mappings create --region ${REGION} --service omni-api-gateway --domain api.omni-platform.ai --certificate-mode managed"

info "Končano. Uporabi --region ${REGION} za Cloud Build: gcloud builds submit --config cloudbuild.missing-services.yaml --region ${REGION} --project ${PROJECT_ID}"