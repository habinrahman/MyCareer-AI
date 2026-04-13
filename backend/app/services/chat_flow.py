"""Backward-compatible entrypoint for mentor chat (non-streaming)."""

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.schemas.chat import ChatResponse
from app.services.chat_mentor_service import run_mentor_turn


async def run_career_chat(
    session: AsyncSession,
    settings: Settings,
    client: AsyncOpenAI,
    *,
    user_id: str,
    messages: list[dict[str, str]],
    session_id: str | None,
) -> tuple[str, str | None]:
    """Legacy tuple API used by tests/callers expecting (reply, session_id)."""
    res = await run_mentor_turn(
        session,
        settings,
        client,
        user_id=user_id,
        messages=messages,
        session_id=session_id,
        structured_output=False,
    )
    return res.reply, res.session_id


async def run_career_chat_response(
    session: AsyncSession,
    settings: Settings,
    client: AsyncOpenAI,
    *,
    user_id: str,
    messages: list[dict[str, str]],
    session_id: str | None,
    structured_output: bool,
) -> ChatResponse:
    return await run_mentor_turn(
        session,
        settings,
        client,
        user_id=user_id,
        messages=messages,
        session_id=session_id,
        structured_output=structured_output,
    )
