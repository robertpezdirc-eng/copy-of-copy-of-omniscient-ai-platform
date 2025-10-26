#!/bin/sh
# Generate env.js from OMNI_API_BASE or use default backend URL
API_BASE=${OMNI_API_BASE:-https://omni-platform-guzjyv6gfa-uw.a.run.app}
echo "window.OMNI_API_BASE = \"$API_BASE\";" > /usr/share/nginx/html/env.js

# Start nginx (listens on 8080 via nginx-react.conf)
exec nginx -g 'daemon off;'