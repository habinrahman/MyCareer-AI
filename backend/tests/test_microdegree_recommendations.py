"""MicroDegree learning paths from suggested roles."""

from app.schemas.resume_analysis import ResumeAnalysisOutput
from app.services.recommendation_engine import (
    enrich_resume_analysis_with_microdegree_paths,
    get_microdegree_learning_paths,
)


def test_get_paths_dedupes_across_roles() -> None:
    paths = get_microdegree_learning_paths(["Cloud Engineer", "Cloud Engineer"])
    titles = [p["title"] for p in paths]
    assert len(titles) == len(set(titles))
    assert all(" — MicroDegree" in t for t in titles)
    assert all(p.get("provider") is None for p in paths)


def test_substring_role_maps_to_cloud_engineer() -> None:
    paths = get_microdegree_learning_paths(["Senior Cloud Engineer"])
    assert any("AWS Solutions Architect" in p["title"] for p in paths)


def test_enrich_overwrites_course_recommendations() -> None:
    nlp = ResumeAnalysisOutput.model_validate(
        {
            "recommended_roles": ["DevOps Engineer"],
            "course_recommendations": [
                {
                    "title": "External MOOC",
                    "provider": "Other",
                    "rationale": "Should be removed",
                }
            ],
        }
    )
    out = enrich_resume_analysis_with_microdegree_paths(nlp)
    assert not any("External" in c.title for c in out.course_recommendations)
    assert out.course_recommendations[0].title.endswith(" — MicroDegree")
    assert out.course_recommendations[0].rationale == ""
