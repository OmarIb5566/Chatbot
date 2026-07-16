import logging

from openai import OpenAI, OpenAIError

from app.config import settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """The OpenAI API could not be reached or returned an error."""


def _client() -> OpenAI:
    return OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        timeout=settings.openai_request_timeout_s,
    )


def chat(messages: list[dict[str, str]], temperature: float = 0.0) -> str:
    """Send a chat completion request to the OpenAI API."""
    try:
        resp = _client().chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=temperature,
        )
    except OpenAIError as exc:
        raise LLMError(
            f"OpenAI API error (model={settings.openai_model}): {exc}"
        ) from exc

    content = resp.choices[0].message.content or ""
    if not content:
        raise LLMError("OpenAI returned an empty response.")
    return content


def health_check() -> bool:
    try:
        _client().models.retrieve(settings.openai_model)
        return True
    except OpenAIError:
        return False
