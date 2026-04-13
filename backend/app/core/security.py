import logging
from functools import lru_cache
from typing import Annotated

import jwt as pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt as jose_jwt
from jwt import PyJWKClient, PyJWKClientError, PyJWTError

logger = logging.getLogger(__name__)

http_bearer = HTTPBearer(auto_error=False)

SUPABASE_JWT_ALGORITHMS = ("HS256",)

_DEFAULT_JOSE_OPTIONS: dict = {
    "verify_signature": True,
    "verify_exp": True,
    "verify_aud": True,
    "verify_iss": True,
    "leeway": 60,
}


def _auth_logging_enabled() -> bool:
    try:
        from app.core.config import get_settings

        s = get_settings()
        return bool(s.debug or s.log_auth_headers)
    except Exception:
        return False


def get_bearer_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(http_bearer),
    ],
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        if _auth_logging_enabled():
            logger.debug(
                "auth.missing_bearer scheme=%r",
                getattr(credentials, "scheme", None) if credentials else None,
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization Bearer token",
        )
    token = credentials.credentials.strip()
    if not token:
        if _auth_logging_enabled():
            logger.debug("auth.empty_bearer_credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization Bearer token",
        )
    if _auth_logging_enabled():
        logger.debug(
            "auth.authorization bearer_len=%s prefix=%s…",
            len(token),
            token[:16],
        )
    return token


def _unverified_alg(token: str) -> str | None:
    try:
        return jose_jwt.get_unverified_header(token).get("alg")
    except Exception:
        return None


@lru_cache(maxsize=4)
def _jwks_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url)


def _decode_hs256_jose(token: str, secret: str) -> dict:
    try:
        return jose_jwt.decode(
            token,
            secret,
            algorithms=list(SUPABASE_JWT_ALGORITHMS),
            audience="authenticated",
            options=_DEFAULT_JOSE_OPTIONS,
        )
    except JWTError as first_exc:
        try:
            return jose_jwt.decode(
                token,
                secret,
                algorithms=list(SUPABASE_JWT_ALGORITHMS),
                audience=None,
                options={**_DEFAULT_JOSE_OPTIONS, "verify_aud": False},
            )
        except JWTError:
            if _auth_logging_enabled():
                logger.debug(
                    "auth.hs256_jose_failed kind=%s",
                    type(first_exc).__name__,
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            ) from first_exc


def _decode_asymmetric_supabase_jwks(token: str) -> dict:
    from app.core.config import get_settings

    base = str(get_settings().supabase_url).rstrip("/")
    jwks_url = f"{base}/auth/v1/.well-known/jwks.json"
    try:
        client = _jwks_client(jwks_url)
        signing_key = client.get_signing_key_from_jwt(token)
        header = jose_jwt.get_unverified_header(token)
        alg = header.get("alg") or "RS256"
        return pyjwt.decode(
            token,
            signing_key.key,
            algorithms=[alg],
            audience="authenticated",
            leeway=60,
            options={"verify_signature": True, "verify_exp": True, "verify_aud": True},
        )
    except (PyJWTError, PyJWKClientError, ValueError, KeyError, TypeError) as exc:
        if _auth_logging_enabled():
            logger.debug("auth.jwks_decode_failed kind=%s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc


def decode_supabase_access_token(token: str, jwt_secret: str) -> dict:
    """
    Supabase access tokens may be HS256 (JWT secret) or asymmetric (JWKS).
    """
    secret = jwt_secret.strip()
    alg = _unverified_alg(token) or "HS256"

    if alg == "HS256":
        return _decode_hs256_jose(token, secret)

    if alg and (
        alg.startswith("RS")
        or alg.startswith("ES")
        or alg.startswith("PS")
        or alg == "EdDSA"
    ):
        return _decode_asymmetric_supabase_jwks(token)

    if _auth_logging_enabled():
        logger.debug("auth.unsupported_jwt_alg=%s", alg)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Unsupported token algorithm: {alg}",
    )


def get_current_user(token: str = Depends(get_bearer_token)) -> dict:
    from app.core.config import get_settings

    return decode_supabase_access_token(token, get_settings().supabase_jwt_secret)


def user_id_from_payload(payload: dict) -> str:
    sub = payload.get("sub")
    if not sub or not isinstance(sub, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
        )
    return sub
