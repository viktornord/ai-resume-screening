"""Deterministic hints from raw JD text when the LLM omits role/leadership fields."""

import re

_VALID_SENIORITY = ("junior", "mid", "senior", "lead", "unknown")

_TITLE_KEYWORDS = re.compile(
    r"\b(?:engineer|developer|architect|scientist|manager|analyst|designer|lead)\b",
    re.I,
)


def clean_jd_text(jd_text: str) -> str:
    """Strip common PDF/scrape noise before sending text to the LLM."""
    lines: list[str] = []
    for line in jd_text.splitlines():
        s = line.strip()
        if not s:
            lines.append("")
            continue
        if re.match(r"https?://", s):
            continue
        if re.search(r"^\d{1,2}/\d{1,2}/\d{2,4}", s) and re.search(r"\d+/\d+\s*$", s):
            continue
        if re.match(r"\d+\s*min\.\s*read", s, re.I):
            continue
        if re.fullmatch(r"view original", s, re.I):
            continue
        lines.append(line)

    text = "\n".join(lines)
    text = re.sub(r"[·•]\s*", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _clean_title(raw: str) -> str:
    title = re.sub(r"\s+", " ", raw).strip(" -–—|")
    title = re.sub(r"\d+\s*min\.\s*read.*$", "", title, flags=re.I).strip()
    return title[:200]


def extract_job_title(jd_text: str) -> str | None:
    """Best-effort job title from JD header lines."""
    lines = [ln.strip() for ln in jd_text.splitlines() if ln.strip()]
    head = "\n".join(lines[:25])
    blob = re.sub(r"\s+", " ", head)

    patterns = [
        r"[-–—]\s*((?:Lead\s+)?(?:AI\s+)?Engineer[^.]{5,120}?)(?:\s+About\b|\s+https?://|$)",
        r"\b((?:Lead\s+)?(?:AI\s+)?Engineer\s*[—–-]\s*[^.]{3,100}?)(?:\s+About\b|\s+https?://|$)",
        r"^[^\n]{0,40}[-–—]\s*([^\n]{8,120}?Engineer[^\n]{0,80})",
    ]
    for pattern in patterns:
        match = re.search(pattern, blob, re.I)
        if match:
            return _clean_title(match.group(1))

    joined = re.sub(r"\n+", " ", head)
    match = re.search(
        r"\b(Lead\s+AI\s+Engineer\s*[—–-]\s*[^.]{3,100}?)(?:\s+About\b|\s+https?://|$)",
        joined,
        re.I,
    )
    if match:
        return _clean_title(match.group(1))

    for line in lines[:12]:
        if _TITLE_KEYWORDS.search(line) and 8 <= len(line) <= 120:
            if "about the role" in line.lower():
                continue
            cleaned = _clean_title(line)
            if cleaned:
                return cleaned
    return None


def infer_seniority(title: str, jd_text: str) -> str:
    title_l = title.lower()
    text_l = jd_text.lower()
    if re.search(r"\blead\b", title_l) or "lead individual contributor" in text_l:
        return "lead"
    if re.search(r"\bsenior\b", title_l) or "senior " in text_l:
        return "senior"
    if re.search(r"\bjunior\b", title_l):
        return "junior"
    if re.search(r"\b(principal|staff)\b", title_l):
        return "senior"
    if re.search(r"\b(mid[- ]level|intermediate)\b", text_l):
        return "mid"
    return "unknown"


def _jd_requires_people_management(text_l: str) -> bool:
    if re.search(
        r"not managing a team|you are not managing|no direct reports|"
        r"not a people manager|without direct reports",
        text_l,
    ):
        return False
    return bool(
        re.search(
            r"(?:will|you(?:'ll| will))\s+manage\s+(?:a\s+)?team|"
            r"people management|direct reports|performance reviews|"
            r"hire and lead a team|managing engineers",
            text_l,
        )
    )


def infer_leadership(title: str, jd_text: str) -> dict[str, bool]:
    """
    Defaults: tech_lead=False, team_lead=False.
    Title/body 'lead' (IC) -> tech_lead True; team_lead only with explicit people mgmt.
    """
    title_l = title.lower()
    text_l = jd_text.lower()

    team_lead = _jd_requires_people_management(text_l)

    tech_lead = False
    if re.search(r"\blead\b", title_l):
        tech_lead = True
    if "lead individual contributor" in text_l or "technical owner" in text_l:
        tech_lead = True
    if re.search(r"tech(nical)?\s+lead|tech_lead", text_l):
        tech_lead = True

    return {"tech_lead": tech_lead, "team_lead": team_lead}


def infer_jd_hints(jd_text: str) -> dict[str, object]:
    title = extract_job_title(jd_text) or ""
    seniority = infer_seniority(title, jd_text) if title else "unknown"
    if seniority not in _VALID_SENIORITY:
        seniority = "unknown"
    leadership = infer_leadership(title, jd_text) if title else {"tech_lead": False, "team_lead": False}
    return {
        "title": title,
        "seniority": seniority,
        "tech_lead": leadership["tech_lead"],
        "team_lead": leadership["team_lead"],
    }
