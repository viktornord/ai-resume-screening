from pathlib import Path

from app.schemas.field_descriptions import PROMPT_CONSTRAINTS

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(name: str, **kwargs: str) -> str:
    template = (PROMPTS_DIR / name).read_text(encoding="utf-8")
    base = {
        "prompt_constraints": PROMPT_CONSTRAINTS.strip(),
        **kwargs,
    }
    return template.format(**base)
