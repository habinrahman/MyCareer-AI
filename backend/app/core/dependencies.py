from functools import lru_cache

from fastapi import Depends
from openai import AsyncOpenAI
from supabase import Client, create_client

from app.core.config import Settings, get_settings
from app.core.database import get_db  # noqa: F401 (re-exported for route modules)
from app.core.security import get_current_user, user_id_from_payload


def get_settings_dep() -> Settings:
    return get_settings()


@lru_cache
def _openai_client(api_key: str) -> AsyncOpenAI:
    return AsyncOpenAI(api_key=api_key)


def get_openai_client(settings: Settings = Depends(get_settings_dep)) -> AsyncOpenAI:
    return _openai_client(settings.openai_api_key)


@lru_cache
def _supabase_client(url: str, service_key: str) -> Client:
    return create_client(url, service_key)


def get_supabase_client(settings: Settings = Depends(get_settings_dep)) -> Client:
    return _supabase_client(str(settings.supabase_url), settings.supabase_service_role_key)


def get_current_user_id(payload: dict = Depends(get_current_user)) -> str:
    return user_id_from_payload(payload)
