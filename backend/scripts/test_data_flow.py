#!/usr/bin/env python3
"""
Smoke-check that core Supabase tables exist and are readable.

Does not mutate data unless ``--write-sample`` is passed (inserts one lead row).

Usage (from ``backend/`` with venv, valid DATABASE_URL):

    python scripts/test_data_flow.py
    python scripts/test_data_flow.py --write-sample
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid


def _backend_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


TABLES = (
    "public.resumes",
    "public.analyses",
    "public.reports",
    "public.resume_download_leads",
    "public.industry_benchmarks",
)


async def main() -> int:
    backend = _backend_dir()
    if backend not in sys.path:
        sys.path.insert(0, backend)
    os.chdir(backend)

    from sqlalchemy import text

    from app.core.database import AsyncSessionLocal

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write-sample",
        action="store_true",
        help="Insert a disposable resume_download_leads row (for manual Supabase verification).",
    )
    args = parser.parse_args()

    async with AsyncSessionLocal() as session:
        for fq in TABLES:
            schema, name = fq.split(".")
            try:
                await session.execute(text(f'SELECT 1 FROM {schema}."{name}" LIMIT 1'))
            except Exception as exc:
                print(f"MISSING or unreadable {fq}: {exc}")
                await session.rollback()
                return 1
            print(f"OK read {fq}")
        if args.write_sample:
            email = f"smoke-{uuid.uuid4().hex[:10]}@example.com"
            await session.execute(
                text(
                    """
                    INSERT INTO public.resume_download_leads
                      (full_name, email, phone, analysis_id)
                    VALUES
                      ('Smoke Test', :email, '+10000000000', NULL)
                    """
                ),
                {"email": email},
            )
            await session.commit()
            print(f"Inserted sample lead email={email} (delete from dashboard if desired).")
        else:
            await session.rollback()

    print("All table probes succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
