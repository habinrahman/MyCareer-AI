import logging
from typing import Any

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import Client

from app.core.config import Settings
from app.services import openai_service, persistence, supabase_storage
from app.services.resume_analysis_llm import analyze_resume_structured
from app.services.resume_parser import (
    UnsupportedResumeFormatError,
    normalize_resume_text,
    parse_resume_file,
)
from app.utils.exceptions import AppError
from app.utils.strings import safe_storage_filename, storage_object_key
from app.utils.vectors import format_vector

logger = logging.getLogger(__name__)


# NOTE: ``session`` is request-scoped from ``get_db`` (autobegin). Use
# ``await session.commit()`` / ``rollback()`` only — never ``async with session.begin()``.


async def upload_resume_file(
    session: AsyncSession,
    supabase: Client,
    settings: Settings,
    *,
    user_id: str,
    filename: str,
    content: bytes,
    content_type: str | None,
) -> dict[str, Any]:
    if len(content) > settings.max_upload_bytes:
        raise AppError("File too large", status_code=413)

    safe_name = safe_storage_filename(filename)
    path = storage_object_key(user_id, safe_name)
    mime = content_type or "application/octet-stream"

    await persistence.ensure_user_row(session, user_id)
    await supabase_storage.upload_bytes(
        supabase,
        settings.supabase_resumes_bucket,
        path,
        content,
        mime,
    )

    resume_id = await persistence.insert_resume_row(
        session,
        user_id=user_id,
        original_filename=filename,
        mime_type=content_type,
        file_size_bytes=len(content),
        storage_path=path,
        meta={"source": "api", "bucket": settings.supabase_resumes_bucket},
    )
    await session.commit()
    logger.info("resume.uploaded user=%s resume_id=%s path=%s", user_id, resume_id, path)

    return {
        "resume_id": resume_id,
        "storage_path": path,
        "original_filename": filename,
        "mime_type": content_type,
        "file_size_bytes": len(content),
    }


async def analyze_resume_for_user(
    session: AsyncSession,
    supabase: Client,
    settings: Settings,
    client: AsyncOpenAI,
    *,
    user_id: str,
    resume_id: str,
) -> dict[str, Any]:
    row = await persistence.get_resume_owned(
        session, resume_id=resume_id, user_id=user_id
    )
    if not row:
        raise AppError("Resume not found", status_code=404)

    storage_path = row.get("storage_path")
    parsed_existing = row.get("parsed_text")

    await persistence.set_resume_processing(session, resume_id)
    await session.commit()

    try:
        if parsed_existing and row.get("parsing_status") == "ready":
            text_body = parsed_existing
        else:
            if not storage_path:
                raise AppError("Resume has no storage path", status_code=400)
            raw = await supabase_storage.download_bytes(
                supabase, settings.supabase_resumes_bucket, storage_path
            )
            try:
                text_body = parse_resume_file(raw, row["original_filename"])
            except UnsupportedResumeFormatError as exc:
                raise AppError(str(exc), status_code=400) from exc
            except ValueError as exc:
                raise AppError(str(exc), status_code=422) from exc

        text_body = normalize_resume_text(text_body)

        nlp = await analyze_resume_structured(
            client, settings.openai_chat_model, text_body
        )
        summary = nlp.professional_summary

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
        }
        scores = {
            "resume_score": nlp.resume_score,
            "ats_score": nlp.ats_compatibility.score,
            "model": settings.openai_chat_model,
            "prompt_version": settings.openai_prompt_version,
        }

        version = await persistence.next_analysis_version(session, resume_id)
        await persistence.update_resume_parsed(
            session,
            resume_id=resume_id,
            parsed_text=text_body,
            embedding_str=emb_str,
            language=None,
        )
        analysis_id = await persistence.insert_analysis(
            session,
            user_id=user_id,
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
    except AppError:
        await session.rollback()
        await persistence.set_resume_failed(session, resume_id)
        await session.commit()
        raise
    except Exception as exc:
        await session.rollback()
        logger.exception("resume.analyze_failed resume_id=%s", resume_id)
        try:
            await persistence.set_resume_failed(session, resume_id)
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        raise AppError("Analysis failed", status_code=500) from exc

    logger.info(
        "resume.analyzed user=%s resume_id=%s analysis_id=%s v=%s",
        user_id,
        resume_id,
        analysis_id,
        version,
    )
    return {
        "resume_id": resume_id,
        "analysis_id": analysis_id,
        "analysis_version": version,
        "summary": summary,
        "parsed_char_count": len(text_body),
        "analysis": nlp.model_dump(mode="json"),
    }
