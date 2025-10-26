#!/usr/bin/env bash
# Vertex AI setup helper

# Default model for local setup (can be overridden by env)
export VERTEX_AI_MODEL="gemini-2.5-pro"

# Other helpful vars
export GOOGLE_CLOUD_REGION=${GOOGLE_CLOUD_REGION:-europe-west1}
export GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT:-refined-graph-471712-n9}

echo "VERTEX_AI_MODEL=${VERTEX_AI_MODEL}"
echo "GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}"
echo "GOOGLE_CLOUD_REGION=${GOOGLE_CLOUD_REGION}"