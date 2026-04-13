import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from starlette.requests import Request
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import Client

from app.core.config import Settings
from app.core.dependencies import (
    get_db,
    get_openai_client,
    get_settings_dep,
    get_supabase_client,
)
from app.core.security import get_current_user, user_id_from_payload
from app.schemas.resume import (
    AnalyzeResumeRequest,
    AnalyzeResumeResponse,
    UploadResumeResponse,
)
from app.middleware.rate_limit import limiter
from app.services.resume_pipeline import analyze_resume_for_user, upload_resume_file

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Resume"])


@router.post(
    "/upload-resume",
    response_model=UploadResumeResponse,
    summary="Upload a resume file to Supabase Storage and create a DB row",
)
@limiter.limit("20/minute")
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
    supabase: Client = Depends(get_supabase_client),
) -> UploadResumeResponse:
    user_id = user_id_from_payload(user)
    if not file.filename:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Filename required")
    raw = await file.read()
    result = await upload_resume_file(
        db,
        supabase,
        settings,
        user_id=user_id,
        filename=file.filename,
        content=raw,
        content_type=file.content_type,
    )
    return UploadResumeResponse(**result)


@router.post(
    "/analyze-resume",
    response_model=AnalyzeResumeResponse,
    summary="Parse (if needed), summarize, embed, and store an analysis",
)
@limiter.limit("15/minute")
async def analyze_resume(
    request: Request,
    body: AnalyzeResumeRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
    supabase: Client = Depends(get_supabase_client),
    openai: AsyncOpenAI = Depends(get_openai_client),
) -> AnalyzeResumeResponse:
    user_id = user_id_from_payload(user)
    result = await analyze_resume_for_user(
        db,
        supabase,
        settings,
        openai,
        user_id=user_id,
        resume_id=body.resume_id,
    )
    return AnalyzeResumeResponse(**result)
