from app.config import settings
from app.models.requirements import Requirements
from app.services.ollama_client import generate_json
from app.services.prompt_loader import load_prompt


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 50] + "\n\n[... truncated ...]"


async def extract_requirements(jd_text: str) -> Requirements:
    prompt = load_prompt(
        "jd_extract.txt",
        jd_text=_truncate(jd_text, settings.max_jd_chars),
    )
    return await generate_json(prompt, Requirements)
