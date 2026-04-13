"""Read/write helpers for careers module (benchmarks and job matching)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def list_industry_benchmarks(
    session: AsyncSession,
    *,
    industry: str | None,
    role_family: str | None,
    metric_name: str = "resume_score",
) -> list[dict[str, Any]]:
    clauses = ["metric_name = :metric"]
    params: dict[str, Any] = {"metric": metric_name}
    if industry:
        clauses.append("(industry = :ind OR industry = 'all')")
        params["ind"] = industry
    if role_family:
        clauses.append("role_family = :rf")
        params["rf"] = role_family
    where = " AND ".join(clauses)
    result = await session.execute(
        text(
            f"""
            SELECT
              id::text, industry, role_family, metric_name,
              p25, p50, p75, sample_size, source, notes
            FROM public.industry_benchmarks
            WHERE {where}
            ORDER BY industry DESC NULLS LAST, role_family
            """
        ),
        params,
    )
    return [dict(r) for r in result.mappings().fetchall()]


async def get_latest_analysis_row(
    session: AsyncSession,
    *,
    user_id: str,
    resume_id: str | None,
) -> dict[str, Any] | None:
    rid_clause = "AND resume_id = CAST(:rid AS uuid)" if resume_id else ""
    params: dict[str, Any] = {"uid": user_id}
    if resume_id:
        params["rid"] = resume_id
    result = await session.execute(
        text(
            f"""
            SELECT id::text, resume_id::text, scores, findings, summary, created_at
            FROM public.analyses
            WHERE user_id = CAST(:uid AS uuid)
            {rid_clause}
            ORDER BY created_at DESC
            LIMIT 1
            """
        ),
        params,
    )
    row = result.mappings().fetchone()
    return dict(row) if row else None


async def get_resume_for_match(
    session: AsyncSession,
    *,
    user_id: str,
    resume_id: str | None,
) -> dict[str, Any] | None:
    if resume_id:
        result = await session.execute(
            text(
                """
                SELECT
                  id::text,
                  parsed_text,
                  parsing_status,
                  CASE WHEN embedding IS NULL THEN NULL ELSE embedding::text END AS embedding_literal
                FROM public.resumes
                WHERE id = CAST(:rid AS uuid) AND user_id = CAST(:uid AS uuid)
                """
            ),
            {"rid": resume_id, "uid": user_id},
        )
    else:
        result = await session.execute(
            text(
                """
                SELECT
                  id::text,
                  parsed_text,
                  parsing_status,
                  CASE WHEN embedding IS NULL THEN NULL ELSE embedding::text END AS embedding_literal
                FROM public.resumes
                WHERE user_id = CAST(:uid AS uuid)
                  AND parsing_status = 'ready'
                ORDER BY created_at DESC
                LIMIT 1
                """
            ),
            {"uid": user_id},
        )
    row = result.mappings().fetchone()
    return dict(row) if row else None


async def list_jobs_missing_embeddings(
    session: AsyncSession,
    *,
    limit: int = 32,
) -> list[dict[str, Any]]:
    result = await session.execute(
        text(
            """
            SELECT id::text, title, description
            FROM public.job_postings
            WHERE is_active AND embedding IS NULL
            ORDER BY created_at ASC
            LIMIT :lim
            """
        ),
        {"lim": limit},
    )
    return [dict(r) for r in result.mappings().fetchall()]


async def set_job_embedding(
    session: AsyncSession,
    *,
    job_id: str,
    embedding_str: str,
) -> None:
    await session.execute(
        text(
            """
            UPDATE public.job_postings
            SET embedding = CAST(:emb AS vector), updated_at = now()
            WHERE id = CAST(:jid AS uuid)
            """
        ),
        {"emb": embedding_str, "jid": job_id},
    )


async def search_jobs_by_vector(
    session: AsyncSession,
    *,
    query_vec: str,
    limit: int,
) -> list[dict[str, Any]]:
    result = await session.execute(
        text(
            """
            SELECT
              j.id::text,
              j.title,
              j.company_name,
              j.location,
              j.employment_type,
              j.industry,
              j.external_url,
              (1 - (j.embedding <=> CAST(:qv AS vector)))::float AS similarity
            FROM public.job_postings j
            WHERE j.is_active AND j.embedding IS NOT NULL
            ORDER BY j.embedding <=> CAST(:qv AS vector)
            LIMIT :lim
            """
        ),
        {"qv": query_vec, "lim": limit},
    )
    return [dict(r) for r in result.mappings().fetchall()]


async def list_active_jobs_recent(
    session: AsyncSession,
    *,
    limit: int,
) -> list[dict[str, Any]]:
    result = await session.execute(
        text(
            """
            SELECT
              j.id::text,
              j.title,
              j.company_name,
              j.location,
              j.employment_type,
              j.industry,
              j.external_url
            FROM public.job_postings j
            WHERE j.is_active
            ORDER BY j.created_at DESC
            LIMIT :lim
            """
        ),
        {"lim": limit},
    )
    return [dict(r) for r in result.mappings().fetchall()]
