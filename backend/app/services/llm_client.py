import json
import logging
import re
from typing import Any, Literal, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.config import settings
from app.services.llm_normalize import normalize_llm_payload
from app.services.llm_schema import model_json_schema
from app.structured_logging import log_event, log_timing

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

MISTRAL_CHAT_URL = "https://api.mistral.ai/v1/chat/completions"

FORMAT_SYSTEM = (
    "You extract structured hiring data. "
    "Respond with JSON only, matching the requested schema. "
    "Use normal JSON numbers for confidence (0-1, at most 2 decimal places)."
)

ResponseMode = Literal["json_schema", "json_object"]


class LLMError(Exception):
    pass


def _httpx_timeout() -> httpx.Timeout:
    return httpx.Timeout(settings.llm_timeout_seconds, connect=30.0)


def _auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.mistral_api_key}"}


def _api_key_configured() -> bool:
    return bool(settings.mistral_api_key.strip())


async def check_health() -> tuple[bool, bool]:
    """Returns (llm_reachable, model_ready). model_ready = API key set (or mock)."""
    if settings.mock_llm:
        return True, True
    if not _api_key_configured():
        return False, False
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            resp = await client.get(
                f"{settings.mistral_base_url.rstrip('/')}/models",
                headers=_auth_headers(),
            )
            return resp.status_code == 200, True
    except httpx.HTTPError:
        return False, _api_key_configured()


async def ensure_model_ready() -> None:
    if settings.mock_llm:
        return
    if not _api_key_configured():
        raise LLMError(
            "MISTRAL_API_KEY is not set. Add it to .env or set MOCK_LLM=true for offline dev."
        )
    reachable, _ = await check_health()
    if not reachable:
        raise LLMError(
            "Cannot reach Mistral API. Check MISTRAL_API_KEY and network access to api.mistral.ai."
        )


def _mistral_error_message(status: int, detail: str) -> str:
    if status == 401:
        return f"Mistral API unauthorized: invalid MISTRAL_API_KEY ({detail})"
    if status == 429:
        return f"Mistral API rate limited: {detail}"
    return f"Mistral API request failed ({status}): {detail}"


def _response_detail(resp: httpx.Response) -> str:
    try:
        body = resp.json()
        if isinstance(body, dict):
            err = body.get("message") or body.get("detail")
            if err:
                return str(err)[:300]
    except json.JSONDecodeError:
        pass
    text = resp.text.strip()
    return text[:300] if text else resp.reason_phrase


def _strip_json_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```\s*$", "", text)
    return text.strip()


def _sanitize_json_text(text: str) -> str:
    """Fix common Mistral glitches: runaway repeated digits in numbers."""
    text = _strip_json_fences(text)

    def _cap_decimal(match: re.Match[str]) -> str:
        try:
            return str(round(float(match.group(0)), 2))
        except ValueError:
            return match.group(0)

    text = re.sub(r"\d+\.\d+", _cap_decimal, text)
    # Collapse absurd integer runs (e.g. 555555…)
    text = re.sub(r"\d{25,}", "0", text)
    return text


def _repair_json_string(text: str) -> str:
    text = _sanitize_json_text(text)
    return re.sub(r",\s*([}\]])", r"\1", text)


def _loads_json_object(raw: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str) or not raw.strip():
        raise LLMError("Empty JSON from model")

    text = _sanitize_json_text(raw)
    last_error: json.JSONDecodeError | None = None
    for candidate in (text, _repair_json_string(text)):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
            raise LLMError("Expected JSON object from model")
        except json.JSONDecodeError as e:
            last_error = e

    pos = last_error.pos if last_error and last_error.pos is not None else 0
    snippet = text[max(0, pos - 40) : pos + 40]
    raise LLMError(f"Invalid JSON from model near: …{snippet}…") from last_error


def _sanitize_parsed_dict(node: Any) -> Any:
    if isinstance(node, dict):
        out: dict[str, Any] = {}
        for k, v in node.items():
            if k == "confidence" and isinstance(v, (int, float)):
                out[k] = round(max(0.0, min(1.0, float(v))), 2)
            else:
                out[k] = _sanitize_parsed_dict(v)
        return out
    if isinstance(node, list):
        return [_sanitize_parsed_dict(item) for item in node]
    return node


def _parse_model_output(raw: str | dict[str, Any], model_class: type[T]) -> T:
    data = _loads_json_object(raw) if isinstance(raw, str) else raw
    if isinstance(data, dict):
        data = _sanitize_parsed_dict(data)
        data = normalize_llm_payload(data, model_class)
    return model_class.model_validate(data)


def _extract_message_content(body: dict[str, Any]) -> str | dict[str, Any]:
    choices = body.get("choices") or []
    if not choices:
        raise LLMError("Mistral API returned no choices")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, dict):
        return content
    if isinstance(content, str):
        return content
    if content is None:
        parsed = message.get("parsed")
        if isinstance(parsed, dict):
            return parsed
    raise LLMError("Mistral API returned empty message content")


def _schema_strict(model_class: type[BaseModel]) -> bool:
    """Strict json_schema enforces shape (e.g. profile + match). Numbers fixed post-parse."""
    return model_class.__name__ == "ResumeScreeningResult"


def _response_modes(model_class: type[BaseModel]) -> list[ResponseMode]:
    # Unstructured json_object retry drops profile; keep schema-only for screening.
    if model_class.__name__ == "ResumeScreeningResult":
        return ["json_schema"]
    return ["json_schema", "json_object"]


def _response_format_payload(
    model_class: type[BaseModel],
    mode: ResponseMode,
) -> dict[str, Any]:
    if mode == "json_object":
        return {"type": "json_object"}
    return {
        "type": "json_schema",
        "json_schema": {
            "name": model_class.__name__,
            "strict": _schema_strict(model_class),
            "schema": model_json_schema(model_class),
        },
    }


async def _post_chat(
    client: httpx.AsyncClient,
    payload: dict[str, Any],
) -> dict[str, Any]:
    resp = await client.post(MISTRAL_CHAT_URL, headers=_auth_headers(), json=payload)
    if resp.status_code >= 400:
        raise LLMError(_mistral_error_message(resp.status_code, _response_detail(resp)))
    return resp.json()


async def _generate_with_mode(
    client: httpx.AsyncClient,
    prompt: str,
    model_class: type[T],
    *,
    system: str | None,
    mode: ResponseMode,
) -> T:
    payload = {
        "model": settings.mistral_model,
        "temperature": 0.1,
        "max_tokens": settings.llm_max_tokens,
        "messages": [
            {"role": "system", "content": system or FORMAT_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "response_format": _response_format_payload(model_class, mode),
    }
    body = await _post_chat(client, payload)
    content = _extract_message_content(body)
    return _parse_model_output(content, model_class)


def _is_json_parse_error(exc: BaseException) -> bool:
    return isinstance(exc, LLMError) and (
        "Invalid JSON" in str(exc) or "Empty JSON" in str(exc)
    )


async def generate_json(
    prompt: str,
    model_class: type[T],
    system: str | None = None,
    *,
    step: str | None = None,
) -> T:
    """Run an LLM step via Mistral; retry with json_object if schema output is invalid."""
    step_name = step or model_class.__name__
    llm_fields = {
        "step": step_name,
        "model": settings.mistral_model,
        "mock_llm": settings.mock_llm,
        "prompt_chars": len(prompt),
    }

    if settings.mock_llm:
        from app.services.mock_llm import mock_response

        with log_timing(logger, "llm_call", **llm_fields):
            return mock_response(prompt, model_class)

    await ensure_model_ready()

    modes = _response_modes(model_class)
    last_error: Exception | None = None

    async with httpx.AsyncClient(timeout=_httpx_timeout()) as client:
        for attempt, mode in enumerate(modes, start=1):
            try:
                with log_timing(logger, "llm_call", **llm_fields, response_mode=mode):
                    return await _generate_with_mode(
                        client,
                        prompt,
                        model_class,
                        system=system,
                        mode=mode,
                    )
            except httpx.TimeoutException as e:
                log_event(
                    logger,
                    "llm_call.timeout",
                    level=logging.ERROR,
                    step=step_name,
                    timeout_seconds=settings.llm_timeout_seconds,
                )
                raise LLMError(
                    f"Mistral timed out after {settings.llm_timeout_seconds:.0f}s. "
                    "Try fewer resumes or MOCK_LLM=true."
                ) from e
            except (json.JSONDecodeError, ValidationError, KeyError, TypeError) as e:
                log_event(
                    logger,
                    "llm_call.invalid_response",
                    level=logging.ERROR,
                    step=step_name,
                    error_type=type(e).__name__,
                    error=str(e),
                    response_mode=mode,
                )
                last_error = LLMError(f"LLM response invalid: {e}")
            except LLMError as e:
                last_error = e
                if _is_json_parse_error(e) and attempt < len(modes):
                    log_event(
                        logger,
                        "llm_call.retry",
                        level=logging.WARNING,
                        step=step_name,
                        response_mode=mode,
                        next_mode=modes[attempt],
                        error=str(e)[:200],
                    )
                    continue
                raise

    if last_error:
        raise last_error
    raise LLMError("LLM call failed with no response")
