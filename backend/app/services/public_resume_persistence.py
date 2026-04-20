"""
Persist MicroDegree /public/analyze-resume runs to Supabase (optional).

The public UI uses ``POST /public/analyze-resume``, which does not send a JWT.
To mirror data into ``public.resumes`` and ``public.analyses`` (and optionally
``public.reports`` for PDF), set ``PUBLIC_RESUME_DB_OWNER_USER_ID`` to a UUID
that already exists in ``public.users`` (typically a dedicated service account
created via Supabase Auth + trigger).
"""

from __future__ import annotations

import logging
import uuid

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import Client

from app.core.config import Settings
from app.schemas.resume_analysis import ResumeAnalysisOutput
from app.services import database_repository, openai_service, persistence, supabase_storage
from app.services.resume_pipeline import upload_resume_file
from app.utils.exceptions import AppError
from app.utils.vectors import format_vector

logger = logging.getLogger(__name__)


async def persist_public_resume_analysis(
    session: AsyncSession,
    supabase: Client,
    settings: Settings,
    client: AsyncOpenAI,
    *,
    owner_user_id: str,
    filename: str,
    raw_bytes: bytes,
    content_type: str | None,
    text_body: str,
    nlp: ResumeAnalysisOutput,
) -> tuple[str, str]:
    """
    Upload bytes to Storage, insert ``resumes``, update parsed text, insert ``analyses``, commit.

    OpenAI embeddings for the persisted row are optional (see
    ``Settings.public_resume_persist_skip_embeddings``) to limit cost on public traffic.

    Returns ``(resume_id, analysis_id)`` as strings.
    """
    uid = owner_user_id.strip()
    try:
        uuid.UUID(uid)
    except ValueError as exc:
        raise AppError(
            "Invalid PUBLIC_RESUME_DB_OWNER_USER_ID (must be a UUID)",
            status_code=400,
        ) from exc

    upload_out = await upload_resume_file(
        session,
        supabase,
        settings,
        user_id=uid,
        filename=filename,
        content=raw_bytes,
        content_type=content_type,
    )
    resume_id = str(upload_out["resume_id"])
    logger.info(
        "public_resume.persist_resume_saved resume_id=%s owner=%s filename=%s",
        resume_id,
        uid,
        filename,
    )

    summary = nlp.professional_summary
    if settings.public_resume_persist_skip_embeddings:
        emb_str = None
        emb_analysis_str = None
    else:
        emb_resume = await openai_service.embed_text(
            client, settings.openai_embedding_model, text_body
        )
        emb_str = format_vector(emb_resume)
        emb_blob = summary + "\n" + "\n".join(nlp.strengths[:20])
        emb_analysis = await openai_service.embed_text(
            client, settings.openai_embedding_model, emb_blob
        )
        emb_analysis_str = format_vector(emb_analysis)

    findings = nlp.model_dump(mode="json")
    findings["_meta"] = {
        "parser": "pdf_docx_text",
        "nlp": "gpt_json_resume_analysis",
        "prompt_version": settings.openai_prompt_version,
        "source": "public_analyze_resume",
        "persist_embeddings_skipped": settings.public_resume_persist_skip_embeddings,
    }
    scores = {
        "resume_score": nlp.resume_score,
        "ats_score": nlp.ats_compatibility.score,
        "model": settings.openai_chat_model,
        "prompt_version": settings.openai_prompt_version,
    }

    try:
        version = await persistence.next_analysis_version(session, resume_id)
        await persistence.update_resume_parsed(
            session,
            resume_id=resume_id,
            parsed_text=text_body,
            embedding_str=emb_str,
            language=None,
        )
        analysis_id = await database_repository.create_analysis(
            session,
            user_id=uid,
            resume_id=resume_id,
            version=version,
            model=settings.openai_chat_model,
            prompt_version=settings.openai_prompt_version,
            summary=summary,
            findings=findings,
            scores=scores,
            embedding_str=emb_analysis_str,
        )
        await session.commit()
    except Exception:
        await session.rollback()
        try:
            await persistence.set_resume_failed(session, resume_id)
            await session.commit()
        except Exception:
            await session.rollback()
        raise

    logger.info(
        "public_resume.persist_analysis_saved analysis_id=%s resume_id=%s owner=%s v=%s",
        analysis_id,
        resume_id,
        uid,
        version,
    )
    return resume_id, analysis_id


async def persist_public_pdf_report(
    session: AsyncSession,
    supabase: Client,
    settings: Settings,
    *,
    owner_user_id: str,
    analysis_id: str,
    pdf_bytes: bytes,
) -> str | None:
    """Upload PDF to reports bucket and insert ``public.reports``. Returns report id or None."""
    uid = owner_user_id.strip()
    existing = await persistence.get_ready_report_id_for_analysis(
        session, user_id=uid, analysis_id=analysis_id
    )
    if existing:
        logger.info(
            "public_resume.persist_report_reused_existing report_id=%s analysis_id=%s",
            existing,
            analysis_id,
        )
        return existing

    path = f"{uid}/reports/analysis-{analysis_id[:8]}-{uuid.uuid4().hex}.pdf"
    try:
        await supabase_storage.upload_bytes(
            supabase,
            settings.supabase_reports_bucket,
            path,
            pdf_bytes,
            "application/pdf",
        )
        report_id = await database_repository.create_report(
            session,
            user_id=uid,
            analysis_id=analysis_id,
            title="MyCareer AI — Career intelligence report",
            report_type="resume_review",
            storage_path=path,
            status="ready",
            meta={"bytes": len(pdf_bytes), "source": "POST /public/analyze-resume?format=pdf"},
        )
        await session.commit()
    except Exception as exc:
        await session.rollback()
        logger.warning(
            "public_resume.persist_report_failed analysis_id=%s err=%s",
            analysis_id,
            exc,
            exc_info=True,
        )
        return None
    logger.info(
        "public_resume.persist_report_saved report_id=%s analysis_id=%s path=%s",
        report_id,
        analysis_id,
        path,
    )
    return report_id
