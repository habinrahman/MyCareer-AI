import uuid

import pytest

from app.core.config import Settings
from app.services import user_service


def test_resolve_default_user_id_prefers_default_over_legacy() -> None:
    uid = str(uuid.uuid4())
    legacy = str(uuid.uuid4())
    s = Settings.model_construct(
        default_user_id=uid,
        public_resume_db_owner_user_id=legacy,
    )
    assert user_service.resolve_default_user_id(s) == uid


def test_resolve_default_user_id_falls_back_to_legacy() -> None:
    legacy = str(uuid.uuid4())
    s = Settings.model_construct(
        default_user_id=None,
        public_resume_db_owner_user_id=legacy,
    )
    assert user_service.resolve_default_user_id(s) == legacy


def test_get_default_user_id_raises_when_unset() -> None:
    s = Settings.model_construct(
        default_user_id=None,
        public_resume_db_owner_user_id=None,
    )
    with pytest.raises(ValueError, match="DEFAULT_USER_ID"):
        user_service.get_default_user_id(s)


def test_get_default_user_id_rejects_non_uuid() -> None:
    s = Settings.model_construct(
        default_user_id="not-a-uuid",
        public_resume_db_owner_user_id=None,
    )
    with pytest.raises(ValueError, match="valid UUID"):
        user_service.get_default_user_id(s)
