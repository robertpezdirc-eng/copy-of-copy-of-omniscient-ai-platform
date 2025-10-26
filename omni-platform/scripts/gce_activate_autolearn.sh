#!/usr/bin/env bash
set -euo pipefail

INSTANCE_NAME="${INSTANCE_NAME:-}"
ZONE="${ZONE:-}"
PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-}"
OPENAI_KEY="${OPENAI_KEY:-}"
SERVICE_ACCOUNT_JSON="${SERVICE_ACCOUNT_JSON:-}"

if [[ -z "$INSTANCE_NAME" || -z "$ZONE" || -z "$PROJECT_ID" || -z "$REGION" ]]; then
  echo "Usage: INSTANCE_NAME=... ZONE=... PROJECT_ID=... REGION=... OPENAI_KEY=... SERVICE_ACCOUNT_JSON=... ./scripts/gce_activate_autolearn.sh"
  exit 1
fi

# 0) Check gcloud
command -v gcloud >/dev/null 2>&1 || { echo "gcloud not found"; exit 1; }

# 1) Prepare service unit
TEMPLATE="$(dirname "$0")/../deployment-packages/omni-autolearn.service.tmpl"
[[ -f "$TEMPLATE" ]] || { echo "Template not found: $TEMPLATE"; exit 1; }
TEMP_SERVICE="$(mktemp)"
USER_NAME=$(id -un)
sed "s/{{USER}}/$USER_NAME/g; s/{{OPENAI_API_KEY}}/$OPENAI_KEY/g" "$TEMPLATE" > "$TEMP_SERVICE"

# 2) Copy service account json
if [[ -n "$SERVICE_ACCOUNT_JSON" && -f "$SERVICE_ACCOUNT_JSON" ]]; then
  gcloud compute scp "$SERVICE_ACCOUNT_JSON" "$INSTANCE_NAME:/opt/omni/service-account.json" --zone="$ZONE"
else
  echo "No SERVICE_ACCOUNT_JSON provided or file missing; skipping copy."
fi

# 3) Copy auto-learn files and service unit
gcloud compute scp "$TEMP_SERVICE" "$INSTANCE_NAME:/tmp/omni-autolearn.service" --zone="$ZONE"
gcloud compute scp omni_autolearn_starter.py omni_event_logger.py omni_data_listener.py omni_learning_core.py omni_autolearn_config.json "$INSTANCE_NAME:/opt/omni/" --zone="$ZONE"

# 4) Remote setup
REMOTE_CMDS='set -e; sudo mkdir -p /opt/omni/logs; if [ ! -d "/opt/omni/omni_env" ]; then python3 -m venv /opt/omni/omni_env; fi; /opt/omni/omni_env/bin/pip install --upgrade pip; /opt/omni/omni_env/bin/pip install requests google-cloud-storage; sudo mv /tmp/omni-autolearn.service /etc/systemd/system/omni-autolearn.service; sudo systemctl daemon-reload; sudo systemctl enable omni-autolearn; sudo systemctl restart omni-autolearn'
gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" --command="$REMOTE_CMDS"

# 5) Ensure bucket and list
BUCKET_CMDS="(gsutil ls gs://omni-meta-data || gsutil mb -p $PROJECT_ID -l $REGION gs://omni-meta-data) && gsutil ls gs://omni-meta-data/models/"
gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" --command="$BUCKET_CMDS"

# 6) Status instructions
echo "Auto-learning service deployed. Follow logs:"
echo "gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command='sudo journalctl -u omni-autolearn -f'"
echo "or check: /opt/omni/logs/autolearn.log"