import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, IntegrityError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette.responses import Response

from app.core.database import get_db
from app.middleware.rate_limit import limiter
from app.schemas.lead import LeadCreate, LeadCreatedResponse
from app.services import database_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/leads", tags=["Leads"])

_MISSING_TABLE_HINT = (
    "The table public.resume_download_leads is missing or unreachable. "
    "In Supabase → SQL Editor, run supabase/migrations/0004_resume_download_leads.sql "
    "(and 0005 if present), then retry."
)


@router.post("/", response_model=LeadCreatedResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_lead(
    request: Request,
    lead: LeadCreate,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Capture contact details before PDF download (public; no JWT).
    Inserts into ``public.resume_download_leads`` using the API database role.
    """
    try:
        lead_id = await database_service.insert_download_lead(
            db,
            full_name=lead.full_name,
            email=str(lead.email).strip().lower(),
            phone=lead.phone,
            analysis_id=lead.analysis_id,
        )
        await db.commit()
    except ProgrammingError as exc:
        await db.rollback()
        logger.exception("lead.insert.programming_error")
        code = getattr(getattr(exc, "orig", None), "pgcode", None)
        msg = str(getattr(exc, "orig", exc)).lower()
        if code == "42P01" or "undefinedtable" in msg or "does not exist" in msg:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=_MISSING_TABLE_HINT,
            ) from exc
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Lead capture failed due to a database error. Check server logs.",
        ) from exc
    except IntegrityError as exc:
        await db.rollback()
        logger.warning("lead.insert.integrity_error: %s", exc.orig)
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Invalid data (e.g. unknown analysis_id). Leave analysis empty for public PDF download.",
        ) from exc
    except DBAPIError as exc:
        await db.rollback()
        logger.exception("lead.insert.dbapi_error")
        msg = str(getattr(exc, "orig", exc)).lower()
        if "permission denied" in msg or "insufficient_privilege" in msg:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Database role cannot insert into resume_download_leads. "
                    "Use a Supabase connection string with sufficient privileges (e.g. postgres / service role)."
                ),
            ) from exc
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Lead capture temporarily unavailable. Check DATABASE_URL and Supabase status.",
        ) from exc
    except Exception as exc:  # noqa: BLE001 — last-resort so the API returns JSON + CORS headers
        await db.rollback()
        logger.exception("lead.insert.unexpected_error")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lead capture failed unexpectedly. Check server logs.",
        ) from exc

    logger.info("lead.captured lead_id=%s email=%s", lead_id, lead.email)
    payload = LeadCreatedResponse(lead_id=lead_id)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=payload.model_dump(),
    )
