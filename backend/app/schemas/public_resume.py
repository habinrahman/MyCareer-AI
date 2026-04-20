"""Public (unauthenticated) resume review API schemas."""

from pydantic import BaseModel, Field

from app.schemas.resume_analysis import ResumeAnalysisOutput


class PublicResumeScores(BaseModel):
    resume_score: int = Field(ge=0, le=100)
    ats_score: int = Field(ge=0, le=100)
    model: str = ""
    prompt_version: str = ""


class PublicAnalyzeResumeResponse(BaseModel):
    """Instant AI feedback without persisting to the database."""

    summary: str
    parsed_char_count: int = Field(ge=0)
    scores: PublicResumeScores
    analysis: ResumeAnalysisOutput
