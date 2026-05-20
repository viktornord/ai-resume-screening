"""Resume text cleanup before LLM extraction (not skill inference)."""

import re


def clean_cv_text(cv_text: str) -> str:
    """Normalize PDF/scrape artifacts; preserve SKILLS and EMPLOYMENT HISTORY content."""
    text = cv_text.replace("\xa0", " ")
    text = re.sub(r"[·•]\s*", "\n- ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
