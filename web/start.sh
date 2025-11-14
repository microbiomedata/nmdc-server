#!/bin/sh
set -e
export DOLLAR='$'
export DNS_ADDRESS=$(grep -m 1 ^nameserver /etc/resolv.conf | sed -E -n 's/\D*(\d+\.\d+\.\d+\.\d+)\D*/\1/p')
export NGINX_CLIENT_MAX_BODY_SIZE=${NGINX_CLIENT_MAX_BODY_SIZE:-10m}

envsubst < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf
nginx -g 'daemon off;'
