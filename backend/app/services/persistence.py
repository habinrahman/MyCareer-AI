"""
DB helpers using raw SQL via ``AsyncSession.execute``.

Transaction boundaries: callers own ``commit`` / ``rollback``. Do not use
``async with session.begin()`` here or in services for sessions injected from
``get_db`` — autobegin already manages the transaction.
"""

import json
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def get_user_pdf_profile(
    session: AsyncSession, *, user_id: str
) -> dict[str, Any]:
    """Display name, email, and optional social URLs from ``public.users`` for PDF cover."""
    result = await session.execute(
        text(
            """
            SELECT display_name, email, preferences
            FROM public.users
            WHERE id = CAST(:uid AS uuid)
            """
        ),
        {"uid": user_id},
    )
    row = result.mappings().fetchone()
    if not row:
        return {
            "display_name": None,
            "email": None,
            "linkedin_url": None,
            "github_url": None,
        }
    prefs = row.get("preferences") or {}
    if isinstance(prefs, str):
        try:
            prefs = json.loads(prefs)
        except json.JSONDecodeError:
            prefs = {}
    if not isinstance(prefs, dict):
        prefs = {}
    li = prefs.get("linkedin_url") or prefs.get("linkedin") or ""
    gh = prefs.get("github_url") or prefs.get("github") or ""
    return {
        "display_name": row.get("display_name"),
        "email": row.get("email"),
        "linkedin_url": str(li).strip() if li else None,
        "github_url": str(gh).strip() if gh else None,
    }


async def ensure_user_row(session: AsyncSession, user_id: str) -> None:
    await session.execute(
        text(
            """
            INSERT INTO public.users (id)
            VALUES (CAST(:id AS uuid))
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {"id": user_id},
    )


async def insert_resume_row(
    session: AsyncSession,
    *,
    user_id: str,
    original_filename: str,
    mime_type: str | None,
    file_size_bytes: int,
    storage_path: str,
    meta: dict[str, Any],
) -> str:
    result = await session.execute(
        text(
            """
            INSERT INTO public.resumes (
                user_id, original_filename, mime_type, file_size_bytes,
                storage_path, parsing_status, meta
            )
            VALUES (
                CAST(:user_id AS uuid),
                :filename,
                :mime,
                :size,
                :path,
                'pending',
                CAST(:meta AS jsonb)
            )
            RETURNING id::text
            """
        ),
        {
            "user_id": user_id,
            "filename": original_filename,
            "mime": mime_type,
            "size": file_size_bytes,
            "path": storage_path,
            "meta": json.dumps(meta),
        },
    )
    row = result.fetchone()
    if not row or row[0] is None:
        raise RuntimeError("insert_resume_row failed")
    return str(row[0])


async def get_resume_owned(
    session: AsyncSession,
    *,
    resume_id: str,
    user_id: str,
) -> dict[str, Any] | None:
    result = await session.execute(
        text(
            """
            SELECT
                id::text, user_id::text, original_filename, mime_type,
                file_size_bytes, storage_path, parsing_status, parsed_text
            FROM public.resumes
            WHERE id = CAST(:rid AS uuid) AND user_id = CAST(:uid AS uuid)
            """
        ),
        {"rid": resume_id, "uid": user_id},
    )
    row = result.mappings().fetchone()
    return dict(row) if row else None


async def set_resume_processing(session: AsyncSession, resume_id: str) -> None:
    await session.execute(
        text(
            """
            UPDATE public.resumes
            SET parsing_status = 'processing', updated_at = now()
            WHERE id = CAST(:rid AS uuid)
            """
        ),
        {"rid": resume_id},
    )


async def update_resume_parsed(
    session: AsyncSession,
    *,
    resume_id: str,
    parsed_text: str,
    embedding_str: str,
    language: str | None,
) -> None:
    await session.execute(
        text(
            """
            UPDATE public.resumes
            SET
                parsed_text = :text,
                parsing_status = 'ready',
                embedding = CAST(:emb AS vector),
                language = COALESCE(:lang, language),
                updated_at = now()
            WHERE id = CAST(:rid AS uuid)
            """
        ),
        {"text": parsed_text, "emb": embedding_str, "lang": language, "rid": resume_id},
    )


async def set_resume_failed(session: AsyncSession, resume_id: str) -> None:
    await session.execute(
        text(
            """
            UPDATE public.resumes
            SET parsing_status = 'failed', updated_at = now()
            WHERE id = CAST(:rid AS uuid)
            """
        ),
        {"rid": resume_id},
    )


async def next_analysis_version(session: AsyncSession, resume_id: str) -> int:
    result = await session.execute(
        text(
            """
            SELECT COALESCE(MAX(analysis_version), 0) + 1 AS v
            FROM public.analyses
            WHERE resume_id = CAST(:rid AS uuid)
            """
        ),
        {"rid": resume_id},
    )
    row = result.fetchone()
    return int(row[0]) if row and row[0] is not None else 1


async def insert_analysis(
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
    emb_sql = "CAST(:emb AS vector)" if embedding_str else "NULL"
    sql = f"""
        INSERT INTO public.analyses (
            user_id, resume_id, analysis_version, model, prompt_version,
            summary, findings, scores, embedding, meta
        )
        VALUES (
            CAST(:user_id AS uuid),
            CAST(:resume_id AS uuid),
            :version,
            :model,
            :prompt_version,
            :summary,
            CAST(:findings AS jsonb),
            CAST(:scores AS jsonb),
            {emb_sql},
            '{{}}'::jsonb
        )
        RETURNING id::text
    """
    params: dict[str, Any] = {
        "user_id": user_id,
        "resume_id": resume_id,
        "version": version,
        "model": model,
        "prompt_version": prompt_version,
        "summary": summary,
        "findings": json.dumps(findings),
        "scores": json.dumps(scores),
    }
    if embedding_str:
        params["emb"] = embedding_str
    result = await session.execute(text(sql), params)
    row = result.fetchone()
    if not row or row[0] is None:
        raise RuntimeError("insert_analysis failed")
    return str(row[0])


async def latest_resume_excerpt(
    session: AsyncSession,
    user_id: str,
    *,
    max_chars: int = 24_000,
) -> str | None:
    result = await session.execute(
        text(
            """
            SELECT parsed_text
            FROM public.resumes
            WHERE user_id = CAST(:uid AS uuid) AND parsing_status = 'ready'
            ORDER BY updated_at DESC
            LIMIT 1
            """
        ),
        {"uid": user_id},
    )
    row = result.fetchone()
    if not row or not row[0]:
        return None
    t: str = row[0]
    return t[:max_chars] if len(t) > max_chars else t


async def get_analysis_owned(
    session: AsyncSession,
    *,
    analysis_id: str,
    user_id: str,
) -> dict[str, Any] | None:
    result = await session.execute(
        text(
            """
            SELECT
                id::text,
                user_id::text,
                resume_id::text,
                summary,
                findings,
                scores,
                analysis_version,
                model,
                prompt_version,
                created_at
            FROM public.analyses
            WHERE id = CAST(:aid AS uuid)
              AND user_id = CAST(:uid AS uuid)
            """
        ),
        {"aid": analysis_id, "uid": user_id},
    )
    row = result.mappings().fetchone()
    if not row:
        return None
    d = dict(row)
    for key in ("findings", "scores"):
        v = d.get(key)
        if isinstance(v, str):
            try:
                d[key] = json.loads(v)
            except json.JSONDecodeError:
                d[key] = {}
        elif v is not None and not isinstance(v, dict):
            try:
                d[key] = dict(v)
            except (TypeError, ValueError):
                d[key] = {}
    return d


async def get_report_owned(
    session: AsyncSession,
    *,
    report_id: str,
    user_id: str,
) -> dict[str, Any] | None:
    result = await session.execute(
        text(
            """
            SELECT
                id::text,
                user_id::text,
                analysis_id::text,
                title,
                report_type,
                storage_path,
                status
            FROM public.reports
            WHERE id = CAST(:rid AS uuid) AND user_id = CAST(:uid AS uuid)
            """
        ),
        {"rid": report_id, "uid": user_id},
    )
    row = result.mappings().fetchone()
    return dict(row) if row else None


async def insert_chat_session(
    session: AsyncSession,
    *,
    user_id: str,
    title: str | None,
    resume_id: str | None,
) -> str:
    if resume_id:
        result = await session.execute(
            text(
                """
                INSERT INTO public.chat_sessions (user_id, title, resume_id, meta)
                VALUES (
                    CAST(:uid AS uuid),
                    :title,
                    CAST(:resume_id AS uuid),
                    '{}'::jsonb
                )
                RETURNING id::text
                """
            ),
            {"uid": user_id, "title": title, "resume_id": resume_id},
        )
    else:
        result = await session.execute(
            text(
                """
                INSERT INTO public.chat_sessions (user_id, title, resume_id, meta)
                VALUES (
                    CAST(:uid AS uuid),
                    :title,
                    NULL,
                    '{}'::jsonb
                )
                RETURNING id::text
                """
            ),
            {"uid": user_id, "title": title},
        )
    row = result.fetchone()
    if not row or row[0] is None:
        raise RuntimeError("insert_chat_session failed")
    return str(row[0])


async def verify_chat_session(
    session: AsyncSession,
    *,
    session_id: str,
    user_id: str,
) -> bool:
    result = await session.execute(
        text(
            """
            SELECT 1 FROM public.chat_sessions
            WHERE id = CAST(:sid AS uuid) AND user_id = CAST(:uid AS uuid)
            """
        ),
        {"sid": session_id, "uid": user_id},
    )
    return result.fetchone() is not None


async def insert_chat_message(
    session: AsyncSession,
    *,
    session_id: str,
    role: str,
    content: str,
    model: str | None,
    embedding_str: str | None = None,
) -> None:
    if embedding_str:
        await session.execute(
            text(
                """
                INSERT INTO public.chat_messages (
                    session_id, role, content, model, embedding, meta
                )
                VALUES (
                    CAST(:sid AS uuid),
                    :role,
                    :content,
                    :model,
                    CAST(:emb AS vector),
                    '{}'::jsonb
                )
                """
            ),
            {
                "sid": session_id,
                "role": role,
                "content": content,
                "model": model,
                "emb": embedding_str,
            },
        )
    else:
        await session.execute(
            text(
                """
                INSERT INTO public.chat_messages (session_id, role, content, model, meta)
                VALUES (
                    CAST(:sid AS uuid),
                    :role,
                    :content,
                    :model,
                    '{}'::jsonb
                )
                """
            ),
            {"sid": session_id, "role": role, "content": content, "model": model},
        )


async def rag_resume_snippets(
    session: AsyncSession,
    *,
    user_id: str,
    query_vec: str,
    limit: int = 2,
) -> list[str]:
    result = await session.execute(
        text(
            """
            SELECT LEFT(parsed_text, 2200) AS snip
            FROM public.resumes
            WHERE user_id = CAST(:uid AS uuid)
              AND embedding IS NOT NULL
              AND parsing_status = 'ready'
            ORDER BY embedding <=> CAST(:qv AS vector)
            LIMIT :lim
            """
        ),
        {"uid": user_id, "qv": query_vec, "lim": limit},
    )
    return [str(row[0]) for row in result.fetchall() if row[0]]


async def rag_analysis_snippets(
    session: AsyncSession,
    *,
    user_id: str,
    query_vec: str,
    limit: int = 2,
) -> list[str]:
    result = await session.execute(
        text(
            """
            SELECT LEFT(
                COALESCE(summary, '') || E'\n' || COALESCE(findings::text, ''),
                2200
            ) AS snip
            FROM public.analyses
            WHERE user_id = CAST(:uid AS uuid)
              AND embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:qv AS vector)
            LIMIT :lim
            """
        ),
        {"uid": user_id, "qv": query_vec, "lim": limit},
    )
    return [str(row[0]) for row in result.fetchall() if row[0]]


async def list_chat_history(
    session: AsyncSession,
    *,
    session_id: str,
    user_id: str,
) -> list[dict[str, Any]]:
    result = await session.execute(
        text(
            """
            SELECT m.id::text, m.role, m.content, m.created_at
            FROM public.chat_messages m
            INNER JOIN public.chat_sessions s ON s.id = m.session_id
            WHERE m.session_id = CAST(:sid AS uuid)
              AND s.user_id = CAST(:uid AS uuid)
            ORDER BY m.created_at ASC
            """
        ),
        {"sid": session_id, "uid": user_id},
    )
    rows = result.mappings().fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        d = dict(row)
        ts = d.get("created_at")
        if ts is not None:
            d["created_at"] = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
        out.append(d)
    return out
