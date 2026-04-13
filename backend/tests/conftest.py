"""
Pytest loads this module before tests: set required env vars before importing the app.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# --- Required Settings (dummy values for import-time engine creation) ---
os.environ.setdefault(
    "OPENAI_API_KEY",
    "sk-test-" + "x" * 40,
)
os.environ.setdefault("SUPABASE_URL", "https://test-project.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "x" * 40)
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret-at-least-10")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://user:pass@127.0.0.1:6543/postgres",
)

from app.core.config import get_settings  # noqa: E402
from app.core.database import get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def mock_db_session() -> AsyncMock:
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock(return_value=MagicMock())
    return session


@pytest.fixture
def client(mock_db_session: AsyncMock):
    async def _override_db() -> AsyncGenerator[AsyncMock, None]:
        yield mock_db_session

    app.dependency_overrides[get_db] = _override_db
    from fastapi.testclient import TestClient

    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()
