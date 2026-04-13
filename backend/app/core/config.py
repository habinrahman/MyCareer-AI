from functools import lru_cache
import socket
from typing import Literal
from urllib.parse import urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AliasChoices, AnyUrl, Field, field_validator, model_validator


def normalize_database_url(value: str) -> str:
    """Normalize SQLAlchemy async PostgreSQL URLs for asyncpg."""
    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+asyncpg://", 1)
    if value.startswith("postgresql://") and "+asyncpg" not in value:
        return value.replace("postgresql://", "postgresql+asyncpg://", 1)
    return value


def database_hostname_from_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.hostname
    if not host:
        raise ValueError("DATABASE_URL must include a resolvable host (e.g. user:pass@host:5432/db).")
    return host


class Settings(BaseSettings):
    """
    Pydantic Settings: loads ``backend/.env`` (when CWD is the backend dir).

    Core DB/app fields among others: ``database_url``, ``database_ssl_cafile``,
    ``app_env`` (``APP_ENV`` / ``ENVIRONMENT``), ``debug``.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        # Allow constructing Settings(..., app_env="staging") as well as APP_ENV / ENVIRONMENT from the OS.
        populate_by_name=True,
    )

    app_name: str = "MyCareer AI API"
    app_env: Literal["development", "staging", "production"] = Field(
        default="development",
        validation_alias=AliasChoices("APP_ENV", "ENVIRONMENT"),
    )
    debug: bool = False

    log_auth_headers: bool = Field(
        default=False,
        validation_alias=AliasChoices("LOG_AUTH_HEADERS"),
        description="Log safe Authorization metadata (length + short prefix only).",
    )

    cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000"
    )
    log_level: str = "INFO"
    log_json: bool = Field(
        default=False,
        description="Emit one JSON object per line (better for log aggregators).",
    )
    request_id_header: str = "X-Request-ID"

    sentry_dsn: str | None = Field(
        default=None,
        description="If set, initialize Sentry for error monitoring.",
    )

    rate_limit_enabled: bool = False
    rate_limit_default: str = "120/minute"

    gzip_minimum_size: int = Field(default=512, ge=256, le=8192)
    response_cache_max_age_seconds: int = Field(
        default=0,
        ge=0,
        le=3600,
        description="If >0, add Cache-Control max-age for safe GET responses (e.g. 30). 0 disables.",
    )

    max_upload_bytes: int = Field(default=8_388_608, ge=1_048_576, le=50_000_000)

    openai_api_key: str = Field(..., min_length=10)
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_prompt_version: str = "v1"

    supabase_url: AnyUrl
    supabase_anon_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("SUPABASE_ANON_KEY", "NEXT_PUBLIC_SUPABASE_ANON_KEY"),
        description="Optional; browser uses anon key. Backend may read for future public endpoints.",
    )
    supabase_service_role_key: str = Field(..., min_length=20)
    supabase_jwt_secret: str = Field(..., min_length=10)
    supabase_resumes_bucket: str = "resumes"
    supabase_reports_bucket: str = "reports"
    supabase_signed_url_ttl_seconds: int = Field(default=3600, ge=60, le=86_400)
    public_app_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("PUBLIC_APP_URL", "NEXT_PUBLIC_APP_URL"),
        description=(
            "Public browser app base URL (no trailing slash), e.g. https://app.example.com. "
            "Used for PDF QR codes linking back to the product."
        ),
    )

    database_url: str = Field(
        ...,
        description="Async SQLAlchemy URL, e.g. postgresql+asyncpg://...",
    )
    database_ssl_required: bool = Field(
        default=True,
        description=(
            "When true (default), TLS is used for non-loopback DATABASE_URL hosts. "
            "Do not disable for Supabase."
        ),
    )
    database_ssl_verify_hostname: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "DATABASE_SSL_VERIFY_HOSTNAME",
            "DATABASE_SSL_VERIFY",
        ),
        description=(
            "TLS hostname verification (certificate CN/SAN vs. host). "
            "Alias env: DATABASE_SSL_VERIFY (same meaning). "
            "In development (APP_ENV=development), defaults to False; staging/production always verify hostname."
        ),
    )
    database_ssl_cafile: str | None = Field(
        default=None,
        description=(
            "Optional path to a PEM CA bundle. When set, it becomes the sole ``cafile`` passed to "
            "``ssl.create_default_context`` for Postgres (overrides the default certifi bundle). "
            "When unset and ``DATABASE_SSL_USE_CERTIFI`` is true, ``certifi.where()`` is used."
        ),
    )
    database_ssl_use_certifi: bool = Field(
        default=True,
        validation_alias=AliasChoices("DATABASE_SSL_USE_CERTIFI"),
        description=(
            "When true (default), merge Mozilla CA roots from the certifi bundle into the SSL context "
            "after ``ssl.create_default_context()`` (OS trust). Improves Supabase/public CA verification "
            "on minimal images or unusual Windows OpenSSL trust setups. Set false if you rely only on "
            "``DATABASE_SSL_CAFILE`` / OS store and certifi causes issues."
        ),
    )
    database_ssl_insecure_dev: bool = Field(
        default=False,
        validation_alias=AliasChoices("DATABASE_SSL_INSECURE", "DATABASE_SSL_INSECURE_DEV"),
        description=(
            "DEVELOPMENT ONLY (APP_ENV=development): set true to disable server certificate verification "
            "for Postgres (MITM risk). Ignored in staging/production. Prefer DATABASE_SSL_CAFILE when possible."
        ),
    )
    database_pool_size: int = Field(default=5, ge=1, le=50)
    database_max_overflow: int = Field(default=10, ge=0, le=50)
    database_pool_recycle: int = Field(default=1800, ge=60, le=86_400)
    database_pool_timeout: int = Field(default=30, ge=5, le=120)
    database_connect_timeout: float = Field(
        default=30.0,
        ge=5.0,
        le=120.0,
        description="Seconds to wait when opening a new TCP connection to Postgres (asyncpg).",
    )

    @field_validator("supabase_jwt_secret")
    @classmethod
    def strip_jwt_secret(cls, v: str) -> str:
        return v.strip()

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url_field(cls, v: str) -> str:
        return normalize_database_url(v)

    @field_validator("database_url")
    @classmethod
    def validate_database_url_format(cls, v: str) -> str:
        parsed = urlparse(v)
        if parsed.scheme != "postgresql+asyncpg":
            raise ValueError(
                "DATABASE_URL must use the asyncpg SQLAlchemy driver "
                "(scheme postgresql+asyncpg). Use postgres:// or postgresql:// and it will be normalized."
            )
        if not parsed.hostname:
            raise ValueError("DATABASE_URL must include a host (e.g. postgresql+asyncpg://user:pass@host:5432/dbname).")
        return v

    @model_validator(mode="after")
    def validate_database_host(self) -> "Settings":
        host = database_hostname_from_url(self.database_url)
        try:
            # Match dual-stack resolution behavior closer to asyncpg than gethostbyname (IPv4-only).
            socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        except OSError as exc:
            raise ValueError(
                f"Unable to resolve database host {host!r}. "
                "Check DATABASE_URL and network connectivity (DNS, VPN, firewall)."
            ) from exc
        return self

    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
