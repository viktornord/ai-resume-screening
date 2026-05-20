import json
import logging
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.config import settings

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class OllamaError(Exception):
    pass


async def check_health() -> tuple[bool, bool]:
    """Returns (ollama_reachable, model_ready)."""
    if settings.mock_llm:
        return True, True
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            if resp.status_code != 200:
                return True, False
            data = resp.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            model_base = settings.ollama_model.split(":")[0]
            ready = any(model_base in name for name in models)
            return True, ready
    except httpx.HTTPError:
        return False, False


async def generate_json(
    prompt: str,
    model_class: type[T],
    system: str = "You are a precise JSON-only assistant. Respond with valid JSON only.",
) -> T:
    if settings.mock_llm:
        from app.services.mock_llm import mock_response

        return mock_response(prompt, model_class)

    schema = model_class.model_json_schema()
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "format": schema,
        "options": {"temperature": 0.1},
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        for attempt in range(2):
            try:
                resp = await client.post(
                    f"{settings.ollama_base_url}/api/generate",
                    json=payload,
                )
                resp.raise_for_status()
                raw = resp.json().get("response", "")
                data = json.loads(raw) if isinstance(raw, str) else raw
                return model_class.model_validate(data)
            except (httpx.HTTPError, json.JSONDecodeError, ValidationError) as e:
                logger.warning("LLM attempt %s failed: %s", attempt + 1, e)
                if attempt == 1:
                    raise OllamaError(f"LLM failed after retry: {e}") from e
    raise OllamaError("Unreachable")
