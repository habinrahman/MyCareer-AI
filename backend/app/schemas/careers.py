from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CareerProfileResponse(BaseModel):
    """All authenticated users use the student-facing careers workspace."""

    role: Literal["student"] = Field(
        default="student",
        description="Fixed learner role; recruitment features are not available.",
    )


class CareerProfileUpdateRequest(BaseModel):
    """Reserved for future student preferences; unknown fields are ignored."""

    model_config = ConfigDict(extra="ignore")


class BenchmarkComparison(BaseModel):
    benchmark_id: str
    industry: str
    role_family: str
    metric_name: str
    p25: int | None
    p50: int
    p75: int | None
    user_value: float | None
    band: str | None = Field(
        default=None,
        description="below_p25 | p25_to_p50 | p50_to_p75 | above_p75 | unknown",
    )
    narrative: str | None = None


class BenchmarksResponse(BaseModel):
    resume_id: str | None = None
    analysis_id: str | None = None
    comparisons: list[BenchmarkComparison]
    notes: list[str] = Field(default_factory=list)


class JobMatchRequest(BaseModel):
    resume_id: str | None = None
    limit: int = Field(default=12, ge=1, le=50)
    backfill_job_embeddings: bool = Field(
        default=True,
        description="When true, embed active job rows missing vectors (OpenAI call).",
    )


class JobMatchRow(BaseModel):
    job_id: str
    title: str
    company_name: str | None = None
    location: str | None = None
    employment_type: str | None = None
    industry: str | None = None
    external_url: str | None = None
    similarity: float | None = None


class JobMatchResponse(BaseModel):
    resume_id: str
    query_source: str
    matches: list[JobMatchRow]
    fallback_text_only: bool = False
    notes: list[str] = Field(default_factory=list)
