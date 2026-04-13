from enum import StrEnum


class ParsingStatus(StrEnum):
    pending = "pending"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class ChatRole(StrEnum):
    user = "user"
    assistant = "assistant"
    system = "system"
    tool = "tool"


class ReportType(StrEnum):
    career_summary = "career_summary"
    resume_review = "resume_review"
    interview_prep = "interview_prep"
    custom = "custom"


class ReportStatus(StrEnum):
    draft = "draft"
    ready = "ready"
    failed = "failed"
