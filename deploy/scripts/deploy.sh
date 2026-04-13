#!/usr/bin/env bash
# Pull latest images (if using registry), rebuild, and restart the stack.
# Run from repo root on the Droplet after git pull.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

echo "==> Building images"
docker compose build --pull

echo "==> Starting / updating services"
docker compose up -d --remove-orphans

echo "==> Status"
docker compose ps
