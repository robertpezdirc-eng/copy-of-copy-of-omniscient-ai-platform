#!/bin/sh
set -e

# Replace PORT placeholder in nginx config with actual PORT from environment
export PORT=${PORT:-8080}
envsubst '${PORT}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

# Start nginx
exec nginx -g 'daemon off;'
