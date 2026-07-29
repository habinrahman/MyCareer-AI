<div align="center">

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=for-the-badge&logo=next.js)
![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker)
![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)
![CI](https://img.shields.io/github/actions/workflow/status/habinrahman/MyCareer-AI/ci.yml?branch=main&label=CI&style=for-the-badge)

# MyCareer AI

**AI-powered resume intelligence and career mentorship** — analyze resumes, benchmark against industry standards, chat with an AI career mentor, and improve employability.

[Features](#features) · [Quick start](#3-local-development-without-docker) · [Deploy](#7-deploying-on-a-digitalocean-droplet) · [Contributing](./CONTRIBUTING.md) · [Changelog](./CHANGELOG.md)

</div>

---

## Features

| Feature | Description |
| -------- | ------------ |
| **Resume analysis** | ATS scoring, strengths/weaknesses, keyword gaps, structured JSON via OpenAI |
| **Career chat** | Streaming SSE mentorship with session history and optional structured facets |
| **Benchmarks** | Compare skills and experience against career-path benchmarks |
| **Job matching** | Semantic job fit scoring with pgvector embeddings |
| **PDF reports** | Downloadable analysis reports with QR verification |
| **Public resume tool** | Lead-capture flow for unauthenticated resume review |
| **Production-ready** | Docker Compose, Nginx TLS, rate limiting, JWT auth, RLS-ready schema |

## Tech stack

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, TanStack Query, Supabase Auth
- **Backend**: FastAPI (async), OpenAI SDK, SQLAlchemy + asyncpg, pgvector
- **Data**: Supabase PostgreSQL, Storage, Row Level Security
- **Ops**: Docker, GitHub Actions CI, Dependabot, DigitalOcean deployment guides

Stack: **resume analysis** with OpenAI, **personalized career guidance** via chat, **Supabase** (Auth, Postgres, Storage, pgvector), and a **Next.js** + **FastAPI** split.

## Architecture

```mermaid
flowchart LR
  subgraph client [Browser]
    Next[Next.js 14]
  end
  subgraph supa [Supabase]
    Auth[Auth]
    PG[(Postgres + pgvector)]
    St[Storage]
  end
  subgraph api [Backend]
    FastAPI[FastAPI async]
    OAI[OpenAI]
  end
  Next -->|JWT| FastAPI
  Next --> Auth
  FastAPI --> PG
  FastAPI --> St
  FastAPI --> OAI
```

- **Frontend** (`frontend/`): Next.js 14 (App Router), TypeScript, Tailwind CSS, Supabase Auth client.
- **Backend** (`backend/`): FastAPI (async), OpenAI SDK, Supabase Storage + Postgres (SQLAlchemy/asyncpg, pgvector), resume parsing (PyMuPDF, pdfplumber, python-docx).
- **Data**: Supabase PostgreSQL with `pgvector`, Supabase Storage for resume files, Row Level Security (RLS) recommended for production.

## Prerequisites

- Node.js 20+
- Python 3.11+
- Docker & Docker Compose (for containerized run)
- [Supabase](https://supabase.com) project
- [OpenAI](https://platform.openai.com) API key

## 1. Supabase setup

1. Create a project in Supabase.
2. Run **`supabase/schema.sql`** in the SQL Editor (Dashboard → SQL). This is the production schema (`users`, `resumes`, `analyses`, `chat_*`, `recommendations`, `reports`, pgvector indexes, RLS, and Storage bucket stubs). The file `supabase/migrations/0001_init.sql` is a legacy minimal demo only; do not use it for the current FastAPI backend.
3. **Resume PDF lead capture**: If your database was created before this feature, run **`supabase/migrations/0004_resume_download_leads.sql`** in the SQL Editor (or keep `schema.sql` in sync). This adds `public.resume_download_leads` for storing name, email, and phone before users download the public AI PDF. If you already applied an older `0004` that referenced `analyses`, run **`supabase/migrations/0005_resume_download_leads_drop_analysis_fk.sql`** so `analysis_id` stays optional without a foreign key. The backend exposes **`POST /leads/`** (rate-limited); inserts use your **`DATABASE_URL`** pooler connection.
4. Create a **Storage** bucket named `resumes` (private). Optionally add a policy so authenticated users can upload to their own folder prefix (`user_id/`).
5. Copy **Project URL**, **anon key**, and **service role key** (server only) from Project Settings → API.
6. For backend JWT verification: Project Settings → API → **JWT Secret**.

## 2. Environment variables

### Root (Docker Compose)

```bash
cp .env.example .env
# Edit .env with your Supabase URL, anon key, and public API URL
```

### Backend

```bash
cd backend
cp .env.example .env
# Set OPENAI_API_KEY, SUPABASE_*, DATABASE_URL (pooler or direct), JWT_SECRET
```

Use Supabase **connection string** (Settings → Database) as `DATABASE_URL`. For serverless-friendly pooling, use the **Transaction** pooler URI when available.

#### PostgreSQL TLS, Supabase pooler, and environments

The backend uses **SQLAlchemy 2 + asyncpg** with:

- **TLS**: For non-loopback hosts, connections use an `ssl.SSLContext` with **`ssl.CERT_REQUIRED`**, built from the **OS trust store** first (Windows Certificate Store, Linux `ca-certificates`). This avoids `self-signed certificate in certificate chain` errors common when **corporate TLS inspection** adds a root that exists only in the system store. Set **`DATABASE_SSL_USE_CERTIFI=true`** to also load Mozilla roots from **certifi** (helpful on some minimal containers). Set **`DATABASE_SSL_CAFILE`** to a PEM file to merge an extra CA bundle (e.g. exported enterprise root).
- **Hostname verification**: **Enforced in staging and production** regardless of flags. In **`APP_ENV=development`**, hostname checks default to **off** (`DATABASE_SSL_VERIFY_HOSTNAME=false`) while certificate chain validation stays on—useful for some pooler/DNS setups; set `DATABASE_SSL_VERIFY_HOSTNAME=true` when you want strict local behavior.
- **Transaction pooler**: If the URL uses port **6543**, a **pooler** hostname, or `pgbouncer=true`, the engine sets asyncpg **`statement_cache_size=0`**, which Supabase **transaction** mode requires.
- **Local Postgres** (`localhost`, `127.0.0.1`, `::1`): No explicit SSL context is applied so a typical dev Postgres without TLS still works (e.g. `docker compose --profile local-db`).

Ensure `DATABASE_URL` uses the **`postgresql+asyncpg://`** scheme (or `postgres://` / `postgresql://`; the app normalizes it). The backend **`Dockerfile`** installs **`ca-certificates`**; **`certifi`** is pinned for optional `DATABASE_SSL_USE_CERTIFI=true`.

##### Troubleshooting TLS to Supabase

- **`certificate verify failed` / `self-signed certificate in certificate chain`**: Often **VPN or antivirus HTTPS scanning**. Keep **`DATABASE_SSL_USE_CERTIFI=false`** (default) so Python uses the **Windows/macOS/Linux system store** (where your org’s inspection CA usually lives). If it still fails, export the proxy root PEM and set **`DATABASE_SSL_CAFILE`**. On **very slim Docker** images with an empty store, try **`DATABASE_SSL_USE_CERTIFI=true`**.
- **`prepared statement` / PgBouncer errors**: Use the **transaction** pooler (port **6543**) and keep `statement_cache_size=0` (automatic when the URL matches pooler heuristics).

### Frontend

```bash
cd frontend
cp .env.local.example .env.local
# Or: cp .env.example .env.local — set NEXT_PUBLIC_SUPABASE_* and NEXT_PUBLIC_API_URL
```

The shared Axios client (`frontend/src/lib/api.ts`) attaches `Authorization: Bearer <access_token>` from the browser Supabase session on every request, so protected FastAPI routes receive a valid JWT without manual wiring.

Never commit `.env`, `backend/.env`, or `frontend/.env.local`.

## 3. Local development (without Docker)

### Backend

**1. Environment file** — the API will not start until required variables are set. From `backend/`:

```bash
cp .env.example .env
```

Edit `backend/.env` and fill at least: **`OPENAI_API_KEY`**, **`SUPABASE_URL`**, **`SUPABASE_SERVICE_ROLE_KEY`**, **`SUPABASE_JWT_SECRET`** (Supabase Dashboard → **Project Settings → API → JWT Secret**), and **`DATABASE_URL`**. If `SUPABASE_JWT_SECRET` is missing, you will see: `ValidationError ... supabase_jwt_secret Field required`. For local development, **`RATE_LIMIT_ENABLED=false`** (default in `.env.example`) avoids hitting SlowAPI limits while iterating.

**2. Virtualenv and server**

**Windows (PowerShell)** — do **not** use `source` (that is a Unix shell command).

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

If activation is blocked by execution policy: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

**macOS / Linux (bash)**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). OpenAPI UI: [http://localhost:8000/docs](http://localhost:8000/docs).

Main HTTP routes: `POST /upload-resume`, `POST /analyze-resume`, `GET /download-report/{analysis_id}` (PDF), `POST /chat` (optional `stream: true` for SSE, `structured_output: true` for JSON facets), `GET /chat-history/{session_id}`, `GET /report/{id}`, `GET /careers/me`, `PATCH /careers/me`, `GET /careers/benchmarks`, `POST /careers/jobs/match`, `GET /health` (all require `Authorization: Bearer <Supabase access token>` except health is public).

## 4. Docker Compose

### Production-style stack (Nginx + TLS on a VPS)

Full steps, DNS, Let’s Encrypt, and firewall notes are in **`deploy/DEPLOYMENT.md`**.

Quick reference from the repo root:

```bash
./deploy/scripts/bootstrap-env.sh   # or copy .env / backend/.env / frontend/.env.production manually
docker compose build
docker compose up -d
./deploy/scripts/init-letsencrypt.sh   # after DNS points to the server
```

### Local containers without Nginx

```bash
docker compose -f docker-compose.yml -f deploy/docker-compose.dev.yml up -d
```

API: `http://127.0.0.1:8000`, web: `http://127.0.0.1:3000`.

### Minimal API + web only (no Nginx profile)

```bash
docker compose -f docker-compose.local.yml up --build
```

Requires `backend/.env` and `frontend/.env.local`; build args for the frontend can be set in a root `.env` or the shell (`NEXT_PUBLIC_*`).

### Optional: local Postgres + pgvector

```bash
docker compose --profile local-db up -d postgres
# Set backend DATABASE_URL to postgresql+asyncpg://mycareer:mycareer_dev@localhost:54322/mycareer
```

## 5. Testing & QA

### Backend (pytest)

```bash
cd backend
pip install -r requirements-dev.txt
pytest -q
```

### Frontend (Jest)

```bash
cd frontend
npm test
```

### API smoke script (HTTP checks)

```bash
cd backend
python scripts/api_smoke.py --base-url http://127.0.0.1:8000
```

## 6. Initial setup scripts

- **Windows (PowerShell)**: `scripts/setup.ps1`
- **macOS / Linux**: `scripts/setup.sh`

These copy env templates and optionally create Python venv / `npm install`.

## 7. Deploying on a DigitalOcean Droplet

Use **`deploy/DEPLOYMENT.md`**: Dockerfiles, Compose, Nginx reverse proxy, Certbot, env layout, `deploy/scripts/*.sh`, and troubleshooting.

## 8. Security checklist (production)

- Enable RLS on all user tables; scope by `auth.uid()`.
- Validate Supabase JWT on every protected FastAPI route (`Authorization: Bearer <access_token>`).
- Store OpenAI and service role keys only on the server.
- Rate-limit upload and chat endpoints (add middleware or edge proxy).
- Scan uploads for type/size; never execute user files.
- Run `APP_ENV=production` (or `staging`) in deployed environments so Postgres TLS hostname verification stays enforced; keep service keys and `DATABASE_URL` out of client bundles and logs.

## 9. Project structure

```
.
├── backend/                 # FastAPI application
├── frontend/                # Next.js application
├── supabase/schema.sql      # Production Postgres + pgvector + RLS (run in Dashboard)
├── supabase/migrations/     # Legacy snippets (prefer schema.sql for this backend)
├── deploy/                  # Nginx image, TLS templates, scripts, DEPLOYMENT.md
├── scripts/                 # setup.ps1, setup.sh
├── docker-compose.yml
├── .env.example
└── README.md
```

## 11. Screenshots & demo

![Resume analysis demo](docs/assets/resume-analysis-demo.gif)

| Landing — upload resume | AI analysis results |
| ----------------------- | ------------------- |
| Drop zone + one-click analyze | ATS score, strengths, skill gaps, course recommendations |

Re-record locally (mock API, no OpenAI key):

```bash
cd frontend && PORT=3010 npm run dev
# in another terminal:
cd scripts && npm install && npx playwright install chromium
DEMO_BASE_URL=http://localhost:3010 npm run record:demo
```

Use `DEMO_BASE_URL` if the dev server binds to a port other than 3000.

## 12. Roadmap

- [ ] v0.2 — GitHub Discussions + community issue triage
- [ ] v0.3 — Enhanced job board integrations
- [ ] v0.4 — Multi-language resume support
- [ ] v1.0 — Stable public API + hosted demo instance

See [CHANGELOG.md](./CHANGELOG.md) for release history.

## 13. FAQ

**Do I need OpenAI and Supabase accounts?**  
Yes for full functionality. The public resume route can run stateless without DB for basic demos.

**Can I self-host?**  
Yes — use Docker Compose and follow [`deploy/DEPLOYMENT.md`](deploy/DEPLOYMENT.md).

**Is this production-ready?**  
The codebase includes auth, rate limits, TLS guidance, and tests, but you must configure RLS, secrets, and monitoring for your environment.

**How do I contribute?**  
See [CONTRIBUTING.md](./CONTRIBUTING.md). Good first issues are tagged `good first issue`.

## 14. License

[MIT License](./LICENSE) — Copyright (c) 2025 Habin Abdul Rahman.
