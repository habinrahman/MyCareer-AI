import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.database import get_db
from app.core.dependencies import get_settings_dep
from app.middleware.rate_limit import limiter
from app.schemas.health import DatabaseHealthResponse, HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness and dependency checks",
)
@limiter.exempt
async def health(
    settings: Settings = Depends(get_settings_dep),
    session: AsyncSession = Depends(get_db),
) -> HealthResponse:
    db_status = "connected"
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        logger.warning("health.db_check_failed: %s", exc)
        db_status = "degraded"
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
        database=db_status,
    )


@router.get(
    "/health/db",
    response_model=DatabaseHealthResponse,
    summary="PostgreSQL connectivity (asyncpg / Supabase)",
    responses={503: {"description": "Database unreachable", "model": DatabaseHealthResponse}},
)
@limiter.exempt
async def health_database(
    session: AsyncSession = Depends(get_db),
) -> DatabaseHealthResponse | JSONResponse:
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        logger.warning("health.db.failed: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "disconnected"},
        )
    return DatabaseHealthResponse(status="ok", database="connected")
