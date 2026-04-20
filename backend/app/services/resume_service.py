"""Stateless resume parsing + LLM analysis for public and future flows."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import UploadFile
from openai import AsyncOpenAI

from app.core.config import Settings
from app.schemas.public_resume import PublicAnalyzeResumeResponse, PublicResumeScores
from app.services.resume_analysis_llm import analyze_resume_structured
from app.services.resume_parser import (
    UnsupportedResumeFormatError,
    normalize_resume_text,
    parse_resume_file,
)
from app.utils.exceptions import AppError

logger = logging.getLogger(__name__)


async def analyze_resume_bytes(
    content: bytes,
    filename: str,
    *,
    client: AsyncOpenAI,
    settings: Settings,
) -> tuple[PublicAnalyzeResumeResponse, str]:
    """
    Parse PDF/DOCX bytes, run structured OpenAI analysis.
    No Supabase, no Postgres, no embeddings (V1 public speed/cost).
    """
    if not filename:
        raise AppError("Filename required", status_code=400)

    if len(content) > settings.max_upload_bytes:
        raise AppError("File too large", status_code=413)

    try:
        text_body = await asyncio.to_thread(parse_resume_file, content, filename)
    except UnsupportedResumeFormatError as exc:
        raise AppError(str(exc), status_code=400) from exc
    except ValueError as exc:
        raise AppError(str(exc), status_code=422) from exc

    text_body = normalize_resume_text(text_body)
    if not text_body.strip():
        raise AppError("Could not extract text from this file", status_code=422)

    try:
        nlp = await analyze_resume_structured(
            client, settings.openai_chat_model, text_body
        )
    except Exception as exc:
        logger.exception("public_resume.analysis_failed")
        raise AppError("Analysis failed", status_code=500) from exc

    scores = PublicResumeScores(
        resume_score=nlp.resume_score,
        ats_score=nlp.ats_compatibility.score,
        model=settings.openai_chat_model,
        prompt_version=settings.openai_prompt_version,
    )
    response = PublicAnalyzeResumeResponse(
        summary=nlp.professional_summary,
        parsed_char_count=len(text_body),
        scores=scores,
        analysis=nlp,
    )
    return response, text_body


async def analyze_resume_file(
    file: UploadFile,
    *,
    client: AsyncOpenAI,
    settings: Settings,
) -> dict[str, Any]:
    """Read ``UploadFile`` and return JSON-serializable analysis dict."""
    raw = await file.read()
    name = file.filename or "resume.pdf"
    result, _text = await analyze_resume_bytes(raw, name, client=client, settings=settings)
    return result.model_dump(mode="json")
