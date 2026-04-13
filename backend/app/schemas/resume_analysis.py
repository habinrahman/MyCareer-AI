"""Structured NLP output for resume analysis (validated after GPT JSON)."""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class ExperienceEntry(BaseModel):
    title: str | None = None
    company: str | None = None
    date_range: str | None = None
    highlights: list[str] = Field(default_factory=list)

    @field_validator("highlights", mode="before")
    @classmethod
    def coerce_highlights(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v.strip()] if v.strip() else []
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        return []


class EducationEntry(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field: str | None = None
    date_range: str | None = None


class StructuredResume(BaseModel):
    """Structured view derived from raw resume text (no fabrication)."""

    headline: str | None = None
    experience: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    summary_excerpt: str | None = Field(
        default=None,
        description="Short neutral excerpt of stated objective/summary if present",
    )


class ATSCompatibility(BaseModel):
    score: int = Field(default=0, ge=0, le=100)
    keywords_match: list[str] = Field(
        default_factory=list,
        description="ATS-relevant keywords detected or missing vs target roles",
    )
    formatting_notes: str = ""
    suggestions: list[str] = Field(default_factory=list)


class SkillsAssessment(BaseModel):
    technical_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    proficiency_notes: str = ""


class SkillGapItem(BaseModel):
    skill: str
    gap_description: str = ""
    importance: str = Field(
        default="medium",
        description="high | medium | low",
    )

    @field_validator("importance", mode="before")
    @classmethod
    def normalize_importance(cls, v: object) -> str:
        if v is None or v == "":
            return "medium"
        s = str(v).strip().lower()
        if s in ("high", "medium", "low"):
            return s
        return "medium"


class SkillGapAnalysis(BaseModel):
    gaps: list[SkillGapItem] = Field(default_factory=list)
    industry_context: str = ""


class CourseRecommendation(BaseModel):
    title: str
    provider: str | None = None
    rationale: str = ""


class ResumeAnalysisOutput(BaseModel):
    """Full analysis payload returned by GPT-4o-mini (JSON mode)."""

    structured_resume: StructuredResume = Field(default_factory=StructuredResume)
    resume_score: int = Field(default=0, ge=0, le=100)
    professional_summary: str = ""
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    ats_compatibility: ATSCompatibility = Field(default_factory=ATSCompatibility)
    skills_assessment: SkillsAssessment = Field(default_factory=SkillsAssessment)
    skill_gap_analysis: SkillGapAnalysis = Field(default_factory=SkillGapAnalysis)
    recommended_roles: list[str] = Field(default_factory=list)
    career_outlook: str = Field(
        default="",
        description="5–10 year outlook narrative grounded in stated experience",
    )
    improvement_suggestions: list[str] = Field(default_factory=list)
    course_recommendations: list[CourseRecommendation] = Field(default_factory=list)
