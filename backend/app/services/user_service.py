"""
Legacy service-tenant UUID resolution (``DEFAULT_USER_ID`` / legacy env).

Used by optional ``database_service`` persistence helpers only—not by the stateless
``POST /public/analyze-resume`` route. Uses :class:`app.core.config.Settings`.
"""

from __future__ import annotations

import uuid

from app.core.config import Settings, get_settings


def resolve_default_user_id(settings: Settings | None = None) -> str | None:
    """
    Return the configured legacy service UUID, if any.

    ``DEFAULT_USER_ID`` takes precedence over ``PUBLIC_RESUME_DB_OWNER_USER_ID``.
    """
    s = settings if settings is not None else get_settings()
    return s.no_login_tenant_user_id()


def get_default_user_id(settings: Settings | None = None) -> str:
    """
    Require a legacy service UUID for callers that use ``database_service`` helpers.

    Raises:
        ValueError: If neither ``DEFAULT_USER_ID`` nor legacy
            ``PUBLIC_RESUME_DB_OWNER_USER_ID`` is set, or the value is not a UUID.
    """
    uid = resolve_default_user_id(settings)
    if not uid:
        raise ValueError(
            "DEFAULT_USER_ID is not configured. Set it to a UUID in public.users when using "
            "database_service public-persist helpers. "
            "Legacy: PUBLIC_RESUME_DB_OWNER_USER_ID is accepted if DEFAULT_USER_ID is unset."
        )
    try:
        uuid.UUID(uid.strip())
    except ValueError as exc:
        raise ValueError(
            "DEFAULT_USER_ID (or PUBLIC_RESUME_DB_OWNER_USER_ID) must be a valid UUID"
        ) from exc
    return uid.strip()
