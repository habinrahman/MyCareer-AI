from __future__ import annotations

import re
import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator


class LeadCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=8, max_length=32)
    analysis_id: str | None = Field(default=None, max_length=36)

    @field_validator("full_name", "phone", mode="before")
    @classmethod
    def strip_ws(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("phone")
    @classmethod
    def phone_chars(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if len(digits) < 8:
            raise ValueError("Phone number must contain at least 8 digits")
        if len(v) > 32:
            raise ValueError("Phone number is too long")
        return v

    @field_validator("analysis_id")
    @classmethod
    def optional_uuid(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        try:
            uuid.UUID(v)
        except ValueError as exc:
            raise ValueError("analysis_id must be a valid UUID") from exc
        return v


class LeadCreatedResponse(BaseModel):
    message: str = "Lead captured successfully"
    lead_id: str | None = Field(
        default=None,
        description="UUID of the inserted row in public.resume_download_leads (when insert succeeded).",
    )
