"""ATS score calibration: weighted composite blended with model output (strict but fair)."""

from __future__ import annotations

import re

from app.schemas.resume_analysis import ResumeAnalysisOutput

_METRIC_RE = re.compile(
    r"(\d+\s*%|\$\s*\d|\d{1,3}\s*(k|m)\b|"
    r"\b(increased|decreased|reduced|improved|saved|grew|cut|raised|lowered)\b[^\n]{0,72}\d)",
    re.IGNORECASE,
)

_ACTION_VERB_RE = re.compile(
    r"\b(led|built|implemented|designed|delivered|owned|shipped|developed|created|"
    r"managed|optimized|launched|migrated|automated)\b",
    re.IGNORECASE,
)

_NEGATIVE_FMT_RE = re.compile(
    r"\b(risk|issue|avoid|missing|sparse|hard to|difficult|problem|concern)\b",
    re.IGNORECASE,
)


def _resume_blob(nlp: ResumeAnalysisOutput) -> str:
    parts: list[str] = [
        nlp.professional_summary or "",
        nlp.structured_resume.summary_excerpt or "",
    ]
    for entry in nlp.structured_resume.experience:
        parts.append(entry.title or "")
        parts.append(entry.company or "")
        parts.extend(entry.highlights or [])
    return " ".join(parts).lower()


def _experience_titles_blob(nlp: ResumeAnalysisOutput) -> str:
    return " ".join(
        f"{e.title or ''} {e.company or ''}" for e in nlp.structured_resume.experience
    ).lower()


def _keyword_match_score(nlp: ResumeAnalysisOutput) -> float:
    kw = [k for k in (nlp.ats_compatibility.keywords_match or []) if str(k).strip()]
    skills = [s for s in (nlp.structured_resume.skills or []) if str(s).strip()]
    n_kw = len(kw)
    n_sk = len(skills)
    if n_kw >= 1:
        # ~4 strong matches → ~80 (plateaus after ~6).
        return min(100.0, 40.0 + 10.0 * min(n_kw, 6))
    if n_sk >= 1:
        return min(100.0, 38.0 + 5.5 * min(n_sk, 12))
    return 40.0


def _experience_strength_score(nlp: ResumeAnalysisOutput) -> float:
    titles = _experience_titles_blob(nlp)
    n = len(nlp.structured_resume.experience)
    if n >= 3:
        return 88.0
    if n == 2:
        return 78.0
    if n == 1:
        if "intern" in titles:
            return 70.0
        return 60.0
    return 45.0


def _impact_score(blob: str) -> float:
    if _METRIC_RE.search(blob):
        return 80.0
    if _ACTION_VERB_RE.search(blob):
        return 65.0
    return 50.0


def _formatting_score(nlp: ResumeAnalysisOutput) -> float:
    fmt = (nlp.ats_compatibility.formatting_notes or "").strip()
    if not fmt:
        return 86.0
    if _NEGATIVE_FMT_RE.search(fmt.lower()):
        return 78.0
    return 87.0


def _completeness_score(nlp: ResumeAnalysisOutput) -> float:
    hits = 0
    basics = nlp.structured_resume.basics
    if basics and (basics.email or basics.phone or basics.linkedin):
        hits += 1
    if nlp.structured_resume.experience:
        hits += 1
    if nlp.structured_resume.education:
        hits += 1
    if nlp.structured_resume.skills:
        hits += 1
    if (nlp.professional_summary or "").strip() or (nlp.structured_resume.summary_excerpt or "").strip():
        hits += 1
    # 52 + 7*h maps ~3 hits to mid-70s, full coverage toward high 80s.
    return max(48.0, min(92.0, 52.0 + 7.0 * hits))


def _weighted_ats(nlp: ResumeAnalysisOutput) -> float:
    blob = _resume_blob(nlp)
    return (
        _keyword_match_score(nlp) * 0.35
        + _experience_strength_score(nlp) * 0.25
        + _impact_score(blob) * 0.20
        + _formatting_score(nlp) * 0.10
        + _completeness_score(nlp) * 0.10
    )


def apply_ats_calibration(nlp: ResumeAnalysisOutput) -> ResumeAnalysisOutput:
    """
    Combine a transparent weighted ATS estimate with the model score.

    The composite prevents keyword-only inflation *and* avoids over-penalizing
    structured resumes that still parse and match well.
    """
    raw = max(0.0, min(100.0, float(int(nlp.ats_compatibility.score))))
    composite = _weighted_ats(nlp)
    # Anchor on weighted signal; retain part of the model for nuance.
    blended = 0.60 * composite + 0.40 * raw
    calibrated = int(round(max(0.0, min(100.0, blended))))

    return nlp.model_copy(
        update={
            "ats_compatibility": nlp.ats_compatibility.model_copy(
                update={"score": calibrated}
            )
        }
    )
