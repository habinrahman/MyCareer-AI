#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> MyCareer AI setup"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example — edit with your values."
else
  echo "Skipping root .env (already exists)."
fi

if [[ ! -f backend/.env ]]; then
  cp backend/.env.example backend/.env
  echo "Created backend/.env from backend/.env.example"
else
  echo "Skipping backend/.env (already exists)."
fi

if [[ ! -f frontend/.env.local ]]; then
  cp frontend/.env.example frontend/.env.local
  echo "Created frontend/.env.local from frontend/.env.example"
else
  echo "Skipping frontend/.env.local (already exists)."
fi

if [[ ! -d backend/.venv ]]; then
  python3 -m venv backend/.venv
  echo "Created backend/.venv"
fi

# shellcheck source=/dev/null
source backend/.venv/bin/activate
pip install -r backend/requirements.txt

cd frontend
npm install

echo ""
echo "Done. Next:"
echo "  1. Run supabase/migrations/0001_init.sql in your Supabase SQL editor."
echo "  2. Fill backend/.env and frontend/.env.local."
echo "  3. Terminal A: cd backend && source .venv/bin/activate && uvicorn app.main:app --reload"
echo "  4. Terminal B: cd frontend && npm run dev"
