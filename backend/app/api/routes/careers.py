import logging

from fastapi import APIRouter, Body, Depends, Query, Request
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.dependencies import (
    get_current_user_id,
    get_db,
    get_openai_client,
    get_settings_dep,
)
from app.middleware.rate_limit import limiter
from app.schemas.careers import (
    BenchmarksResponse,
    CareerProfileResponse,
    CareerProfileUpdateRequest,
    JobMatchRequest,
    JobMatchResponse,
)
from app.services import benchmarking_service, job_matching_service, persistence

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/careers", tags=["Careers"])


@router.get("/me", response_model=CareerProfileResponse)
@limiter.limit("60/minute")
async def get_career_profile(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> CareerProfileResponse:
    await persistence.ensure_user_row(db, user_id)
    return CareerProfileResponse()


@router.patch("/me", response_model=CareerProfileResponse)
@limiter.limit("30/minute")
async def update_career_profile(
    request: Request,
    body: CareerProfileUpdateRequest = Body(default_factory=CareerProfileUpdateRequest),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> CareerProfileResponse:
    _ = body  # validated by FastAPI; extend CareerProfileUpdateRequest when PATCH fields exist
    await persistence.ensure_user_row(db, user_id)
    await db.commit()
    logger.info("careers.profile_touch user=%s", user_id)
    return CareerProfileResponse()


@router.get("/benchmarks", response_model=BenchmarksResponse)
@limiter.limit("60/minute")
async def get_benchmarks(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    industry: str | None = Query(default=None),
    role_family: str | None = Query(default=None),
    resume_id: str | None = Query(default=None),
    metric_name: str = Query(default="resume_score"),
) -> BenchmarksResponse:
    return await benchmarking_service.build_benchmarks_response(
        db,
        user_id=user_id,
        industry=industry,
        role_family=role_family,
        resume_id=resume_id,
        metric_name=metric_name,
    )


@router.post("/jobs/match", response_model=JobMatchResponse)
@limiter.limit("20/minute")
async def post_job_match(
    request: Request,
    body: JobMatchRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
    openai: AsyncOpenAI = Depends(get_openai_client),
) -> JobMatchResponse:
    return await job_matching_service.match_jobs_for_user(
        db,
        openai,
        settings,
        user_id=user_id,
        resume_id=body.resume_id,
        limit=body.limit,
        backfill_job_embeddings=body.backfill_job_embeddings,
    )
