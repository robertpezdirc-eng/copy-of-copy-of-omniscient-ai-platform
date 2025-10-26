#!/usr/bin/env bash
set -euo pipefail

# enable_policy.sh
# Enable one or more Cloud Monitoring alert policies by displayName (exact or regex).
# Usage:
#   ./enable_policy.sh -p <PROJECT_ID> -f "<displayName regex>" [--exact] [-n] [-y]
# Examples:
#   ./enable_policy.sh -p omni-dev-420223 -f "Uptime Check Failed"               # regex match
#   ./enable_policy.sh -p omni-dev-420223 -f "Uptime Check Failed - mycheck (host)" --exact
#   ./enable_policy.sh -p omni-dev-420223 -f "^Cloud Run P95 Latency" -y          # auto-confirm
#   ./enable_policy.sh -f "Uptime Check Failed"                                   # use default gcloud project

PROJECT_ID=""
FILTER=""
EXACT=false
DRY_RUN=false
ASSUME_YES=false

usage() {
  echo "Enable Cloud Monitoring alert policies by displayName (regex or exact)."
  echo "\nOptions:"
  echo "  -p, --project <ID>     GCP project ID (defaults to gcloud config if omitted)"
  echo "  -f, --filter  <TEXT>   displayName regex or exact string (use --exact for exact match)"
  echo "      --exact            treat filter as exact displayName"
  echo "  -n, --dry-run          show which policies would be enabled, do not modify"
  echo "  -y                    auto-confirm (no interactive prompt)"
  echo "  -h, --help             show this help"
}

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project)
      PROJECT_ID="$2"; shift 2;;
    -f|--filter)
      FILTER="$2"; shift 2;;
    --exact)
      EXACT=true; shift;;
    -n|--dry-run)
      DRY_RUN=true; shift;;
    -y)
      ASSUME_YES=true; shift;;
    -h|--help)
      usage; exit 0;;
    *)
      echo "Unknown arg: $1" >&2; usage; exit 1;;
  esac
done

if [[ -z "${FILTER}" ]]; then
  echo "Error: --filter <TEXT> is required" >&2
  usage
  exit 1
fi

# Determine project if not provided
if [[ -z "${PROJECT_ID}" ]]; then
  PROJECT_ID=$(gcloud config get-value project 2>/dev/null || true)
  if [[ -z "${PROJECT_ID}" ]]; then
    echo "Error: no project specified and no default configured (gcloud config set project <ID>)." >&2
    exit 1
  fi
fi

# Build gcloud filter
if $EXACT; then
  GCLOUD_FILTER="displayName=\"${FILTER}\""
else
  GCLOUD_FILTER="displayName ~ \"${FILTER}\""
fi

echo "Project: ${PROJECT_ID}"
if $EXACT; then echo "Filter (exact): ${FILTER}"; else echo "Filter (regex): ${FILTER}"; fi

mapfile -t POLICY_IDS < <(gcloud monitoring policies list \
  --project="${PROJECT_ID}" \
  --filter="${GCLOUD_FILTER}" \
  --format='value(name)')

if [[ ${#POLICY_IDS[@]} -eq 0 ]]; then
  echo "No policies matched filter." >&2
  exit 1
fi

echo "Matched policies:" 
for pid in "${POLICY_IDS[@]}"; do
  gcloud monitoring policies describe "$pid" --project="${PROJECT_ID}" --format='table(name,displayName,enabled)'
done

if $DRY_RUN; then
  echo "Dry-run: would enable ${#POLICY_IDS[@]} policy(ies)."
  exit 0
fi

if ! $ASSUME_YES; then
  read -r -p "Enable ${#POLICY_IDS[@]} policy(ies)? [y/N] " ans
  case "$ans" in
    [Yy]*) ;; 
    *) echo "Aborted."; exit 0;;
  esac
fi

TMP_JSON=$(mktemp)
TMP_UPDATED=$(mktemp)
trap 'rm -f "$TMP_JSON" "$TMP_UPDATED"' EXIT

for pid in "${POLICY_IDS[@]}"; do
  echo "Enabling $pid ..."
  gcloud alpha monitoring policies describe "$pid" --project="${PROJECT_ID}" --format=json > "$TMP_JSON"
  jq '.enabled=true' "$TMP_JSON" > "$TMP_UPDATED"
  gcloud alpha monitoring policies update --project="${PROJECT_ID}" --policy-from-file="$TMP_UPDATED" >/dev/null
  gcloud monitoring policies describe "$pid" --project="${PROJECT_ID}" --format='value(name,enabled)'
done

echo "Done."