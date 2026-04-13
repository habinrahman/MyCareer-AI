from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import Client

from app.core.config import Settings, get_settings
from app.core.dependencies import (
    get_current_user_id,
    get_db,
    get_settings_dep,
    get_supabase_client,
)
from app.schemas.report import ReportDetailResponse
from app.services import persistence, supabase_storage
from app.services.pdf_analysis_report import build_analysis_pdf_bytes
from app.utils.ttl_response_cache import (
    get_cached_report_detail,
    set_cached_report_detail,
)

router = APIRouter(tags=["Reports"])


@router.get(
    "/download-report/{analysis_id}",
    summary="Download a branded PDF career report for an analysis you own",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
async def download_analysis_report(
    analysis_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Response:
    row = await persistence.get_analysis_owned(
        db, analysis_id=analysis_id, user_id=user_id
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    settings = get_settings()
    profile = await persistence.get_user_pdf_profile(db, user_id=user_id)
    base = (str(settings.public_app_url).rstrip("/") if settings.public_app_url else "")
    online_report_url = (
        f"{base}/resume?analysisId={row['id']}" if base else None
    )

    pdf = build_analysis_pdf_bytes(
        analysis_id=row["id"],
        summary_column=str(row.get("summary") or ""),
        findings_raw=row.get("findings"),
        scores_raw=row.get("scores"),
        analysis_version=int(row.get("analysis_version") or 1),
        model_name=str(row.get("model") or "") or None,
        candidate_display_name=profile.get("display_name"),
        candidate_email=profile.get("email"),
        candidate_linkedin_url=profile.get("linkedin_url"),
        candidate_github_url=profile.get("github_url"),
        online_report_url=online_report_url,
    )
    fname = f"mycareer-ai-report-{row['id'][:8]}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{fname}"',
            "Cache-Control": "private, no-store",
        },
    )


@router.get(
    "/report/{report_id}",
    response_model=ReportDetailResponse,
    summary="Report metadata and signed download URL when applicable",
)
async def get_report(
    report_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
    supabase: Client = Depends(get_supabase_client),
) -> ReportDetailResponse:
    cached = get_cached_report_detail(user_id, report_id)
    if cached is not None:
        return cached

    row = await persistence.get_report_owned(
        db, report_id=report_id, user_id=user_id
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Report not found")

    signed: str | None = None
    path = row.get("storage_path")
    if path and row.get("status") == "ready":
        signed = await supabase_storage.create_signed_url(
            supabase,
            settings.supabase_reports_bucket,
            path,
            settings.supabase_signed_url_ttl_seconds,
        )

    out = ReportDetailResponse(
        id=row["id"],
        title=row["title"],
        report_type=row["report_type"],
        status=row["status"],
        storage_path=path,
        signed_url=signed,
        analysis_id=row.get("analysis_id"),
    )
    set_cached_report_detail(user_id, report_id, out)
    return out
