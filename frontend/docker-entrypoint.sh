#!/bin/sh
set -e

# Default backend URL if not set
export BACKEND_URL=${BACKEND_URL:-"http://backend-service.claims-demo.svc.cluster.local:8000"}

echo "Using backend URL: $BACKEND_URL"

# Replace environment variables in nginx config
envsubst '${BACKEND_URL}' < /tmp/nginx.conf.template > /tmp/nginx.conf

# Start nginx
exec nginx -c /tmp/nginx.conf -g "daemon off;"
