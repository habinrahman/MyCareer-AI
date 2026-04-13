# MyCareer AI — Diagnostic Report

**Generated:** 2026-04-11  
**Scope:** Backend FastAPI + asyncpg/SQLAlchemy, Supabase PostgreSQL, SSL/TLS, frontend API auth, schema checks, dependencies.  
**Note:** This document uses **placeholders** for secrets and hosts. Do not paste real keys into tickets or chat logs.

---

## 1. Executive Summary

The persistent `ssl.SSLCertVerificationError: certificate verify failed: self-signed certificate in certificate chain` is **not a bug in Supabase or in the FastAPI route logic itself**. It occurs when **asyncpg** opens a TLS connection to PostgreSQL using an `ssl.SSLContext` built with **`ssl.CERT_REQUIRED`** (correct for production). The handshake fails because the **certificate chain presented to the client** includes a certificate that Python’s trust store does not treat as a trusted anchor.

**Most likely root causes (in order):**

1. **TLS interception** (corporate proxy, antivirus “HTTPS scanning,” or a middlebox) replacing or augmenting the chain with an **enterprise private CA** or **self-signed** issuer that is **not** in the trust store used by **OpenSSL** (which backs Python’s `ssl` module on Windows builds).
2. **Missing custom CA bundle** in the app: the codebase trusts the **OS default store** via `ssl.create_default_context()`, then optionally `DATABASE_SSL_CAFILE` / certifi. If the inspecting CA is only in the **Windows user/machine store** but not merged the way OpenSSL expects, or the chain is unusual, verification can still fail.
3. **Less common:** Wrong host/port (e.g. non-Supabase endpoint), IPv6-only issues, or DNS hijack — ruled out when DNS resolves and the error is specifically **self-signed in chain** during **TLS** (as in your stack traces).

**Application symptom:** Any code path that checks out a DB connection fails the same way — notably `POST /upload-resume` → `resume_pipeline.upload_resume_file` → `persistence.ensure_user_row` → `session.execute(...)` (first DB use).

**Fix priority:** Prefer **`DATABASE_SSL_CAFILE`** (PEM of org root/chain) → then **`DATABASE_SSL_USE_CERTIFI=true`** on minimal Linux if only Mozilla roots are missing → **last resort (development only):** `APP_ENV=development` + `DATABASE_SSL_INSECURE=true`.

---

## 2. Root Cause Analysis

| Layer | Finding |
|--------|---------|
| **Error class** | `ssl.SSLCertVerificationError` during `asyncio` `start_tls` / OpenSSL handshake. |
| **Driver** | `asyncpg` via SQLAlchemy dialect `postgresql+asyncpg`. |
| **Trust policy** | `build_asyncpg_ssl_context` uses `ssl.create_default_context()` + `verify_mode=CERT_REQUIRED` unless dev insecure mode is enabled. |
| **Chain semantics** | “Self-signed certificate **in certificate chain**” means some link in the chain is not anchored to a trusted root **from the client’s perspective** — typical of **inspection appliances** or **mis-issued** server certs, not of a correct public Supabase-only chain on a clean consumer network. |

The backend **does** pass an explicit `ssl` object to asyncpg for non-loopback hosts when `database_ssl_required` is true (default). That is **correct** for Supabase. The failure is **environment/trust configuration**, not missing `ssl=True` in the URL string.

---

## 3. Identified Errors

| Error | Classification | Where it surfaces |
|--------|----------------|-------------------|
| `SSLCertVerificationError: self-signed certificate in certificate chain` | **SSL / trust store** (environment) | `asyncpg.connect_utils._create_ssl_connection` → `loop.start_tls` |
| `500` on `POST /upload-resume` | **Downstream of SSL** — DB session cannot connect | `resume.py` → `resume_pipeline.py` → `persistence.py` |
| `ModuleNotFoundError: asyncpg` (if seen) | **Wrong Python interpreter** | Running `python` without project venv |

---

## 4. Affected Files and Line Numbers

| File | Role |
|------|------|
| `backend/app/core/postgres_connect.py` | `build_asyncpg_ssl_context` (~41–75), `build_asyncpg_connect_args` (~78–95): TLS + pooler `statement_cache_size=0` for port 6543 / `pooler.supabase.com` / `pgbouncer=true`. |
| `backend/app/core/database.py` | `create_async_engine(..., connect_args=build_asyncpg_connect_args(settings))` (~32–41); startup warning if dev insecure SSL (~46–50). |
| `backend/app/core/config.py` | `database_url` normalization/validation (~10–16, 157–173), DNS check at settings init (~175–186), SSL-related fields (~98–140). |
| `backend/app/services/persistence.py` | `ensure_user_row` (~11–21) — **first failing line** when SSL breaks, because it runs SQL as soon as a session needs a connection. |
| `backend/app/api/routes/resume.py` | `upload_resume` (~36–57) — triggers persistence. |
| `backend/app/main.py` | App factory, CORS, lifespan `engine.dispose()` (~30–36) — no SSL bug; confirms engine is global. |
| `frontend/src/lib/api.ts` | Axios interceptor attaches `Authorization: Bearer <access_token>` (~35–63) — orthogonal to Postgres SSL. |

---

## 5. Environment Diagnostics

### Python and OpenSSL

- **Supported:** Python 3.11+ with async SQLAlchemy 2.x and asyncpg 0.30.x (see `requirements.txt`).
- **Observed in diagnostics:** Python **3.13.x** with **OpenSSL 3.0.x** (Windows) is compatible with the pinned stack; failures are **trust**, not version skew.
- **Virtualenv:** Always use **`backend/venv/Scripts/python.exe`** (Windows) or **`backend/venv/bin/python`** (Unix) for `uvicorn`, `pytest`, `test_db.py`, and `test_env.py`.

### Antivirus / proxy

- Products that **scan TLS** often install a **local root** into the Windows store. Python’s OpenSSL may still fail until that root is in a **PEM** referenced by **`DATABASE_SSL_CAFILE`** or the OS store is correctly wired for your build.
- **Corporate HTTP proxy** usually affects HTTPS to the internet, not raw Postgres **5432/6543**, unless traffic is explicitly proxied — but **SSL inspection** can still apply to outbound TLS.

### `certifi`

- Listed in `requirements.txt`. Used only when **`DATABASE_SSL_USE_CERTIFI=true`** and no `DATABASE_SSL_CAFILE` (see `postgres_connect.py`). Not a substitute for an **enterprise inspection root** unless that root is **included** in the bundle you point to.

### Scripts added/updated

- **`backend/test_env.py`** — Redacted settings summary, OpenSSL version, DNS for DB host, optional asyncpg version.
- **`backend/test_db.py`** — Loads `backend/.env` via `Settings()`, runs `SELECT 1`, catches TLS verification errors with **exit code 2** and remediation text; **`sys.path`** fix allows `python backend/test_db.py` from repo root when using the venv interpreter.

**Do not commit** real `.env` files. Use `backend/.env.example` and `frontend/.env.example` as templates.

---

## 6. Dependency Compatibility Report

| Package | Pinned (excerpt) | Notes |
|---------|------------------|--------|
| FastAPI | 0.115.6 | OK with Starlette middleware stack in `main.py`. |
| SQLAlchemy | 2.0.36 + asyncio | Async engine + asyncpg URL scheme required. |
| asyncpg | 0.30.0 | TLS via `connect_args["ssl"]` SSLContext. |
| pydantic-settings | 2.7.0 | Loads `backend/.env` when CWD is backend (scripts `chdir` to backend). |
| certifi | 2024.12.14 | Optional trust augmentation. |

No change required for compatibility to resolve SSL trust issues; **configuration** drives the fix.

---

## 7. Supabase Connectivity Status

### URL and driver

- **`DATABASE_URL`** must normalize to scheme **`postgresql+asyncpg`** (`config.normalize_database_url`).
- **Transaction pooler (recommended):** host like `*.pooler.supabase.com`, port **6543**, query **`pgbouncer=true`** — code sets **`statement_cache_size=0`** to avoid prepared-statement issues with PgBouncer.

### DNS / IPv4 / IPv6

- `Settings` validates **`socket.getaddrinfo`** on the DB hostname at import (~175–186 in `config.py`). If DNS fails, you get a **validation error at startup**, not an SSL error.

### Connectivity vs SSL

- **TCP + DNS can succeed** while **TLS verification still fails** — that matches `SSLCertVerificationError` after connect.

---

## 8. SSL Certificate Analysis

### What the app sends to asyncpg

- Non-loopback + `database_ssl_required=True` → `connect_args["ssl"]` is an `SSLContext` with:
  - **Default:** `create_default_context(SERVER_AUTH)`, optional `load_verify_locations` from `DATABASE_SSL_CAFILE` or certifi path, **`CERT_REQUIRED`**, hostname check per `effective_database_ssl_verify_hostname` (staging/production always verify hostname).
  - **Development only:** `DATABASE_SSL_INSECURE=true` + `APP_ENV=development` → **`CERT_NONE`** (documented MITM risk).

### Why “self-signed in chain” on Supabase path

- Legitimate Supabase pooler endpoints use **public CAs**. A **self-signed** entry almost always indicates **inspection / custom signing** or a **non-standard endpoint** in the path.
- **Remediation:** Export the **inspecting root CA** (or full chain PEM) and set **`DATABASE_SSL_CAFILE`**. Confirm with your IT department if on a managed device.

---

## 9. Recommended Fixes

1. **Obtain PEM** for the CA that signs the TLS certificate you see when connecting to the DB host (same as in `DATABASE_URL`).
2. Set in **`backend/.env`**:
   - `DATABASE_SSL_CAFILE=C:\path\to\corp-or-inspection-root.pem`  
   - Keep `DATABASE_SSL_REQUIRED=true`.
3. Restart **`uvicorn`**.
4. Re-run **`python backend/test_db.py`** (from repo root with venv) or `cd backend` + `.\venv\Scripts\python.exe test_db.py`.
5. If still failing in **dev only** and you accept risk: `APP_ENV=development` and `DATABASE_SSL_INSECURE=true` — **never** in production.

---

## 10. Step-by-Step Remediation Guide

1. `cd backend`
2. Activate venv: `.\venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Unix).
3. Run `python test_env.py` — confirm `DATABASE_URL (shape)` uses `postgresql+asyncpg` and pooler port **6543** if using transaction mode.
4. Run `python test_db.py`:
   - **Exit 0** — DB TLS OK.
   - **Exit 2** — follow section 9 (CA file or dev-only insecure flag).
5. Start API: `uvicorn app.main:app --reload --port 8000` (from `backend/`).
6. Frontend: copy `frontend/.env.example` → `.env.local`; set `NEXT_PUBLIC_SUPABASE_*` and `NEXT_PUBLIC_API_URL`; `npm run dev`.
7. Docker: from repo root, ensure `backend/.env` and `frontend/.env.production` exist per `docker-compose.yml`; `docker compose up --build`.
8. Supabase SQL: run `supabase/verify_schema.sql` after applying **`supabase/schema.sql`** (authoritative for this app — see section 11).

---

## 11. Production Readiness Assessment

| Area | Status | Notes |
|------|--------|--------|
| Async driver + pooler | **Ready** | `statement_cache_size=0` when pooler detected. |
| TLS defaults | **Ready** | `CERT_REQUIRED`; hostname enforced outside development. |
| Dev-only insecure SSL | **Controlled** | Ignored when `APP_ENV` ≠ `development`. |
| Schema | **Action required** | `supabase/migrations/0001_init.sql` is **legacy** (profiles-centric). Production should use **`supabase/schema.sql`** (`users`, `analyses`, `reports`, etc.) per comments in `0001_init.sql`. |
| RLS | **Review** | Service role bypasses RLS; use least privilege and secrets rotation. |
| Secrets in repo | **Verify** | No keys in committed `.env`; rotate if ever leaked. |

---

## 12. Risk and Security Recommendations

- **Do not** disable TLS verification (`DATABASE_SSL_INSECURE`) outside local development.
- **Do not** commit `backend/.env`, `frontend/.env.local`, or production env files.
- Prefer **CA pinning via `DATABASE_SSL_CAFILE`** over insecure mode.
- **Rotate** `SUPABASE_SERVICE_ROLE_KEY` and DB password if exposed.
- Keep **`CORS_ORIGINS`** explicit; avoid `allow_headers=["*"]` with credentials (current `main.py` uses an explicit list — good).
- **JWT:** Backend validates Supabase JWTs; ensure `SUPABASE_JWT_SECRET` matches project settings.

---

## Appendix: Validation Commands (canonical)

```text
# Backend (from backend/)
uvicorn app.main:app --reload --port 8000

# Frontend (from frontend/)
npm run dev

# Diagnostics (from repo root — use venv python)
backend\venv\Scripts\python.exe backend\test_env.py
backend\venv\Scripts\python.exe backend\test_db.py

# Docker (from repo root)
docker compose up --build
```

---

*This report reflects the repository state at generation time. Re-run `test_env.py` / `test_db.py` after any infrastructure or `.env` change.*
