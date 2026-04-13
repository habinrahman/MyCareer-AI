from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str
    environment: str
    database: str = Field(
        description="connected | degraded | unknown",
    )
