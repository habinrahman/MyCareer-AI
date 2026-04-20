# Supabase database integration (MyCareer AI)

This document describes how the FastAPI backend connects to **Supabase PostgreSQL** (via **asyncpg** + Async SQLAlchemy), how data maps to **API routes**, and how **Supabase Storage** is used for binary artifacts.

## Environment

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Async SQLAlchemy URL, e.g. `postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres` (transaction pooler) or port `5432` (direct). `postgres://` and `postgresql://` are auto-normalized to `postgresql+asyncpg://`. |
| `SUPABASE_URL` | Project URL (`https://<project>.supabase.co`). |
| `SUPABASE_SERVICE_ROLE_KEY` | Server-side Supabase client (Storage, bypasses RLS for DB when using the Postgres `postgres` role in `DATABASE_URL`). |
| `SUPABASE_JWT_SECRET` | Validates Supabase JWTs for authenticated routes. |
| `SUPABASE_RESUMES_BUCKET` | Storage bucket for uploaded resumes (default `resumes`). |
| `SUPABASE_REPORTS_BUCKET` | Storage bucket for generated PDFs referenced by `public.reports` (default `reports`). |
| `CORS_ORIGINS` | Comma-separated browser origins (default includes `http://localhost:3000`). |

Frontend (local): set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend/.env.local` (see `frontend/.env.local.example`).

## Schema source of truth

Apply **`supabase/schema.sql`** in the Supabase SQL Editor for a complete `public` schema (users, resumes, analyses, reports, chat, benchmarks, RLS, and storage bucket seeds).

Incremental migrations live under `supabase/migrations/` (e.g. `0004_resume_download_leads.sql`).

## Tables and API mapping

| Table | Written by | Notes |
|-------|------------|------|
| `public.users` | `POST /upload-resume` (via `ensure_user_row`) | Mirrors `auth.users` (trigger in `schema.sql` also provisions rows). |
| `public.resumes` | `POST /upload-resume` | Row created after file upload to Storage (`supabase_resumes_bucket`). |
| `public.analyses` | `POST /analyze-resume` | Versioned per resume; `findings` / `scores` are **JSONB**; embeddings via raw SQL in `persistence`. |
| `public.reports` | `GET /download-report/{analysis_id}` | PDF bytes uploaded to `reports` bucket, then a row with `storage_path` + `status='ready'`. |
| `public.resume_download_leads` | `POST /leads/` | Public lead capture (optional `analysis_id`). |
| `public.industry_benchmarks` | Seed / admin SQL | Read by `GET /careers/benchmarks` through `careers_repository.list_industry_benchmarks`. |

### Public resume tool (`POST /public/analyze-resume`)

The MicroDegree **Resume Intelligence** UI calls this route (no JWT). By default it does **not** write rows.

To **mirror** public runs into `public.resumes`, `public.analyses`, and (for `format=pdf`) `public.reports`:

1. Create a dedicated user in **Supabase Auth** (e.g. `public-resume-pipeline@yourdomain.com`) so `public.users` gets a row (via `schema.sql` trigger).
2. Copy that user’s UUID into backend **`.env`** as **`DEFAULT_USER_ID`** (canonical for no-login V1):

```env
DEFAULT_USER_ID=00000000-0000-0000-0000-000000000000
```

3. Restart the API. Each public analyze attaches storage + DB rows **under that tenant** (analytics / ops bucket, not per-browser identity).

Legacy env **`PUBLIC_RESUME_DB_OWNER_USER_ID`** is still read if `DEFAULT_USER_ID` is unset (same precedence: `DEFAULT_USER_ID` wins).

Runtime helpers: **`app.services.user_service`** (`resolve_default_user_id`, `get_default_user_id`) and **`app.services.database_service`** (Storage + SQLAlchemy bundles for `/public/analyze-resume` and leads).

### Deduping & integrity (migrations)

Run **`supabase/migrations/0007_dedupe_resume_report_integrity.sql`** in the Supabase SQL Editor when you are ready to clean legacy duplicates and add:

- partial **unique index** on `resumes (user_id, storage_path)` where `storage_path` is not null;
- **unique index** on `reports (analysis_id)` where `analysis_id` is not null (one stored PDF row per analysis).

The API also skips inserting a new report when a **ready** report already exists for the same analysis, and uses savepoints + `IntegrityError` handling for rare insert races on analyses and resumes.

Authenticated users should still use **`POST /upload-resume`** + **`POST /analyze-resume`** with a Bearer token so rows are tied to their own `user_id`.

## Backend layers

- **`app.core.database`** — Async engine + `get_db()` session factory (`pool_pre_ping`, asyncpg TLS via `postgres_connect`).
- **`app.services.persistence`** — Low-level `AsyncSession` + `text()` SQL (including pgvector casts).
- **`app.services.database_repository`** — Logged wrappers: `create_resume`, `create_analysis`, `create_report`, `create_lead`, `get_analysis_by_id`, `get_report_by_id`.
- **`app.services.supabase_storage`** — Upload / download / signed URLs for Storage.
- **`app.models.db_tables`** — Declarative ORM documentation (vectors omitted; use `persistence` for embeddings).

## Health checks

| Endpoint | Meaning |
|----------|---------|
| `GET /health` | Liveness; runs `SELECT 1` and reports `database`: `connected` or `degraded`. |
| `GET /health/db` | Strict DB probe: `200` + `{"status":"ok","database":"connected"}` or `503` + `{"status":"error","database":"disconnected"}`. |

Startup logs **`database.connectivity_ok`** with resolved host after `SELECT 1` on the global engine.

## Docker

`docker-compose.yml` injects `backend/.env` into the API container. Ensure `DATABASE_URL` and Supabase keys are set there (or via your host environment) before `docker compose up`.

## Operational scripts

From the `backend/` directory (with dependencies installed):

```bash
python scripts/test_db_connection.py
python scripts/test_data_flow.py
python scripts/test_data_flow.py --write-sample
```

## Troubleshooting

1. **`database: degraded` in `/health`** — Wrong password, network/VPN, or pooler settings. For Supabase pooler (port `6543`), keep `statement_cache_size=0` behavior (handled in `postgres_connect.py`).
2. **Lead insert 503 / undefined table** — Run `0004_resume_download_leads.sql` (and `0005_*.sql` if upgrading).
3. **Report row missing after download** — Check API logs for `report.download_persist_skipped` (Storage upload or DB insert failed); response may still return the PDF.
4. **CORS** — Set `CORS_ORIGINS` to include your frontend origin (comma-separated).
