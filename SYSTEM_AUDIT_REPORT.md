# MyCareer AI — Backend system audit report

**Scope:** `backend/app/api/`, `core/`, `services/`, `models/`, `schemas/`, `utils/`, `middleware/`  
**Date:** 2026-04-11 (revised)  
**Focus:** SQLAlchemy async sessions, `InvalidRequestError` (nested transactions), Supabase Postgres, FastAPI dependencies, production readiness

---

## 1. Issues detected

| Severity | Area | Finding |
|----------|------|--------|
| **Critical (root cause)** | SQLAlchemy autobegin + `session.begin()` | `InvalidRequestError: A transaction is already begun on this Session` occurs when code calls **`async with session.begin():`** (or equivalent) on an `AsyncSession` that **already** has an active transaction. With default **autobegin**, the first `await session.execute(...)` starts a transaction; a second `begin()` is invalid. |
| **Medium** | `app/core/database.py` | `get_db()` did not call **`session.close()`** in a `finally` block after `yield` (relying only on `async with` cleanup). Explicit close makes lifecycle obvious and matches FastAPI + SQLAlchemy guidance for generator dependencies. |
| **Low** | `POST /chat` + `stream=true` | Route still injects **`get_db`** even though **`stream_mentor_turn`** uses its own `AsyncSessionLocal()` session. The request-scoped session may sit idle for the stream duration (pool tie-up). Consider a dedicated **`/chat/stream`** route without `get_db` in a future refactor. |
| **Info** | Repository grep | Current `backend/app` tree contains **no** `session.begin(`, `async with session.begin`, or `begin_nested` — services use **`commit` / `rollback`** only. Any error you saw likely came from **older/local code**, a **fork**, or a **library example** pasted into a service. |

---

## 2. Fixes applied

### 2.1 Transaction policy (no nested `begin()`)

- **`app/core/database.py` — `get_db()`**
  - Documents that **nested `session.begin()` must not** be used with autobegin + injected sessions.
  - **`try` / `except Exception`:** `await session.rollback()` then re-raise.
  - **`finally`:** `await session.close()` for explicit teardown (idempotent with `async with AsyncSessionLocal()` exit).

- **`app/services/resume_pipeline.py`**
  - Module note: use **`commit` / `rollback`** only; never **`async with session.begin()`** on the injected session.
  - **`upload_resume_file`:** unchanged — single `commit` after persistence + storage.
  - **`analyze_resume_for_user`:** unchanged logic — `commit` after `set_resume_processing`; success path commits once after writes; `AppError` / generic paths use `rollback` + `set_resume_failed` + `commit` as appropriate.

- **`app/services/chat_mentor_service.py`**
  - **`run_mentor_turn`:** single `commit` at end (unchanged).
  - **`stream_mentor_turn`:** owns a **separate** session via `async with AsyncSessionLocal()`; mid-stream `commit` after user message and final `commit` after assistant message with rollback on assistant persist failure (unchanged).

- **`app/services/persistence.py`**
  - Module docstring: callers own transaction boundaries; no `session.begin()` in helpers.

### 2.2 Supabase transaction pooler + asyncpg

- **`app/core/postgres_connect.py`:** `statement_cache_size=0` in `connect_args` when the URL indicates the **transaction pooler** (port `6543`, `pooler.supabase.com`, or `pgbouncer=true`). Not forced on every host (direct `5432` sessions can keep the statement cache).
- **`create_async_engine`:** `pool_pre_ping`, pool size / recycle / timeout from `Settings`; `connect_args` from `build_asyncpg_connect_args` (TLS + pooler).

### 2.3 Unchanged (already correct)

- **`persistence.py`:** Stateless `execute` helpers; no transaction wrappers.
- **JWT / CORS / SlowAPI / GZip / Request context / Sentry:** No ORM session lifecycle coupling beyond normal exception propagation.

---

## 3. Security improvements (existing)

- TLS to Postgres for non-loopback hosts; hostname verification outside `APP_ENV=development`.
- Optional `DATABASE_SSL_CAFILE`; dev-only insecure TLS flag logged and ignored in staging/production.
- Secrets remain server-side (`SUPABASE_SERVICE_ROLE_KEY`, `OPENAI_API_KEY`, `DATABASE_URL`).

---

## 4. Performance

- **`analyze_resume_for_user`:** Commits **`processing`** before long OpenAI / download work to shorten row lock duration.
- **Connection pooling:** Configurable via `Settings` (`database_pool_*`, `database_connect_timeout`).

---

## 5. Supabase connectivity status

| Item | Status |
|------|--------|
| Driver | `postgresql+asyncpg://` (normalized from `postgres://` / `postgresql://`) |
| Transaction pooler | `statement_cache_size=0` when pooler is detected in URL |
| TLS | `build_asyncpg_ssl_context` (OS + certifi + optional `DATABASE_SSL_CAFILE`) |
| Live connectivity | Environment-specific — use `backend/test_db.py` and `backend/test_env.py` |

---

## 6. Deployment readiness checklist

- [ ] `APP_ENV=production` or `staging` for strict TLS hostname checks.
- [ ] `DATABASE_URL` uses Supabase **transaction** pooler when appropriate for server workloads.
- [ ] Secrets from platform secret store, not committed `.env`.
- [ ] Docker image: CA certificates + Python `certifi` as in `requirements.txt`.
- [ ] Supabase RLS + storage policies reviewed for production.
- [ ] CI: `ruff check` + `pytest` on each PR.

---

## 7. Middleware compatibility

| Middleware | DB impact |
|------------|-----------|
| SlowAPI (`SafeSlowAPIMiddleware`) | None |
| GZip | None |
| CORS | None |
| Request context | None |
| Sentry | Exceptions after `get_db` rollback path |

---

## 8. Endpoint validation (contract)

| Route | Session | Notes |
|-------|---------|-------|
| `POST /upload-resume` | `get_db` | Service `commit` after DB + Storage. |
| `POST /analyze-resume` | `get_db` | Service-owned commits / rollbacks. |
| `POST /chat` | `get_db` + optional stream-only session | JSON path uses injected session; SSE uses **inner** `AsyncSessionLocal()` (see §1 Low). |
| `GET /chat-history/{id}` | `get_db` | Read-only; no commit. |
| `GET /report/{report_id}` | `get_db` | Read + cache; no DB writes in route. |
| `GET /download-report/{analysis_id}` | `get_db` | Read-only. |
| `GET /health` | `get_db` | `SELECT 1` ping. |

---

## 9. Component status (expected)

| Component | Expected state |
|-----------|----------------|
| Supabase PostgreSQL | OK when URL, TLS, and DNS are correct |
| Resume upload | OK with explicit `commit` |
| Resume analysis | Stable without nested `begin()` |
| AI chatbot | JSON path committed in service; stream path isolated session |
| PDF reports | PDF built in route from DB row; verify separately |
| Authentication | JWT unchanged |
| SQLAlchemy transactions | Autobegin + explicit `commit`/`rollback`; `get_db` rolls back on errors and closes in `finally` |
| Logging | `logger` in resume pipeline, chat stream persist failures |
| Docker / DigitalOcean | Compose + env templates align with README |

---

## 10. Follow-up

1. Integration tests against disposable Postgres for multi-step `analyze_resume_for_user` paths.  
2. Optional: **`GET /chat/stream`** (or similar) without `get_db` to avoid idle pooled sessions during long SSE.  
3. Keep **service-owned commits**; do **not** add `async with session.begin()` inside services on `get_db` sessions.

---

*Re-audit after any new service that touches `AsyncSession`.*
