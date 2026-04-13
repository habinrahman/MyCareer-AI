"""Vector job matching: resume embedding vs ``job_postings.embedding`` (pgvector)."""

from __future__ import annotations

import logging

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.schemas.careers import JobMatchResponse, JobMatchRow
from app.services import careers_repository, openai_service
from app.utils.vectors import format_vector

logger = logging.getLogger(__name__)


async def _backfill_missing_job_embeddings(
    session: AsyncSession,
    client: AsyncOpenAI,
    settings: Settings,
) -> int:
    rows = await careers_repository.list_jobs_missing_embeddings(session, limit=48)
    n = 0
    for row in rows:
        blob = f"{row['title']}\n{row['description']}"
        vec = await openai_service.embed_text(client, settings.openai_embedding_model, blob)
        await careers_repository.set_job_embedding(
            session,
            job_id=str(row["id"]),
            embedding_str=format_vector(vec),
        )
        n += 1
    if n:
        await session.commit()
        logger.info("careers.jobs_embedded count=%s", n)
    return n


async def match_jobs_for_user(
    session: AsyncSession,
    client: AsyncOpenAI,
    settings: Settings,
    *,
    user_id: str,
    resume_id: str | None,
    limit: int,
    backfill_job_embeddings: bool,
) -> JobMatchResponse:
    notes: list[str] = []
    resume = await careers_repository.get_resume_for_match(
        session, user_id=user_id, resume_id=resume_id
    )
    if not resume:
        from app.utils.exceptions import AppError

        raise AppError(
            "No resume found for matching. Upload and analyze a resume first.",
            status_code=404,
        )

    if resume.get("parsing_status") != "ready":
        from app.utils.exceptions import AppError

        raise AppError("Resume is not ready for matching (parsing not complete).", status_code=400)

    parsed = (resume.get("parsed_text") or "").strip()
    if not parsed:
        from app.utils.exceptions import AppError

        raise AppError("Resume has no parsed text to embed.", status_code=400)

    emb_lit = resume.get("embedding_literal")
    query_source = "stored_resume_embedding"
    vec_str: str
    if emb_lit:
        vec_str = str(emb_lit)
    else:
        vec = await openai_service.embed_text(client, settings.openai_embedding_model, parsed[:120_000])
        vec_str = format_vector(vec)
        query_source = "runtime_resume_text_embedding"

    if backfill_job_embeddings:
        await _backfill_missing_job_embeddings(session, client, settings)

    matches_raw = await careers_repository.search_jobs_by_vector(
        session, query_vec=vec_str, limit=limit
    )
    fallback = False
    if not matches_raw:
        fallback = True
        notes.append("No job embeddings available yet; showing recent active postings without similarity.")
        recent = await careers_repository.list_active_jobs_recent(session, limit=limit)
        matches = [
            JobMatchRow(
                job_id=str(r["id"]),
                title=str(r["title"]),
                company_name=r.get("company_name"),
                location=r.get("location"),
                employment_type=r.get("employment_type"),
                industry=r.get("industry"),
                external_url=r.get("external_url"),
                similarity=None,
            )
            for r in recent
        ]
    else:
        matches = [
            JobMatchRow(
                job_id=str(r["id"]),
                title=str(r["title"]),
                company_name=r.get("company_name"),
                location=r.get("location"),
                employment_type=r.get("employment_type"),
                industry=r.get("industry"),
                external_url=r.get("external_url"),
                similarity=float(r["similarity"]) if r.get("similarity") is not None else None,
            )
            for r in matches_raw
        ]

    return JobMatchResponse(
        resume_id=str(resume["id"]),
        query_source=query_source,
        matches=matches,
        fallback_text_only=fallback,
        notes=notes,
    )
