"""Async Postgres connect_args (TLS + Supabase pooler) built from Settings."""

import ssl

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.database import build_asyncpg_connect_args


@pytest.fixture(autouse=True)
def _clear_database_ssl_insecure_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Constructor kwargs must win; still clear env so local .env cannot flip tests."""
    monkeypatch.delenv("DATABASE_SSL_INSECURE", raising=False)
    monkeypatch.delenv("DATABASE_SSL_INSECURE_DEV", raising=False)


def _settings(**kwargs: object) -> Settings:
    # pydantic-settings honors validation_alias on init: use APP_ENV / ENVIRONMENT, not app_env.
    if "app_env" in kwargs:
        kwargs["APP_ENV"] = kwargs.pop("app_env")
    base: dict[str, object] = {
        "openai_api_key": "sk-" + "x" * 40,
        "supabase_url": "https://x.supabase.co",
        "supabase_service_role_key": "x" * 40,
        "supabase_jwt_secret": "jwt-secret-12345",
        "database_url": "postgresql+asyncpg://user:pass@127.0.0.1:5432/postgres",
        # Use env alias so this wins over backend/.env (pydantic-settings + AliasChoices).
        "DATABASE_SSL_INSECURE": False,
    }
    base.update(kwargs)
    return Settings(**base)


def test_loopback_url_omits_explicit_ssl_context() -> None:
    args = build_asyncpg_connect_args(_settings())
    assert "ssl" not in args
    assert "timeout" in args


def test_remote_host_uses_tls_context() -> None:
    # example.com resolves publicly; satisfies Settings DNS validation.
    s = _settings(
        database_url="postgresql+asyncpg://user:pass@example.com:5432/postgres",
    )
    args = build_asyncpg_connect_args(s)
    assert "ssl" in args
    assert args["timeout"] == 30.0


def test_remote_host_omits_ssl_when_database_ssl_required_false() -> None:
    s = _settings(
        database_url="postgresql+asyncpg://user:pass@example.com:5432/postgres",
        database_ssl_required=False,
    )
    args = build_asyncpg_connect_args(s)
    assert "ssl" not in args


def test_transaction_pooler_sets_statement_cache_off() -> None:
    s = _settings(
        database_url="postgresql+asyncpg://user:pass@example.com:6543/postgres",
    )
    args = build_asyncpg_connect_args(s)
    assert args.get("statement_cache_size") == 0


def test_pgbouncer_query_sets_statement_cache_off() -> None:
    s = _settings(
        database_url=(
            "postgresql+asyncpg://user:pass@example.com:5432/postgres?pgbouncer=true"
        ),
    )
    args = build_asyncpg_connect_args(s)
    assert args.get("statement_cache_size") == 0


def test_staging_always_verifies_tls_hostname_even_if_flag_false() -> None:
    s = _settings(
        app_env="staging",
        database_ssl_verify_hostname=False,
        database_url="postgresql+asyncpg://user:pass@example.com:5432/postgres",
    )
    ctx = build_asyncpg_connect_args(s)["ssl"]
    assert ctx.check_hostname is True


def test_development_relaxes_tls_hostname_by_default() -> None:
    s = _settings(
        app_env="development",
        database_ssl_verify_hostname=False,
        database_url="postgresql+asyncpg://user:pass@example.com:5432/postgres",
    )
    ctx = build_asyncpg_connect_args(s)["ssl"]
    assert ctx.check_hostname is False
    assert ctx.verify_mode == ssl.CERT_REQUIRED


def test_development_can_enable_tls_hostname_verification() -> None:
    s = _settings(
        app_env="development",
        database_ssl_verify_hostname=True,
        database_url="postgresql+asyncpg://user:pass@example.com:5432/postgres",
    )
    ctx = build_asyncpg_connect_args(s)["ssl"]
    assert ctx.check_hostname is True


def test_ssl_can_use_os_trust_store_without_certifi() -> None:
    s = _settings(
        database_url="postgresql+asyncpg://user:pass@example.com:5432/postgres",
        database_ssl_use_certifi=False,
        database_ssl_cafile=None,
    )
    ctx = build_asyncpg_connect_args(s)["ssl"]
    assert ctx.verify_mode == ssl.CERT_REQUIRED


def test_ssl_can_merge_certifi_when_enabled() -> None:
    s = _settings(
        database_url="postgresql+asyncpg://user:pass@example.com:5432/postgres",
        database_ssl_use_certifi=True,
        database_ssl_cafile=None,
    )
    ctx = build_asyncpg_connect_args(s)["ssl"]
    assert ctx.verify_mode == ssl.CERT_REQUIRED


def test_ssl_custom_cafile_or_certifi_bundle() -> None:
    import certifi

    s = _settings(
        database_url="postgresql+asyncpg://user:pass@example.com:5432/postgres",
        database_ssl_cafile=certifi.where(),
        database_ssl_use_certifi=True,
    )
    ctx = build_asyncpg_connect_args(s)["ssl"]
    assert ctx.verify_mode == ssl.CERT_REQUIRED


def test_development_ssl_insecure_disables_cert_verify() -> None:
    s = _settings(
        app_env="development",
        DATABASE_SSL_INSECURE=True,
        database_url="postgresql+asyncpg://user:pass@example.com:5432/postgres",
    )
    ctx = build_asyncpg_connect_args(s)["ssl"]
    assert ctx.verify_mode == ssl.CERT_NONE
    assert ctx.check_hostname is False


def test_staging_ignores_ssl_insecure_flag() -> None:
    s = _settings(
        app_env="staging",
        DATABASE_SSL_INSECURE=True,
        database_url="postgresql+asyncpg://user:pass@example.com:5432/postgres",
    )
    ctx = build_asyncpg_connect_args(s)["ssl"]
    assert ctx.verify_mode == ssl.CERT_REQUIRED


def test_database_url_rejects_non_asyncpg_scheme_after_normalize() -> None:
    with pytest.raises(ValidationError):
        Settings(
            openai_api_key="sk-" + "x" * 40,
            supabase_url="https://x.supabase.co",
            supabase_service_role_key="x" * 40,
            supabase_jwt_secret="jwt-secret-12345",
            database_url="mysql+asyncmy://user:pass@localhost/db",
        )
