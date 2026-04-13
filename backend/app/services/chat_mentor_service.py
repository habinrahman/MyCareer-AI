"""Career mentor chat: RAG (pgvector), OpenAI, persistence, optional streaming."""

import logging
import re
from collections.abc import AsyncIterator

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.database import AsyncSessionLocal
from app.prompts.mentor import (
    CAREER_MENTOR_BASE,
    CAREER_MENTOR_RETRIEVAL_WRAPPER,
    CAREER_MENTOR_STRUCTURED_SUFFIX,
)
from app.schemas.chat import ChatResponse, MentorStructuredBlock, MentorStructuredJSON
from app.services import openai_service, persistence
from app.utils.sse import sse_encode
from app.utils.vectors import format_vector

logger = logging.getLogger(__name__)

# Shared OpenAI sampling for mentor chat (non-stream + stream + structured JSON).
_MENTOR_TEMPERATURE = 0.3
_MENTOR_TOP_P = 0.9
_MENTOR_PRESENCE_PENALTY = 0.2
_MENTOR_FREQUENCY_PENALTY = 0.1

# Cap for merged RAG retrieval text injected into the system prompt (performance + focus).
RAG_CONTEXT_CHAR_LIMIT = 12_000

# Fallback excerpt when RAG is empty (fits under RAG cap).
_FALLBACK_EXCERPT_MAX = 8_000

_EMPTY_REPLY_FALLBACK = (
    "I wasn't able to produce a full answer just now. Could you rephrase your question "
    "or share what role or skill you want to focus on?"
)

_STREAM_FAILURE_FALLBACK = (
    "Something went wrong while generating the reply. Please try sending your message again."
)


def clean_markdown(text: str) -> str:
    """Strip common Markdown markers for plain-text mentor replies (API-safe, idempotent-ish)."""
    if not text:
        return ""
    s = text.replace("\r\n", "\n")
    # Fenced code blocks: drop fences, keep inner body when simple.
    s = re.sub(r"^```[^\n]*\n", "", s, flags=re.MULTILINE)
    s = s.replace("```", "")
    # ATX headings
    s = re.sub(r"(?m)^#{1,6}\s+", "", s)
    # Bold / strong (repeat to unwrap nested-looking patterns)
    for _ in range(8):
        nxt = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
        nxt = re.sub(r"__([^_]+)__", r"\1", nxt)
        if nxt == s:
            break
        s = nxt
    # Italic single * or _ (conservative: single line chunks)
    s = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\1", s)
    s = re.sub(r"(?<!_)_([^_\n]+)_(?!_)", r"\1", s)
    # Images then links
    s = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
    # Inline code
    s = re.sub(r"`([^`]+)`", r"\1", s)
    # Horizontal rules
    s = re.sub(r"(?m)^\s*-{3,}\s*$", "", s)
    # Trim stray list markers at line starts if duplicated
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def _mentor_sampling_kwargs() -> dict[str, float]:
    return {
        "temperature": _MENTOR_TEMPERATURE,
        "top_p": _MENTOR_TOP_P,
        "presence_penalty": _MENTOR_PRESENCE_PENALTY,
        "frequency_penalty": _MENTOR_FREQUENCY_PENALTY,
    }


def _truncate_rag_block(text: str, limit: int = RAG_CONTEXT_CHAR_LIMIT) -> str:
    t = text.strip()
    if len(t) <= limit:
        return t
    marker = "\n[Context truncated for length]"
    head = limit - len(marker)
    return (t[:head] if head > 0 else t[:limit]) + marker


def _merge_retrieval_snippets(
    resume_snips: list[str], analysis_snips: list[str]
) -> str:
    parts: list[str] = []
    for i, s in enumerate(resume_snips, 1):
        parts.append(f"[Resume RAG {i}]\n{s}")
    for i, s in enumerate(analysis_snips, 1):
        parts.append(f"[Analysis RAG {i}]\n{s}")
    return _truncate_rag_block("\n\n".join(parts))


async def build_mentor_system_prompt(
    session: AsyncSession,
    *,
    user_id: str,
    query_vec_str: str,
    structured_output: bool,
) -> str:
    r_snips = await persistence.rag_resume_snippets(
        session, user_id=user_id, query_vec=query_vec_str
    )
    a_snips = await persistence.rag_analysis_snippets(
        session, user_id=user_id, query_vec=query_vec_str
    )
    retrieval = _merge_retrieval_snippets(r_snips, a_snips)
    if not retrieval.strip():
        fb = await persistence.latest_resume_excerpt(session, user_id)
        if fb:
            excerpt = fb.strip()[:_FALLBACK_EXCERPT_MAX]
            retrieval = _truncate_rag_block(f"[Latest resume excerpt]\n{excerpt}")

    system = CAREER_MENTOR_BASE
    if retrieval.strip():
        system += CAREER_MENTOR_RETRIEVAL_WRAPPER.format(retrieval_block=retrieval)
    if structured_output:
        system += CAREER_MENTOR_STRUCTURED_SUFFIX

    base_len = len(CAREER_MENTOR_BASE)
    retrieval_chars = len(retrieval) if retrieval.strip() else 0
    logger.info(
        "mentor.system_prompt user=%s base_chars=%d retrieval_chars=%d total_chars=%d "
        "resume_snippets=%d analysis_snippets=%d structured=%s",
        user_id,
        base_len,
        retrieval_chars,
        len(system),
        len(r_snips),
        len(a_snips),
        structured_output,
    )
    return system


async def _resolve_session_id(
    session: AsyncSession,
    user_id: str,
    session_id: str | None,
    first_user_text: str,
) -> str:
    sid = session_id
    if sid and not await persistence.verify_chat_session(
        session, session_id=sid, user_id=user_id
    ):
        sid = None
    if not sid:
        title = (
            (first_user_text[:120] + "…")
            if len(first_user_text) > 120
            else first_user_text
        )
        sid = await persistence.insert_chat_session(
            session,
            user_id=user_id,
            title=title,
            resume_id=None,
        )
    return sid


def _plain_reply(text: str, *, fallback: str = _EMPTY_REPLY_FALLBACK) -> str:
    """Normalize mentor user-visible text: trim, then strip Markdown; use fallback if empty."""
    t = (text or "").strip()
    if not t:
        return fallback
    c = clean_markdown(t).strip()
    return c if c else fallback


async def run_mentor_turn(
    session: AsyncSession,
    settings: Settings,
    client: AsyncOpenAI,
    *,
    user_id: str,
    messages: list[dict[str, str]],
    session_id: str | None,
    structured_output: bool,
) -> ChatResponse:
    await persistence.ensure_user_row(session, user_id)
    user_query = messages[-1]["content"]

    q_emb = await openai_service.embed_text(
        client, settings.openai_embedding_model, user_query
    )
    vec_str = format_vector(q_emb)

    system = await build_mentor_system_prompt(
        session,
        user_id=user_id,
        query_vec_str=vec_str,
        structured_output=structured_output,
    )
    sid = await _resolve_session_id(session, user_id, session_id, user_query)

    await persistence.insert_chat_message(
        session,
        session_id=sid,
        role="user",
        content=user_query,
        model=None,
        embedding_str=vec_str,
    )

    kw = _mentor_sampling_kwargs()
    structured: MentorStructuredBlock | None = None
    if structured_output:
        raw = await openai_service.mentor_chat_structured_raw(
            client,
            settings.openai_chat_model,
            system,
            messages,
            **kw,
        )
        try:
            parsed = MentorStructuredJSON.model_validate_json(raw)
        except Exception:
            logger.warning(
                "mentor.structured_parse_failed user=%s session=%s",
                user_id,
                sid,
                exc_info=True,
            )
            reply = _plain_reply(raw)
        else:
            reply = _plain_reply(parsed.answer.strip() or raw)
            structured = MentorStructuredBlock(
                role_recommendations=[
                    clean_markdown(str(x)).strip() for x in parsed.role_recommendations
                ],
                skill_gap_notes=[clean_markdown(str(x)).strip() for x in parsed.skill_gap_notes],
                interview_prep=[clean_markdown(str(x)).strip() for x in parsed.interview_prep],
                learning_roadmap=[
                    clean_markdown(str(x)).strip() for x in parsed.learning_roadmap
                ],
            )
    else:
        reply = await openai_service.mentor_chat_completion(
            client,
            settings.openai_chat_model,
            system,
            messages,
            **kw,
        )
        reply = _plain_reply(reply)

    if not reply.strip():
        logger.warning("mentor.empty_reply_after_parse user=%s session=%s", user_id, sid)
        reply = _EMPTY_REPLY_FALLBACK

    reply_emb = format_vector(
        await openai_service.embed_text(
            client, settings.openai_embedding_model, reply[:30_000]
        )
    )
    await persistence.insert_chat_message(
        session,
        session_id=sid,
        role="assistant",
        content=reply,
        model=settings.openai_chat_model,
        embedding_str=reply_emb,
    )
    await session.commit()
    logger.info("mentor.turn user=%s session=%s structured=%s", user_id, sid, structured_output)
    return ChatResponse(reply=reply, session_id=sid, structured=structured)


async def stream_mentor_turn(
    settings: Settings,
    client: AsyncOpenAI,
    *,
    user_id: str,
    messages: list[dict[str, str]],
    session_id: str | None,
) -> AsyncIterator[bytes]:
    """SSE stream: `token` chunks then `done` with session_id. Uses its own DB session."""
    async with AsyncSessionLocal() as session:
        await persistence.ensure_user_row(session, user_id)
        user_query = messages[-1]["content"]

        q_emb = await openai_service.embed_text(
            client, settings.openai_embedding_model, user_query
        )
        vec_str = format_vector(q_emb)

        system = await build_mentor_system_prompt(
            session,
            user_id=user_id,
            query_vec_str=vec_str,
            structured_output=False,
        )
        sid = await _resolve_session_id(session, user_id, session_id, user_query)

        await persistence.insert_chat_message(
            session,
            session_id=sid,
            role="user",
            content=user_query,
            model=None,
            embedding_str=vec_str,
        )
        await session.commit()

        parts: list[str] = []
        kw = _mentor_sampling_kwargs()
        payload = [{"role": "system", "content": system}, *messages]
        full_reply: str

        try:
            stream = await client.chat.completions.create(
                model=settings.openai_chat_model,
                messages=payload,
                stream=True,
                **kw,
            )
        except Exception:
            logger.exception(
                "mentor.stream_create_failed user=%s session=%s",
                user_id,
                sid,
            )
            full_reply = _STREAM_FAILURE_FALLBACK
            yield sse_encode({"type": "token", "text": full_reply})
        else:
            try:
                async for chunk in stream:
                    choice = chunk.choices[0] if chunk.choices else None
                    if not choice:
                        continue
                    delta = choice.delta.content or ""
                    if delta:
                        parts.append(delta)
                        yield sse_encode({"type": "token", "text": delta})
            except Exception:
                logger.exception(
                    "mentor.stream_iterate_failed user=%s session=%s",
                    user_id,
                    sid,
                )
                partial = "".join(parts).strip()
                full_reply = _plain_reply(
                    partial if partial else _STREAM_FAILURE_FALLBACK,
                    fallback=_STREAM_FAILURE_FALLBACK,
                )
                if not partial:
                    yield sse_encode({"type": "token", "text": full_reply})
            else:
                full_reply = _plain_reply(
                    "".join(parts), fallback=_STREAM_FAILURE_FALLBACK
                )

        full_reply = _plain_reply(full_reply, fallback=_STREAM_FAILURE_FALLBACK)

        reply_emb = format_vector(
            await openai_service.embed_text(
                client, settings.openai_embedding_model, full_reply[:30_000]
            )
        )

        try:
            await persistence.insert_chat_message(
                session,
                session_id=sid,
                role="assistant",
                content=full_reply,
                model=settings.openai_chat_model,
                embedding_str=reply_emb,
            )
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception(
                "mentor.stream_assistant_persist_failed user=%s session=%s",
                user_id,
                sid,
            )
            raise

        yield sse_encode({"type": "done", "session_id": sid})
