#!/usr/bin/env bash
set -euo pipefail

# smoke_test.sh
# Reusable Cloud Run uptime smoke test with retries and optional content validation.
# Resolves SERVICE_URL from (priority): --url -> --url-file (cloudrun-url.json) -> gcloud run services describe.
# Supports multiple endpoints, mode all/any, expected status, substring check, jq JSON filter, and diagnostics on failure.
#
# Usage examples:
#   ./smoke_test.sh --url https://your.run.app --paths /health --retries 20 --delay 5
#   ./smoke_test.sh --service omni-dashboard --region europe-west1 --paths /health,/readyz --mode all
#   ./smoke_test.sh --url-file cloudrun-url.json --path /health --expect-status 200 --expect-contains ok
#   ./smoke_test.sh --url-file cloudrun-url.json --path /health --expect-json '.status=="ok" and .version != null'
#
# Requirements:
#   - bash, curl
#   - jq (only if using --expect-json or resolving URL from JSON file)
#   - gcloud (only if resolving URL via service/region or printing diagnostics)

URL=""
URL_FILE="cloudrun-url.json"
SERVICE_NAME=""
REGION=""
# Default single endpoint
PATHS=("/health")
MODE="all"            # all|any
RETRIES=20
DELAY=5               # seconds between retries
TIMEOUT=10            # curl --max-time seconds
EXPECT_STATUS=200
EXPECT_CONTAINS=""    # substring to find in body
EXPECT_JSON_FILTER="" # jq expression that must evaluate to true
VERBOSE=false

usage() {
  cat <<EOF
Reusable Cloud Run uptime smoke test

Options:
  -u, --url <URL>                 Explicit base URL (e.g., https://service-xyz.run.app)
      --url-file <PATH>          JSON file with .url or .status.url (default: cloudrun-url.json)
  -s, --service <NAME>           Cloud Run service name (used if --url not provided)
  -r, --region <REGION>          Cloud Run region
      --paths <CSV>              Comma-separated endpoint paths, e.g. "/health,/readyz"
      --path <PATH>              Repeatable; endpoint path, e.g. --path /health --path /readyz
      --mode <all|any>           all (default) requires every path to pass; any passes if one succeeds
      --retries <N>              Retry attempts (default: 20)
      --delay <SEC>              Delay between attempts (default: 5)
      --timeout <SEC>            Per-request timeout (default: 10)
      --expect-status <CODE>     Expected HTTP status code (default: 200)
      --expect-contains <TEXT>   Require substring in the response body
      --expect-json <JQ>         jq expression that must evaluate to true on response JSON
  -v, --verbose                  Verbose output
  -h, --help                     Show help

Resolution priority for base URL: --url > --url-file > (gcloud run describe with --service/--region)
EOF
}

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    -u|--url) URL="$2"; shift 2;;
    --url-file) URL_FILE="$2"; shift 2;;
    -s|--service) SERVICE_NAME="$2"; shift 2;;
    -r|--region) REGION="$2"; shift 2;;
    --paths) IFS=',' read -r -a PATHS <<< "$2"; shift 2;;
    --path) PATHS+=("$2"); shift 2;;
    --mode) MODE="$2"; shift 2;;
    --retries) RETRIES="${2}"; shift 2;;
    --delay) DELAY="${2}"; shift 2;;
    --timeout) TIMEOUT="${2}"; shift 2;;
    --expect-status) EXPECT_STATUS="${2}"; shift 2;;
    --expect-contains) EXPECT_CONTAINS="${2}"; shift 2;;
    --expect-json) EXPECT_JSON_FILTER="${2}"; shift 2;;
    -v|--verbose) VERBOSE=true; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1;;
  esac
done

# Normalize paths to start with '/'
for i in "${!PATHS[@]}"; do
  p="${PATHS[$i]}"
  if [[ -z "$p" ]]; then continue; fi
  if [[ "${p:0:1}" != "/" ]]; then p="/$p"; fi
  PATHS[$i]="$p"
done

# Resolve URL
resolve_url() {
  local u="$URL"
  if [[ -z "$u" ]] && [[ -f "$URL_FILE" ]]; then
    if command -v jq >/dev/null 2>&1; then
      u=$(jq -r '.url // .status.url // empty' "$URL_FILE" || echo "")
    else
      echo "Warning: jq not found; skipping --url-file resolution" >&2
    fi
  fi
  if [[ -z "$u" ]] && [[ -n "$SERVICE_NAME" && -n "$REGION" ]]; then
    if command -v gcloud >/dev/null 2>&1; then
      u=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format='value(status.url)' || echo "")
    else
      echo "Error: gcloud not found; cannot resolve URL via service/region" >&2
      exit 1
    fi
  fi
  if [[ -z "$u" ]]; then
    echo "Error: Unable to resolve SERVICE_URL. Provide --url or --url-file or --service/--region." >&2
    exit 1
  fi
  URL="$u"
}

resolve_url

$VERBOSE && echo "Base URL: $URL" && echo "Paths: ${PATHS[*]}" && echo "Mode: $MODE, Retries: $RETRIES, Delay: $DELAYs, Timeout: $TIMEOUTs"

# Perform checks
last_body=""
last_code=""

all_paths_pass() {
  local passed_any=false
  local all_pass=true
  for path in "${PATHS[@]}"; do
    local full="${URL%/}${path}"
    $VERBOSE && echo "Requesting: $full"
    # Capture body and HTTP status
    local resp
    set +e
    resp=$(curl -sS --connect-timeout 5 --max-time "$TIMEOUT" "$full" -w "HTTPSTATUS:%{http_code}")
    local rc=$?
    set -e
    if [[ $rc -ne 0 ]]; then
      $VERBOSE && echo "curl failed with code $rc"
      all_pass=false
      continue
    fi
    local body="${resp%HTTPSTATUS:*}"
    local code="${resp##*HTTPSTATUS:}"
    last_body="$body"; last_code="$code"
    $VERBOSE && echo "HTTP $code" && echo "Body (truncated): ${body:0:200}"

    # Status check
    if [[ "$code" != "$EXPECT_STATUS" ]]; then
      all_pass=false
      continue
    fi
    # Contains check
    if [[ -n "$EXPECT_CONTAINS" ]]; then
      if ! grep -qi -- "$EXPECT_CONTAINS" <<<"$body"; then
        all_pass=false
        continue
      fi
    fi
    # JSON filter check
    if [[ -n "$EXPECT_JSON_FILTER" ]]; then
      if ! command -v jq >/dev/null 2>&1; then
        echo "Error: --expect-json requires jq." >&2
        exit 1
      fi
      echo -n "$body" | jq -e "$EXPECT_JSON_FILTER" >/dev/null 2>&1 || { all_pass=false; continue; }
    fi
    passed_any=true
  done
  if [[ "$MODE" == "any" ]]; then
    $passed_any && return 0 || return 1
  else
    $all_pass && return 0 || return 1
  fi
}

success=false
for ((i=1; i<=RETRIES; i++)); do
  echo "Attempt $i/${RETRIES}"
  if all_paths_pass; then
    success=true
    break
  fi
  sleep "$DELAY"
done

if ! $success; then
  echo "Smoke test FAILED." >&2
  echo "Last HTTP status: ${last_code:-<none>}" >&2
  if [[ -n "$last_body" ]]; then
    echo "Last response body (first 1000 chars):" >&2
    echo "${last_body:0:1000}" >&2
  fi
  # Diagnostics: recent error logs from Cloud Run, if service+region known
  if [[ -n "${SERVICE_NAME}" && -n "${REGION}" ]] && command -v gcloud >/dev/null 2>&1; then
    echo "Recent Cloud Run error logs (last 5m):" >&2
    gcloud logging read \
      "resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME} AND resource.labels.location=${REGION} AND severity>=ERROR" \
      --freshness=5m --limit=50 --format='value(textPayload)' || true
  fi
  exit 1
fi

echo "Smoke test PASSED."