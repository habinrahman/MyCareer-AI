import logging

from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["120/minute"],
    headers_enabled=True,
)


def apply_rate_limit_settings(*, enabled: bool, default_limit: str) -> None:
    limiter.enabled = enabled
    if default_limit:
        limiter._default_limits = [default_limit]  # noqa: SLF001
    logger.info(
        "rate_limit configured enabled=%s default=%s",
        enabled,
        default_limit,
    )
