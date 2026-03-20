#!/bin/sh
set -e
export DOLLAR='$'
export DNS_ADDRESS=$(grep -m 1 ^nameserver /etc/resolv.conf | sed -E -n 's/\D*(\d+\.\d+\.\d+\.\d+)\D*/\1/p')
export NGINX_CLIENT_MAX_BODY_SIZE=${NGINX_CLIENT_MAX_BODY_SIZE:-10m}

envsubst < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

# Inject run-time configuration into the built index.html by replacing the placeholder comment
# with a <script> tag that sets a global JS variable. This allows the frontend to read
# environment-specific settings (e.g. Sentry DSN) that are not known at build time.
#
# Note: SENTRY_DSN is expected to be a URL (e.g. "https://key@host/project-id") and
# SENTRY_ENVIRONMENT_NAME is expected to be a simple identifier (e.g. "production").
# SENTRY_TRACES_SAMPLE_RATE is expected to be a number between 0.0 and 1.0.
# Both values are operator-supplied via environment variables and are never user-supplied.
SENTRY_DSN="${SENTRY_DSN:-}"
SENTRY_ENVIRONMENT_NAME="${SENTRY_ENVIRONMENT_NAME:-unknown}"
SENTRY_TRACES_SAMPLE_RATE="${SENTRY_TRACES_SAMPLE_RATE:-1.0}"
INDEX_HTML="/www/data/index.html"
sed -i "s|<!-- __NMDC_CONFIG_INJECTION_PLACEHOLDER__ -->|<script>window.__nmdc_config__ = { sentryDsn: \"${SENTRY_DSN}\", sentryEnvironmentName: \"${SENTRY_ENVIRONMENT_NAME}\", sentryTracesSampleRate: ${SENTRY_TRACES_SAMPLE_RATE} };</script>|g" "${INDEX_HTML}"

nginx -g 'daemon off;'
