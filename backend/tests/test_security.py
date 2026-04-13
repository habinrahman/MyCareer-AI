import pytest
from fastapi import HTTPException

from app.core.security import decode_supabase_access_token, user_id_from_payload


def test_user_id_from_payload_ok() -> None:
    assert user_id_from_payload({"sub": "user-1"}) == "user-1"


def test_user_id_from_payload_missing_sub() -> None:
    with pytest.raises(HTTPException) as exc:
        user_id_from_payload({})
    assert exc.value.status_code == 401


def test_decode_invalid_token() -> None:
    with pytest.raises(HTTPException) as exc:
        decode_supabase_access_token("not-a-jwt", "secret-value-12345")
    assert exc.value.status_code == 401
