import logging
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse, Response
from openai import AsyncOpenAI
from starlette.requests import Request

from app.core.config import Settings
from app.core.dependencies import (
    get_openai_client,
    get_settings_dep,
)
from app.core.feature_guards import require_public_resume_review
from app.middleware.rate_limit import limiter
from app.services.pdf_analysis_report import build_analysis_pdf_bytes
from app.services.resume_service import analyze_resume_bytes
from app.utils.exceptions import AppError
from app.utils.resume_upload_validation import (
    read_upload_bytes_capped,
    resume_filename_allowed,
    resume_magic_matches_filename,
)

router = APIRouter(prefix="/public", tags=["Public"])
logger = logging.getLogger(__name__)


@router.post(
    "/analyze-resume",
    summary="Public resume analysis (no authentication)",
    response_model=None,
    responses={
        200: {
            "description": "JSON when format=json (default); PDF when format=pdf",
            "content": {
                "application/json": {"schema": {}},
                "application/pdf": {},
            },
        }
    },
)
@limiter.limit("5/minute")
async def analyze_resume_public(
    request: Request,
    _: None = Depends(require_public_resume_review),
    file: UploadFile = File(...),
    response_format: Literal["json", "pdf"] = Query(
        default="json",
        alias="format",
        description="Return structured JSON or a one-shot PDF report",
    ),
    settings: Settings = Depends(get_settings_dep),
    openai: AsyncOpenAI = Depends(get_openai_client),
) -> Response:
    """
    Upload a PDF or DOCX resume and receive AI feedback (scores, strengths,
    gaps, suggestions, recommended roles).

    **Stateless:** responses are not written to Postgres or Storage (no shared anonymous
    tenant). To persist files and analyses per user, use authenticated
    ``POST /upload-resume`` and ``POST /analyze-resume`` with a Supabase JWT.
    """
    if not resume_filename_allowed(file.filename):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are supported.",
        )

    name = (file.filename or "resume.pdf").strip()
    forwarded = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    client_ip = forwarded or (request.client.host if request.client else None)

    raw = await read_upload_bytes_capped(file, settings.max_upload_bytes)
    if not raw:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Empty file.",
        )
    if not resume_magic_matches_filename(raw, name):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="File content does not match a valid PDF or DOCX.",
        )

    logger.info(
        "public.analyze_resume client_ip=%s filename=%s bytes=%s format=%s origin=%s",
        client_ip,
        name,
        len(raw),
        response_format,
        request.headers.get("origin"),
    )

    try:
        result, _parsed_text = await analyze_resume_bytes(
            raw, name, client=openai, settings=settings
        )
        result_dict = result.model_dump(mode="json")
    except AppError as exc:
        raise HTTPException(exc.status_code, detail=exc.message) from exc

    if response_format == "pdf":
        findings = result.analysis.model_dump(mode="json")
        scores_dict = {
            "resume_score": result.scores.resume_score,
            "ats_score": result.scores.ats_score,
            "model": result.scores.model,
            "prompt_version": result.scores.prompt_version,
        }
        pdf_bytes = build_analysis_pdf_bytes(
            analysis_id="public-review",
            summary_column=result.summary,
            findings_raw=findings,
            scores_raw=scores_dict,
            analysis_version=1,
            model_name=settings.openai_chat_model,
            candidate_display_name=None,
            candidate_email=None,
            candidate_linkedin_url=None,
            candidate_github_url=None,
            online_report_url=None,
        )
        fname = (file.filename.rsplit(".", 1)[0] or "resume") + "-review.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{fname}"',
            },
        )

    return JSONResponse(content=result_dict)
