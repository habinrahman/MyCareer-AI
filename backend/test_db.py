"""
Optional manual check: async SQLAlchemy + asyncpg can reach Postgres.

Usage (from ``backend/``, use the **project virtualenv** so ``asyncpg`` is available):

  Windows: .\\venv\\Scripts\\python.exe test_db.py
  Unix:    ./venv/bin/python test_db.py

Loads ``backend/.env`` via Pydantic Settings (run from any directory). Never commit secrets.
"""

from __future__ import annotations

import asyncio
import os
import ssl
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.core.postgres_connect import build_asyncpg_connect_args  # noqa: E402


def _die_if_no_asyncpg() -> None:
    try:
        import asyncpg  # noqa: F401
    except ModuleNotFoundError:
        print(
            "Missing dependency: asyncpg. Run this script with the project venv Python, e.g.\n"
            r"  .\venv\Scripts\python.exe test_db.py",
            file=sys.stderr,
        )
        sys.exit(1)


async def main() -> None:
    _die_if_no_asyncpg()
    # So pydantic-settings finds backend/.env when launched from another directory.
    os.chdir(_BACKEND)
    try:
        settings = Settings()
    except Exception as exc:  # noqa: BLE001 — smoke script
        print(
            "Could not load Settings from backend/.env (and environment).",
            type(exc).__name__,
            exc,
            file=sys.stderr,
        )
        sys.exit(1)
    engine = create_async_engine(
        settings.database_url,
        connect_args=build_asyncpg_connect_args(settings),
    )
    try:
        async with engine.connect() as conn:
            one = (await conn.execute(text("SELECT 1"))).scalar_one()
        print("Database OK, SELECT 1 =>", one)
    except ssl.SSLCertVerificationError as exc:
        print("TLS certificate verification failed.", file=sys.stderr)
        print(
            "Remediation: set DATABASE_SSL_CAFILE to your org/root PEM; or for local dev only "
            "with APP_ENV=development, DATABASE_SSL_INSECURE=true. See DIAGNOSTIC_REPORT.md.",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
