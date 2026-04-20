from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str
    environment: str
    database: str = Field(
        description="connected | degraded | unknown",
    )


class DatabaseHealthResponse(BaseModel):
    """Dedicated Postgres connectivity probe (Supabase-compatible)."""

    status: str = Field(description="ok when SELECT 1 succeeds")
    database: str = Field(description="connected | disconnected")
