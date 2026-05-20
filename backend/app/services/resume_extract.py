from app.config import settings
from app.models.candidate_profile import CandidateProfile
from app.services.ollama_client import generate_json
from app.services.prompt_loader import load_prompt


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 50] + "\n\n[... truncated ...]"


async def extract_profile(cv_text: str, filename: str = "") -> CandidateProfile:
    hint = f"\nCANDIDATE NAME HINT: {filename}\n" if filename else ""
    prompt = load_prompt(
        "resume_extract.txt",
        cv_text=hint + _truncate(cv_text, settings.max_resume_chars),
    )
    return await generate_json(prompt, CandidateProfile)
