"""
Application repository: DB writes/reads with structured logging.

Transaction rule: callers own ``await session.commit()`` / ``rollback()`` (same as
``persistence``). Do not nest ``session.begin()`` for sessions from ``get_db``.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import persistence

logger = logging.getLogger(__name__)


async def ensure_user(session: AsyncSession, user_id: str) -> None:
    await persistence.ensure_user_row(session, user_id)


async def create_resume(
    session: AsyncSession,
    *,
    user_id: str,
    original_filename: str,
    mime_type: str | None,
    file_size_bytes: int,
    storage_path: str,
    meta: dict[str, Any],
) -> str:
    # ``insert_resume_row`` is an upsert (ON CONFLICT) — idempotent per user + storage_path.
    rid = await persistence.insert_resume_row(
        session,
        user_id=user_id,
        original_filename=original_filename,
        mime_type=mime_type,
        file_size_bytes=file_size_bytes,
        storage_path=storage_path,
        meta=meta,
    )
    logger.info("db.resume_upserted resume_id=%s user=%s path=%s", rid, user_id, storage_path)
    return rid


async def create_analysis(
    session: AsyncSession,
    *,
    user_id: str,
    resume_id: str,
    version: int,
    model: str,
    prompt_version: str,
    summary: str,
    findings: dict[str, Any],
    scores: dict[str, Any],
    embedding_str: str | None,
) -> str:
    aid = await persistence.insert_analysis(
        session,
        user_id=user_id,
        resume_id=resume_id,
        version=version,
        model=model,
        prompt_version=prompt_version,
        summary=summary,
        findings=findings,
        scores=scores,
        embedding_str=embedding_str,
    )
    logger.info(
        "db.analysis_upserted analysis_id=%s user=%s resume=%s v=%s",
        aid,
        user_id,
        resume_id,
        version,
    )
    return aid


async def create_report(
    session: AsyncSession,
    *,
    user_id: str,
    analysis_id: str | None,
    title: str,
    report_type: str,
    storage_path: str | None,
    status: str,
    meta: dict[str, Any] | None = None,
) -> str:
    # With ``analysis_id``, ``insert_report_row`` upserts on ``analysis_id`` (one PDF row per analysis).
    rid = await persistence.insert_report_row(
        session,
        user_id=user_id,
        analysis_id=analysis_id,
        title=title,
        report_type=report_type,
        storage_path=storage_path,
        status=status,
        meta=meta,
    )
    logger.info(
        "db.report_upserted report_id=%s user=%s analysis=%s path=%s",
        rid,
        user_id,
        analysis_id,
        storage_path,
    )
    return rid


async def create_lead(
    session: AsyncSession,
    *,
    full_name: str,
    email: str,
    phone: str,
    analysis_id: str | None,
) -> str:
    lead_id = await persistence.insert_resume_download_lead(
        session,
        full_name=full_name,
        email=email,
        phone=phone,
        analysis_id=analysis_id,
    )
    logger.info("db.lead_created lead_id=%s email=%s analysis_id=%s", lead_id, email, analysis_id)
    return lead_id


async def get_analysis_by_id(
    session: AsyncSession,
    *,
    analysis_id: str,
    user_id: str,
) -> dict[str, Any] | None:
    return await persistence.get_analysis_owned(
        session, analysis_id=analysis_id, user_id=user_id
    )


async def get_report_by_id(
    session: AsyncSession,
    *,
    report_id: str,
    user_id: str,
) -> dict[str, Any] | None:
    return await persistence.get_report_owned(
        session, report_id=report_id, user_id=user_id
    )
