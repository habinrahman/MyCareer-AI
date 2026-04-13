from pydantic import BaseModel, Field

from app.schemas.resume_analysis import ResumeAnalysisOutput


class UploadResumeResponse(BaseModel):
    resume_id: str
    storage_path: str
    original_filename: str
    mime_type: str | None = None
    file_size_bytes: int


class AnalyzeResumeRequest(BaseModel):
    resume_id: str = Field(..., min_length=10, max_length=64)


class AnalyzeResumeResponse(BaseModel):
    resume_id: str
    analysis_id: str
    analysis_version: int
    summary: str
    parsed_char_count: int = Field(ge=0)
    analysis: ResumeAnalysisOutput = Field(
        description="Full structured NLP output (JSON-validated)",
    )
