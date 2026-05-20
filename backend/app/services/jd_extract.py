import logging

from app.config import settings
from app.models.requirements import Requirements
from app.services.llm_client import generate_json
from app.services.prompt_loader import load_prompt
from app.structured_logging import log_event, log_timing, requirements_summary

logger = logging.getLogger(__name__)


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 50] + "\n\n[... truncated ...]"


async def extract_requirements(jd_text: str) -> Requirements:
    with log_timing(logger, "jd_extract", jd_chars=len(jd_text)):
        prompt = load_prompt(
            "jd_extract.md",
            jd_text=_truncate(jd_text, settings.max_jd_chars),
        )
        requirements = await generate_json(
            prompt,
            Requirements,
            step="jd_extract",
        )
    log_event(logger, "jd_extract.result", **requirements_summary(requirements))
    return requirements
