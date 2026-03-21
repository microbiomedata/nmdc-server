#!/bin/sh
set -e
export DOLLAR='$'
export DNS_ADDRESS=$(grep -m 1 ^nameserver /etc/resolv.conf | sed -E -n 's/\D*(\d+\.\d+\.\d+\.\d+)\D*/\1/p')
export NGINX_CLIENT_MAX_BODY_SIZE=${NGINX_CLIENT_MAX_BODY_SIZE:-10m}

echo 'Generating nginx configuration file'
envsubst < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

# Build an HTML snippet containing the values of environment variables,
# and inject that snippet into our built app's `index.html` file.
#
# Note: The injected snippet will consist of a `<script>` element containing
#       JavaScript code that inserts a property named `__nmdc_config__` into
#       the global `window` object. That property will be an object containing
#       Sentry configuration parameters. The reason we do it this way is that
#       we don't know the Sentry environment name at app build time or at
#       container image build time — only at container start time/run time.
#
# Note: The reason we don't use a plain `sed 's/old/new/' file` command to
#       inject the snippet is that that command would risk sed interpreting
#       characters in the replacement string as sed control characters. So,
#       we use a different approach, one which involves a temporary file.
#
echo 'Injecting NMDC config snippet into HTML file'
SENTRY_DSN="${SENTRY_DSN:-}"                                   # get from Sentry dashboard
SENTRY_ENVIRONMENT_NAME="${SENTRY_ENVIRONMENT_NAME:-unknown}"  # e.g. "production", "development", "local", "unknown"
SENTRY_TRACES_SAMPLE_RATE="${SENTRY_TRACES_SAMPLE_RATE:-0.0}"  # any number from 0.0 to 1.0
cat > /tmp/__nmdc_config__.html.snippet <<EOF
    <script>
        window.__nmdc_config__ = {
            sentryDsn: "${SENTRY_DSN}",
            sentryEnvironmentName: "${SENTRY_ENVIRONMENT_NAME}",
            sentryTracesSampleRate: ${SENTRY_TRACES_SAMPLE_RATE}
        };
    </script>
EOF
sed -i \
    -e '/<!-- __NMDC_CONFIG_INJECTION_PLACEHOLDER__ -->/r /tmp/__nmdc_config__.html.snippet' \
    -e '/<!-- __NMDC_CONFIG_INJECTION_PLACEHOLDER__ -->/d' \
    /www/data/index.html

echo 'Launching nginx in the foreground'
nginx -g 'daemon off;'
