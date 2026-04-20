"""ATS calibration keeps thin resumes out of inflated ATS bands."""

from app.schemas.resume_analysis import (
    ATSCompatibility,
    ExperienceEntry,
    ResumeAnalysisOutput,
    SkillGapAnalysis,
    SkillGapItem,
    StructuredResume,
)
from app.services.ats_score_calibration import apply_ats_calibration


def test_thin_resume_lowers_inflated_ats() -> None:
    nlp = ResumeAnalysisOutput(
        resume_score=82,
        professional_summary="Junior developer with coursework.",
        weaknesses=[
            "Limited professional experience",
            "No quantified business outcomes",
            "No internship experience yet",
            "Education still in progress",
        ],
        ats_compatibility=ATSCompatibility(
            score=92,
            keywords_match=["React", "Java", "Spring Boot", "SQL"],
            formatting_notes="Readable sections.",
            suggestions=["Add metrics to each bullet."],
        ),
        skill_gap_analysis=SkillGapAnalysis(
            gaps=[
                SkillGapItem(skill="Testing", gap_description="Limited coverage", importance="high"),
                SkillGapItem(skill="CI/CD", gap_description="No pipeline ownership", importance="high"),
            ],
        ),
        structured_resume=StructuredResume(
            experience=[
                ExperienceEntry(
                    title="Junior Developer",
                    company="Acme",
                    highlights=["Built internal tools using React"],
                )
            ]
        ),
    )
    out = apply_ats_calibration(nlp)
    assert out.ats_compatibility.score < nlp.ats_compatibility.score
    # Strict-but-fair band: not inflated (90s) and not over-penalized (50s).
    assert 68 <= out.ats_compatibility.score <= 82


def test_metrics_present_preserves_high_band() -> None:
    nlp = ResumeAnalysisOutput(
        resume_score=88,
        professional_summary="Shipped features that improved signup conversion by 18%.",
        weaknesses=["Minor wording polish"],
        ats_compatibility=ATSCompatibility(
            score=88,
            keywords_match=["Python", "AWS"],
            formatting_notes="Clean.",
            suggestions=[],
        ),
        structured_resume=StructuredResume(
            experience=[
                ExperienceEntry(
                    title="Engineer",
                    company="Co",
                    highlights=["Cut infra cost by 12% YoY", "Owned API serving 2M requests/day"],
                )
            ]
        ),
    )
    out = apply_ats_calibration(nlp)
    assert out.ats_compatibility.score >= 75
