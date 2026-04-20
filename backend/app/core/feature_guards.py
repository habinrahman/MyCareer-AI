"""Feature flags for V1 MVP vs full product; use as FastAPI dependencies."""

from fastapi import Depends, HTTPException, status

from app.core.config import Settings
from app.core.dependencies import get_settings_dep


def _service_unavailable(detail: str) -> HTTPException:
    return HTTPException(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=detail,
    )


def require_public_resume_review(settings: Settings = Depends(get_settings_dep)) -> None:
    if not settings.public_resume_review_enabled:
        raise _service_unavailable("Public resume review is disabled for this deployment.")


def require_chat_enabled(settings: Settings = Depends(get_settings_dep)) -> None:
    if not settings.enable_chat:
        raise _service_unavailable("AI mentor chat is disabled for this deployment.")


def require_reports_enabled(settings: Settings = Depends(get_settings_dep)) -> None:
    if not settings.enable_reports:
        raise _service_unavailable("Reports are disabled for this deployment.")


def require_benchmarking_enabled(settings: Settings = Depends(get_settings_dep)) -> None:
    if not settings.enable_benchmarking:
        raise _service_unavailable("Industry benchmarking is disabled for this deployment.")


def require_job_matching_enabled(settings: Settings = Depends(get_settings_dep)) -> None:
    if not settings.enable_job_matching:
        raise _service_unavailable("Job matching is disabled for this deployment.")


def require_career_profile_enabled(settings: Settings = Depends(get_settings_dep)) -> None:
    """Career profile (/careers/me) when any careers-area feature is enabled."""
    if not (
        settings.enable_benchmarking
        or settings.enable_job_matching
        or settings.enable_recruiter_mode
    ):
        raise _service_unavailable("Career profiles are disabled for this deployment.")
