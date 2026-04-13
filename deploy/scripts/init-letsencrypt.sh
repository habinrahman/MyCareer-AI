#!/usr/bin/env bash
# Obtain (or expand) a Let's Encrypt SAN certificate for APP_HOST + API_HOST.
# Run on the Droplet after DNS points here and: docker compose up -d
#
# Usage: ./deploy/scripts/init-letsencrypt.sh
# Requires: .env at repo root with APP_HOST, API_HOST, LETSENCRYPT_EMAIL

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Missing .env at repo root. Copy .env.example and set APP_HOST, API_HOST, LETSENCRYPT_EMAIL."
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

: "${APP_HOST:?Set APP_HOST in .env}"
: "${API_HOST:?Set API_HOST in .env}"
: "${LETSENCRYPT_EMAIL:?Set LETSENCRYPT_EMAIL in .env}"

echo "==> Ensuring Nginx is up (HTTP bootstrap for ACME)"
docker compose up -d api web nginx

echo "==> Requesting certificate (cert name: mycareer-ai)"
docker compose run --rm --entrypoint certbot certbot certonly \
  --webroot -w /var/www/certbot \
  --cert-name mycareer-ai \
  -d "$APP_HOST" \
  -d "$API_HOST" \
  -m "$LETSENCRYPT_EMAIL" \
  --agree-tos \
  --non-interactive \
  --rsa-key-size 4096

echo "==> Restarting Nginx to pick HTTPS config (entrypoint re-renders templates)"
docker compose restart nginx

echo "Done. Check https://${APP_HOST} and https://${API_HOST}"
