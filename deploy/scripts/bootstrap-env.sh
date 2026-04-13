#!/usr/bin/env bash
# Copy example env files for first-time Droplet setup (no secrets filled in).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env — edit APP_HOST, API_HOST, LETSENCRYPT_EMAIL, NEXT_PUBLIC_*"
else
  echo ".env already exists, skipping."
fi

if [[ ! -f backend/.env ]]; then
  cp backend/.env.example backend/.env
  echo "Created backend/.env — set secrets and DATABASE_URL"
else
  echo "backend/.env already exists, skipping."
fi

if [[ ! -f frontend/.env.production ]]; then
  cp frontend/.env.production.example frontend/.env.production
  echo "Created frontend/.env.production — set NEXT_PUBLIC_* (must match build-time URLs)"
else
  echo "frontend/.env.production already exists, skipping."
fi

echo ""
echo "Next:"
echo "  1) Point DNS for APP_HOST and API_HOST to this server."
echo "  2) Set CORS_ORIGINS in backend/.env to include https://\${APP_HOST}"
echo "  3) Set NEXT_PUBLIC_API_URL in root .env to https://\${API_HOST} (same value in frontend/.env.production for reference)"
echo "  4) docker compose up -d && ./deploy/scripts/init-letsencrypt.sh"
