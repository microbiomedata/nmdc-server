#!/bin/sh
set -e
export DOLLAR='$'
export DNS_ADDRESS=$(grep -m 1 ^nameserver /etc/resolv.conf | sed -E -n 's/\D*(\d+\.\d+\.\d+\.\d+)\D*/\1/p')
export NGINX_CLIENT_MAX_BODY_SIZE=${NGINX_CLIENT_MAX_BODY_SIZE:-10m}

envsubst < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

# Build an HTML snippet containing the values of environment variables,
# and inject that snippet into our built app's `index.html` file.
#
# Note: The injected snippet will consist of a `<script>` element containing
#       JavaScript code that inserts an property named `__nmdc_config__` into
#       the global `window` object. That property will be an object containing
#       Sentry configuration parameters. The reason we do it this way is that
#       we don't know the Sentry environment name at app build time or at
#       container image build time — only at container start time/run time.
#
SENTRY_DSN="${SENTRY_DSN:-}"                                   # get from Sentry dashboard
SENTRY_ENVIRONMENT_NAME="${SENTRY_ENVIRONMENT_NAME:-unknown}"  # e.g. "production", "development", "local", "unknown"
SENTRY_TRACES_SAMPLE_RATE="${SENTRY_TRACES_SAMPLE_RATE:-0.0}"  # any number from 0.0 to 1.0
PLACEHOLDER = "<!-- __NMDC_CONFIG_INJECTION_PLACEHOLDER__ -->"
HTML_SNIPPET=$(cat <<'EOF'
    <script>
        window.__nmdc_config__ = {
            sentryDsn: "${SENTRY_DSN}",
            sentryEnvironmentName: "${SENTRY_ENVIRONMENT_NAME}",
            sentryTracesSampleRate: ${SENTRY_TRACES_SAMPLE_RATE}
        };
    </script>
EOF
)
sed -i "s|${PLACEHOLDER}|${HTML_SNIPPET}|g" /www/data/index.html

nginx -g 'daemon off;'
