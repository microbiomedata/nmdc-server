set -e
export DOLLAR='$'
export DNS_ADDRESS=$(grep -m 1 ^nameserver /etc/resolv.conf | sed -E -n 's/\D*(\d+\.\d+\.\d+\.\d+)\D*/\1/p')

envsubst < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf
nginx -g 'daemon off;'
