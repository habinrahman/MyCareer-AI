from openai import AsyncOpenAI

from app.prompts.career import CAREER_CHAT_SYSTEM, RESUME_SUMMARY_SYSTEM


async def summarize_resume_text(
    client: AsyncOpenAI,
    model: str,
    resume_text: str,
) -> str:
    text = resume_text.strip()
    if len(text) > 120_000:
        text = text[:120_000]
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": RESUME_SUMMARY_SYSTEM},
            {"role": "user", "content": text},
        ],
        temperature=0.3,
    )
    return (response.choices[0].message.content or "").strip()


async def embed_text(
    client: AsyncOpenAI,
    model: str,
    text: str,
) -> list[float]:
    chunk = text.strip()
    if len(chunk) > 30_000:
        chunk = chunk[:30_000]
    response = await client.embeddings.create(model=model, input=chunk)
    return list(response.data[0].embedding)


async def career_chat(
    client: AsyncOpenAI,
    model: str,
    messages: list[dict[str, str]],
    resume_context: str | None,
) -> str:
    sys_content = CAREER_CHAT_SYSTEM
    if resume_context:
        sys_content += (
            "\n\nRelevant resume excerpt (may be truncated):\n" + resume_context[:24_000]
        )
    payload = [{"role": "system", "content": sys_content}, *messages]
    response = await client.chat.completions.create(
        model=model,
        messages=payload,
        temperature=0.5,
    )
    return (response.choices[0].message.content or "").strip()


async def mentor_chat_completion(
    client: AsyncOpenAI,
    model: str,
    system_prompt: str,
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.3,
    top_p: float = 0.9,
    presence_penalty: float = 0.2,
    frequency_penalty: float = 0.1,
) -> str:
    payload = [{"role": "system", "content": system_prompt}, *messages]
    response = await client.chat.completions.create(
        model=model,
        messages=payload,
        temperature=temperature,
        top_p=top_p,
        presence_penalty=presence_penalty,
        frequency_penalty=frequency_penalty,
    )
    return (response.choices[0].message.content or "").strip()


async def mentor_chat_structured_raw(
    client: AsyncOpenAI,
    model: str,
    system_prompt: str,
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.3,
    top_p: float = 0.9,
    presence_penalty: float = 0.2,
    frequency_penalty: float = 0.1,
) -> str:
    payload = [{"role": "system", "content": system_prompt}, *messages]
    response = await client.chat.completions.create(
        model=model,
        messages=payload,
        response_format={"type": "json_object"},
        temperature=temperature,
        top_p=top_p,
        presence_penalty=presence_penalty,
        frequency_penalty=frequency_penalty,
    )
    return (response.choices[0].message.content or "").strip()
