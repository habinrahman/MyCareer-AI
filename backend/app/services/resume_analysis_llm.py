"""OpenAI structured JSON analysis for resumes (NLP layer)."""

import json
import logging
from typing import Any

from openai import AsyncOpenAI

from app.prompts.resume_analysis import (
    RESUME_ANALYSIS_SYSTEM,
    RESUME_ANALYSIS_USER_PREFIX,
    RESUME_ANALYSIS_USER_SUFFIX,
)
from app.schemas.resume_analysis import ResumeAnalysisOutput

logger = logging.getLogger(__name__)

MAX_RESUME_CHARS = 100_000


def _repair_prompt(bad_json: str, error: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": "You fix invalid JSON. Reply with a single valid JSON object only, no markdown.",
        },
        {
            "role": "user",
            "content": f"The following JSON failed validation ({error}). Return corrected JSON only:\n{bad_json[:25_000]}",
        },
    ]


def _parse_and_validate(content: str) -> ResumeAnalysisOutput:
    data: Any = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError("root must be object")
    return ResumeAnalysisOutput.model_validate(data)


async def analyze_resume_structured(
    client: AsyncOpenAI,
    model: str,
    resume_text: str,
) -> ResumeAnalysisOutput:
    """
    Run GPT-4o-mini (or compatible) with JSON mode and validate to ResumeAnalysisOutput.
    One repair retry on validation failure.
    """
    body = resume_text.strip()
    if len(body) > MAX_RESUME_CHARS:
        body = body[:MAX_RESUME_CHARS]

    user_message = (
        RESUME_ANALYSIS_USER_PREFIX + body + RESUME_ANALYSIS_USER_SUFFIX
    )

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": RESUME_ANALYSIS_SYSTEM},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    raw = (response.choices[0].message.content or "").strip()
    try:
        return _parse_and_validate(raw)
    except (json.JSONDecodeError, ValueError) as first_exc:
        logger.warning("resume_analysis.json_first_pass_failed: %s", first_exc)
        repair = await client.chat.completions.create(
            model=model,
            messages=_repair_prompt(raw, str(first_exc)),
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        fixed = (repair.choices[0].message.content or "").strip()
        return _parse_and_validate(fixed)
