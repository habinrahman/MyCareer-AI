"""Compare stored analysis scores to ``industry_benchmarks`` rows."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.careers import BenchmarkComparison, BenchmarksResponse
from app.services import careers_repository


def _score_band(score: float, p25: int | None, p50: int, p75: int | None) -> str:
    if p25 is not None and score < p25:
        return "below_p25"
    if p75 is not None and score > p75:
        return "above_p75"
    if p25 is not None and score < p50:
        return "p25_to_p50"
    if p75 is not None and score > p50:
        return "p50_to_p75"
    if score >= p50:
        return "p50_to_p75"
    return "p25_to_p50"


def _narrative(band: str, role_family: str, p50: int) -> str:
    if band == "below_p25":
        return (
            f"For {role_family}, your score sits below the typical lower quartile (below p25). "
            "Focus on measurable impact, role keywords, and clarity versus the median "
            f"around {p50}."
        )
    if band == "p25_to_p50":
        return (
            f"You are between the lower quartile and the median for {role_family}. "
            "Small upgrades to structure and quantified outcomes often move candidates into the top half."
        )
    if band in ("p50_to_p75", "above_p75"):
        return (
            f"You are at or above the median for {role_family} in this composite. "
            "Keep tailoring each application to the job description and ATS keywords."
        )
    return ""


def _extract_resume_score(scores: Any) -> float | None:
    if scores is None:
        return None
    if isinstance(scores, str):
        try:
            scores = json.loads(scores)
        except Exception:
            return None
    if not isinstance(scores, dict):
        return None
    raw = scores.get("resume_score")
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


async def build_benchmarks_response(
    session: AsyncSession,
    *,
    user_id: str,
    industry: str | None,
    role_family: str | None,
    resume_id: str | None,
    metric_name: str = "resume_score",
) -> BenchmarksResponse:
    notes: list[str] = []
    analysis = await careers_repository.get_latest_analysis_row(
        session, user_id=user_id, resume_id=resume_id
    )
    user_score = _extract_resume_score(analysis.get("scores") if analysis else None)
    if user_score is None and analysis:
        notes.append("Latest analysis has no numeric resume_score in scores JSON; comparisons are qualitative only.")

    rows = await careers_repository.list_industry_benchmarks(
        session,
        industry=industry,
        role_family=role_family,
        metric_name=metric_name,
    )
    if not rows:
        notes.append(
            "No benchmark rows matched the filter. Try another industry/role_family or seed industry_benchmarks."
        )

    comparisons: list[BenchmarkComparison] = []
    for row in rows:
        p25 = int(row["p25"]) if row.get("p25") is not None else None
        p50 = int(row["p50"])
        p75 = int(row["p75"]) if row.get("p75") is not None else None
        band: str | None = None
        narrative: str | None = None
        if user_score is not None:
            band = _score_band(user_score, p25, p50, p75)
            narrative = _narrative(band, str(row["role_family"]), p50)
        comparisons.append(
            BenchmarkComparison(
                benchmark_id=str(row["id"]),
                industry=str(row["industry"]),
                role_family=str(row["role_family"]),
                metric_name=str(row["metric_name"]),
                p25=p25,
                p50=p50,
                p75=p75,
                user_value=user_score,
                band=band,
                narrative=narrative,
            )
        )

    return BenchmarksResponse(
        resume_id=str(analysis["resume_id"]) if analysis and analysis.get("resume_id") else None,
        analysis_id=str(analysis["id"]) if analysis and analysis.get("id") else None,
        comparisons=comparisons,
        notes=notes,
    )
