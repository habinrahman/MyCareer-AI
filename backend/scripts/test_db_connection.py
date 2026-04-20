#!/usr/bin/env python3
"""
Verify DATABASE_URL (Supabase Postgres + asyncpg) from backend/.env.

Usage (from ``backend/`` with the project virtualenv):

    python scripts/test_db_connection.py
"""

from __future__ import annotations

import asyncio
import os
import sys


def _backend_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


async def main() -> int:
    backend = _backend_dir()
    if backend not in sys.path:
        sys.path.insert(0, backend)
    os.chdir(backend)

    from sqlalchemy import text

    from app.core.config import database_hostname_from_url, get_settings
    from app.core.database import engine

    settings = get_settings()
    host = database_hostname_from_url(settings.database_url)
    print(f"Connecting to host={host!r} (scheme postgresql+asyncpg) …")
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1
    print("OK: database connected (SELECT 1).")
    await engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
