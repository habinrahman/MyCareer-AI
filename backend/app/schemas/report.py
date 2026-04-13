from pydantic import BaseModel, Field


class ReportDetailResponse(BaseModel):
    id: str
    title: str
    report_type: str
    status: str
    storage_path: str | None = None
    signed_url: str | None = Field(
        default=None,
        description="Time-limited URL when report is ready and stored in Supabase Storage",
    )
    analysis_id: str | None = None
