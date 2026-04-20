"""
Optional persistence helpers (Async SQLAlchemy + Supabase Storage).

These use the same ``public.*`` tables as authenticated flows. They are intended
for internal or scripted use—not ``POST /public/analyze-resume``, which is stateless.

Tenant resolution: :mod:`app.services.user_service` (``DEFAULT_USER_ID`` / legacy env).
"""

from __future__ import annotations

import logging
from typing import Any

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import Client

from app.core.config import Settings
from app.schemas.resume_analysis import ResumeAnalysisOutput
from app.services import database_repository, user_service
from app.services.public_resume_persistence import (
    persist_public_pdf_report,
    persist_public_resume_analysis,
)
from app.services.resume_pipeline import upload_resume_file

logger = logging.getLogger(__name__)


def resolve_no_login_tenant_user_id(settings: Settings) -> str | None:
    """Backward-compatible alias for :func:`user_service.resolve_default_user_id`."""
    return user_service.resolve_default_user_id(settings)


async def save_resume_for_default_tenant(
    session: AsyncSession,
    supabase: Client,
    settings: Settings,
    *,
    filename: str,
    content: bytes,
    content_type: str | None,
) -> dict[str, Any]:
    """Upload to Storage and insert ``public.resumes`` (``upload_resume_file`` commits)."""
    tenant_id = user_service.get_default_user_id(settings)
    out = await upload_resume_file(
        session,
        supabase,
        settings,
        user_id=tenant_id,
        filename=filename,
        content=content,
        content_type=content_type,
    )
    logger.info(
        "database_service.resume_saved tenant=%s resume_id=%s",
        tenant_id,
        out.get("resume_id"),
    )
    return out


async def save_public_resume_analysis_bundle(
    session: AsyncSession,
    supabase: Client,
    settings: Settings,
    client: AsyncOpenAI,
    *,
    filename: str,
    raw_bytes: bytes,
    content_type: str | None,
    text_body: str,
    nlp: ResumeAnalysisOutput,
) -> tuple[str, str]:
    """Resume + parsed text + embeddings + ``public.analyses`` row. Returns (resume_id, analysis_id)."""
    tenant_id = user_service.get_default_user_id(settings)
    return await persist_public_resume_analysis(
        session,
        supabase,
        settings,
        client,
        owner_user_id=tenant_id,
        filename=filename,
        raw_bytes=raw_bytes,
        content_type=content_type,
        text_body=text_body,
        nlp=nlp,
    )


async def save_public_pdf_report_artifact(
    session: AsyncSession,
    supabase: Client,
    settings: Settings,
    *,
    analysis_id: str,
    pdf_bytes: bytes,
) -> str | None:
    """Upload PDF to reports bucket and insert ``public.reports``."""
    tenant_id = user_service.get_default_user_id(settings)
    return await persist_public_pdf_report(
        session,
        supabase,
        settings,
        owner_user_id=tenant_id,
        analysis_id=analysis_id,
        pdf_bytes=pdf_bytes,
    )


async def insert_download_lead(
    session: AsyncSession,
    *,
    full_name: str,
    email: str,
    phone: str,
    analysis_id: str | None = None,
) -> str:
    """Insert ``public.resume_download_leads``. Caller must ``commit``."""
    lead_id = await database_repository.create_lead(
        session,
        full_name=full_name,
        email=email,
        phone=phone,
        analysis_id=analysis_id,
    )
    logger.info("database_service.download_lead_inserted lead_id=%s email=%s", lead_id, email)
    return lead_id
