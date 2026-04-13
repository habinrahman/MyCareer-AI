#!/bin/sh
set -eu

APP_HOST="${APP_HOST:?Set APP_HOST in environment}"
API_HOST="${API_HOST:?Set API_HOST in environment}"

if [ -f /etc/letsencrypt/live/mycareer-ai/fullchain.pem ]; then
  TPL=/templates/phase2-https.conf.template
  echo "nginx: TLS certificate found, using HTTPS configuration."
else
  TPL=/templates/phase1-http.conf.template
  echo "nginx: No certificate yet, using HTTP bootstrap (ACME + reverse proxy)."
fi

sed -e "s/__APP_HOST__/${APP_HOST}/g" -e "s/__API_HOST__/${API_HOST}/g" "$TPL" \
  > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
