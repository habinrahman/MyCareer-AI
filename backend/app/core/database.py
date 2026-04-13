"""
Async SQLAlchemy engine for PostgreSQL (Supabase).

``connect_args`` are built in ``app.core.postgres_connect`` (Step 3 style): TLS uses
``ssl.create_default_context(cafile=DATABASE_SSL_CAFILE or certifi.where())`` when the default
certifi path applies; ``statement_cache_size=0`` is set only for the Supabase transaction pooler
(port 6543 / pooler host / ``pgbouncer=true``), not for every connection.

Import ``postgres_connect`` from smoke scripts instead of this package to avoid creating the
global engine at import time.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

import certifi  # noqa: F401 — default CA bundle for Postgres TLS (see ``postgres_connect``)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, get_settings
from app.core.postgres_connect import (
    build_asyncpg_connect_args,
    build_asyncpg_ssl_context,
    effective_database_ssl_verify_hostname,
)

__all__ = [
    "AsyncSessionLocal",
    "build_asyncpg_connect_args",
    "build_asyncpg_ssl_context",
    "effective_database_ssl_verify_hostname",
    "engine",
    "get_db",
]

logger = logging.getLogger(__name__)


def _create_engine(settings: Settings):
    return create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_pre_ping=True,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_recycle=settings.database_pool_recycle,
        pool_timeout=settings.database_pool_timeout,
        connect_args=build_asyncpg_connect_args(settings),
    )


_settings = get_settings()
if _settings.app_env == "development" and _settings.database_ssl_insecure_dev:
    logger.warning(
        "DATABASE_SSL_INSECURE is enabled: Postgres TLS certificate verification is OFF. "
        "MITM risk. Remove for staging/production; use DATABASE_SSL_CAFILE when possible."
    )
engine = _create_engine(_settings)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a request-scoped session; rollback on errors; commits stay in route/service code.

    Do not wrap the injected session in ``async with session.begin()`` (or ``session.begin()``):
    SQLAlchemy **autobegin** starts a transaction on the first ``execute``; a nested ``begin()``
    raises ``InvalidRequestError: A transaction is already begun on this Session``.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
