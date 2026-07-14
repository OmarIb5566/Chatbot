import logging

import requests

from app.config import settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """The OpenAI LLM could not be reached or returned an error."""


def chat(messages: list[dict[str, str]], temperature: float = 0.0) -> str:
    """Send a chat completion request to the OpenAI API."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
    payload = {
        "model": settings.openai_model,
        "messages": messages,
        "temperature": temperature,
    }
    try:
        resp = requests.post(
            url, json=payload, headers=headers, timeout=settings.openai_request_timeout_s
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise LLMError(f"Could not reach OpenAI API (model={settings.openai_model}): {exc}") from exc

    data = resp.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content:
        raise LLMError(f"OpenAI returned an empty response: {data}")
    return content


def health_check() -> bool:
    try:
        headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
        resp = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=5)
        resp.raise_for_status()
        models = [m["id"] for m in resp.json().get("data", [])]
        return settings.openai_model in models
    except requests.RequestException:
        return False


# ---------------------------------------------------------------------------
# Previous local Ollama implementation - kept for reference / easy rollback.
# To switch back: uncomment this block and remove/comment the OpenAI one above.
# ---------------------------------------------------------------------------
# def chat(messages: list[dict[str, str]], temperature: float = 0.0) -> str:
#     """Send a chat completion request to the local Ollama server.
#
#     A fixed seed is pinned so identical prompts are far more likely to
#     produce identical SQL - local CPU inference isn't perfectly
#     deterministic even at temperature 0, but seeding removes the sampler
#     as a source of variance.
#     """
#     url = f"{settings.ollama_host}/api/chat"
#     payload = {
#         "model": settings.ollama_model,
#         "messages": messages,
#         "stream": False,
#         "options": {"temperature": temperature, "seed": settings.ollama_seed},
#     }
#     try:
#         resp = requests.post(url, json=payload, timeout=settings.ollama_request_timeout_s)
#         resp.raise_for_status()
#     except requests.RequestException as exc:
#         raise LLMError(
#             f"Could not reach local Ollama at {settings.ollama_host} "
#             f"(model={settings.ollama_model}): {exc}"
#         ) from exc
#
#     data = resp.json()
#     content = data.get("message", {}).get("content", "")
#     if not content:
#         raise LLMError(f"Ollama returned an empty response: {data}")
#     return content
#
#
# def health_check() -> bool:
#     try:
#         resp = requests.get(f"{settings.ollama_host}/api/tags", timeout=5)
#         resp.raise_for_status()
#         models = [m["name"] for m in resp.json().get("models", [])]
#         return settings.ollama_model in models
#     except requests.RequestException:
#         return False
