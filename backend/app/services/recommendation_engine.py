"""
MicroDegree learning-path recommendations from AI-suggested roles.

Replaces model-generated external course lists with catalog-backed paths only.
"""

from __future__ import annotations

from app.data.microdegree_courses import MICRODEGREE_COURSES
from app.schemas.resume_analysis import CourseRecommendation, ResumeAnalysisOutput


def _catalog_key_for_suggested_role(role: str) -> str | None:
    """Map a free-form suggested role string to a catalog key when possible."""
    r = role.strip()
    if not r:
        return None
    if r in MICRODEGREE_COURSES:
        return r
    rl = r.lower()
    for key in MICRODEGREE_COURSES:
        if key.lower() == rl:
            return key
    # e.g. "Senior Cloud Engineer" -> "Cloud Engineer"
    for key in sorted(MICRODEGREE_COURSES.keys(), key=len, reverse=True):
        if key.lower() in rl:
            return key
    return None


def get_microdegree_learning_paths(suggested_roles: list[str]) -> list[dict[str, str | None]]:
    """
    Build de-duplicated MicroDegree course lines for the given suggested roles.

    ``title`` is the full display line (``… — MicroDegree``). ``provider`` is
    omitted so UIs that append ``— {provider}`` do not duplicate the suffix.
    """
    if not suggested_roles:
        return []

    recommendations: list[dict[str, str | None]] = []
    seen: set[str] = set()

    for role in suggested_roles:
        key = _catalog_key_for_suggested_role(role)
        if not key:
            continue
        for course in MICRODEGREE_COURSES.get(key, []):
            if course not in seen:
                recommendations.append({"title": course, "provider": None})
                seen.add(course)

    return recommendations


def enrich_resume_analysis_with_microdegree_paths(
    analysis: ResumeAnalysisOutput,
) -> ResumeAnalysisOutput:
    """
    Overwrite ``course_recommendations`` with MicroDegree-only paths derived from
    ``recommended_roles`` (model output for target roles).
    """
    paths = get_microdegree_learning_paths(analysis.recommended_roles)
    analysis.course_recommendations = [
        CourseRecommendation(title=p["title"], provider=p.get("provider"), rationale="")
        for p in paths
    ]
    return analysis
