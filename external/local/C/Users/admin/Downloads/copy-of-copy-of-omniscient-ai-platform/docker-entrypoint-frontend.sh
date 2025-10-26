#!/bin/sh
set -e

HTML_DIR="/usr/share/nginx/html"
TEMPLATE="$HTML_DIR/env.template.js"
TARGET="$HTML_DIR/env.js"

# Defaults for local/dev
: "${OMNI_API_BASE:=http://localhost:8082}"

# Generate env.js from template
if [ -f "$TEMPLATE" ]; then
  sed "s#__OMNI_API_BASE__#${OMNI_API_BASE}#g" "$TEMPLATE" > "$TARGET"
else
  echo "window.OMNI_API_BASE=\"${OMNI_API_BASE}\";" > "$TARGET"
fi

# Start Nginx
exec nginx -g 'daemon off;'