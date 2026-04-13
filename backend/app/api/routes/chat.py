from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.core.config import Settings
from app.core.dependencies import (
    get_current_user_id,
    get_db,
    get_openai_client,
    get_settings_dep,
)
from app.schemas.chat import (
    ChatHistoryMessage,
    ChatHistoryResponse,
    ChatRequest,
)
from app.middleware.rate_limit import limiter
from app.services.chat_mentor_service import run_mentor_turn, stream_mentor_turn
from app.services import persistence

router = APIRouter(tags=["Chat"])


@router.post(
    "/chat",
    summary="Career mentor chat (RAG + optional structured JSON or SSE streaming)",
    responses={
        200: {
            "description": "JSON body when stream=false; `text/event-stream` when stream=true",
            "content": {
                "application/json": {"schema": {}},
                "text/event-stream": {},
            },
        }
    },
)
@limiter.limit("30/minute")
async def chat(
    request: Request,
    body: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
    openai: AsyncOpenAI = Depends(get_openai_client),
):
    msgs = [{"role": m.role, "content": m.content} for m in body.messages]
    if not msgs or msgs[-1]["role"] != "user":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Last message must be from the user",
        )
    if body.stream and body.structured_output:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Cannot use stream=true with structured_output=true",
        )

    if body.stream:
        return StreamingResponse(
            stream_mentor_turn(
                settings,
                openai,
                user_id=user_id,
                messages=msgs,
                session_id=body.session_id,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return await run_mentor_turn(
        db,
        settings,
        openai,
        user_id=user_id,
        messages=msgs,
        session_id=body.session_id,
        structured_output=body.structured_output,
    )


@router.get(
    "/chat-history/{session_id}",
    response_model=ChatHistoryResponse,
    summary="Load persisted messages for a chat session (owner-only)",
)
@limiter.limit("60/minute")
async def chat_history(
    request: Request,
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ChatHistoryResponse:
    if not await persistence.verify_chat_session(
        db, session_id=session_id, user_id=user_id
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
    rows = await persistence.list_chat_history(
        db, session_id=session_id, user_id=user_id
    )
    messages = [
        ChatHistoryMessage(
            id=r["id"],
            role=r["role"],
            content=r["content"],
            created_at=str(r["created_at"]),
        )
        for r in rows
    ]
    return ChatHistoryResponse(session_id=session_id, messages=messages)
