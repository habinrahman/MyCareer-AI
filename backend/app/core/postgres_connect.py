"""
Pure helpers for asyncpg TLS and connect_args (no SQLAlchemy engine).

Import this module from smoke scripts (e.g. ``test_db.py``) instead of ``database`` to avoid
creating the global engine and pulling asyncpg at import time.

TLS trust bundle: ``DATABASE_SSL_CAFILE`` if set, otherwise ``certifi.where()`` when
``DATABASE_SSL_USE_CERTIFI`` is true (default), matching ``ssl.create_default_context(cafile=...)``.
"""

from __future__ import annotations

import ssl
from urllib.parse import ParseResult, parse_qs, urlparse

import certifi

from app.core.config import Settings


def _is_loopback_postgres_host(hostname: str | None) -> bool:
    if not hostname:
        return False
    h = hostname.lower()
    return h in ("localhost", "127.0.0.1", "::1")


def _uses_supabase_transaction_pooler(parsed: ParseResult) -> bool:
    host = (parsed.hostname or "").lower()
    port = parsed.port or 5432
    if port == 6543:
        return True
    if "pooler.supabase.com" in host:
        return True
    qs = parse_qs(parsed.query)
    return qs.get("pgbouncer", [""])[0].lower() in ("true", "1", "yes")


def effective_database_ssl_verify_hostname(settings: Settings) -> bool:
    """Staging/production always verify TLS hostname; development follows settings."""
    if settings.app_env != "development":
        return True
    return settings.database_ssl_verify_hostname


def build_asyncpg_ssl_context(
    settings: Settings, *, verify_hostname: bool
) -> ssl.SSLContext:
    """
    SSL context compatible with Supabase (public PKI) on Windows, Docker, and cloud VMs.

    Uses ``ssl.create_default_context(..., cafile=...)`` where ``cafile`` is
    ``DATABASE_SSL_CAFILE`` when set, else ``certifi.where()`` when ``DATABASE_SSL_USE_CERTIFI``
    is true (default). If both are absent / certifi disabled, falls back to OS defaults only
    (no ``cafile`` argument).

    ``verify_hostname=False`` still uses ``CERT_REQUIRED``; only hostname matching is relaxed.

    In ``APP_ENV=development`` only, ``DATABASE_SSL_INSECURE=true`` disables certificate verification
    (MITM risk); ignored in staging/production.
    """
    if settings.app_env == "development" and settings.database_ssl_insecure_dev:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    custom = (settings.database_ssl_cafile or "").strip()
    if custom:
        cafile = custom
    elif settings.database_ssl_use_certifi:
        cafile = certifi.where()
    else:
        cafile = None

    if cafile is not None:
        ctx = ssl.create_default_context(
            purpose=ssl.Purpose.SERVER_AUTH,
            cafile=cafile,
        )
    else:
        ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    ctx.check_hostname = verify_hostname
    ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx


def build_asyncpg_connect_args(settings: Settings) -> dict:
    """asyncpg connect_args for SQLAlchemy; safe on Windows, Docker, and cloud VMs."""
    parsed = urlparse(settings.database_url)
    hostname = parsed.hostname
    args: dict = {}

    args["timeout"] = settings.database_connect_timeout

    if settings.database_ssl_required and not _is_loopback_postgres_host(hostname):
        verify_host = effective_database_ssl_verify_hostname(settings)
        args["ssl"] = build_asyncpg_ssl_context(
            settings, verify_hostname=verify_host
        )

    if _uses_supabase_transaction_pooler(parsed):
        args["statement_cache_size"] = 0

    return args
