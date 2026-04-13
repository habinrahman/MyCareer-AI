from pydantic import BaseModel, ConfigDict, Field


class ChatMessageSchema(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system|tool)$")
    content: str = Field(..., min_length=1, max_length=32000)


class ChatRequest(BaseModel):
    messages: list[ChatMessageSchema] = Field(..., min_length=1, max_length=50)
    session_id: str | None = None
    stream: bool = Field(
        default=False,
        description="If true, response is text/event-stream (SSE); cannot combine with structured_output.",
    )
    structured_output: bool = Field(
        default=False,
        description="If true, response is JSON with reply + structured fields (non-streaming only).",
    )


class MentorStructuredBlock(BaseModel):
    """Structured facets returned alongside the main answer (JSON mode)."""

    role_recommendations: list[str] = Field(default_factory=list)
    skill_gap_notes: list[str] = Field(default_factory=list)
    interview_prep: list[str] = Field(default_factory=list)
    learning_roadmap: list[str] = Field(default_factory=list)


class MentorStructuredJSON(BaseModel):
    """Validated OpenAI json_object output for structured chat."""

    model_config = ConfigDict(extra="ignore")

    answer: str = ""
    role_recommendations: list[str] = Field(default_factory=list)
    skill_gap_notes: list[str] = Field(default_factory=list)
    interview_prep: list[str] = Field(default_factory=list)
    learning_roadmap: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    session_id: str | None = None
    structured: MentorStructuredBlock | None = Field(
        default=None,
        description="Populated when structured_output=true",
    )


class ChatHistoryMessage(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: list[ChatHistoryMessage]
