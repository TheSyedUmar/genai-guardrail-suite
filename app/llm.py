"""Thin wrapper around the OpenAI SDK, pointed at Groq's free endpoint."""
from openai import OpenAI

from app import config

# max_retries makes the SDK automatically wait and retry when Groq's free tier
# returns 429 (rate limit), so tests don't fail just because we were too fast.
client = OpenAI(
    api_key=config.GROQ_API_KEY or "missing-key",
    base_url=config.LLM_BASE_URL,
    max_retries=6,
    timeout=60,
)


def chat(messages: list[dict], model: str | None = None) -> str:
    """Send messages to the LLM and return the reply text."""
    response = client.chat.completions.create(
        model=model or config.CHAT_MODEL,
        messages=messages,
        temperature=0,  # as repeatable as possible, which matters for testing
    )
    return response.choices[0].message.content or ""
