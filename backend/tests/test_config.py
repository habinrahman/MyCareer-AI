from app.core.config import Settings, normalize_database_url


def test_normalize_postgres_scheme_to_asyncpg() -> None:
    assert "asyncpg" in normalize_database_url("postgres://user:pw@localhost:5432/db")


def test_normalize_postgresql_adds_asyncpg_driver() -> None:
    out = normalize_database_url("postgresql://localhost/db")
    assert "+asyncpg" in out


def test_cors_origin_list_splits_comma(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    s = Settings(
        openai_api_key="sk-" + "x" * 40,
        supabase_url="https://x.supabase.co",
        supabase_service_role_key="x" * 40,
        supabase_jwt_secret="jwt-secret-12345",
        database_url="postgresql+asyncpg://localhost/db",
        cors_origins="http://a.com, http://b.com ",
    )
    assert s.cors_origin_list() == ["http://a.com", "http://b.com"]


def test_cors_origin_list_merges_localhost_in_development(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    s = Settings(
        openai_api_key="sk-" + "x" * 40,
        supabase_url="https://x.supabase.co",
        supabase_service_role_key="x" * 40,
        supabase_jwt_secret="jwt-secret-12345",
        database_url="postgresql+asyncpg://localhost/db",
        cors_origins="http://custom.test:4000",
    )
    out = s.cors_origin_list()
    assert "http://custom.test:4000" in out
    assert "http://localhost:3000" in out
    assert "http://127.0.0.1:3000" in out
