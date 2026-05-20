import json

from app.config import settings
from app.models.candidate_profile import CandidateProfile
from app.models.match import MatchResult
from app.models.requirements import Requirements
from app.services.ollama_client import generate_json
from app.services.prompt_loader import load_prompt


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 50] + "\n\n[... truncated ...]"


def _low_confidence_sections(
    requirements: Requirements,
    profile: CandidateProfile,
) -> list[str]:
    threshold = settings.confidence_threshold
    sections: list[str] = []
    req_sections = [
        ("role", requirements.role.confidence),
        ("technologies", requirements.technologies.confidence),
        ("soft_skills", requirements.soft_skills.confidence),
        ("leadership", requirements.leadership.confidence),
        ("education", requirements.education.confidence),
        ("experience", requirements.experience.confidence),
    ]
    for name, conf in req_sections:
        if conf < threshold:
            sections.append(f"requirements.{name}")
    prof_sections = [
        ("identity", profile.identity.confidence),
        ("technologies", profile.technologies.confidence),
        ("soft_skills", profile.soft_skills.confidence),
        ("leadership", profile.leadership.confidence),
        ("education", profile.education.confidence),
        ("experience", profile.experience.confidence),
    ]
    for name, conf in prof_sections:
        if conf < threshold:
            sections.append(f"candidate.{name}")
    return sections


def _requirements_block(req: Requirements) -> str:
    must = [t for t in req.technologies.items if t.priority == "must"]
    nice = [t for t in req.technologies.items if t.priority == "nice"]
    lines = [
        f"Title: {req.role.title} ({req.role.seniority})",
        f"Must-have tech: {', '.join(f'{t.name} ({t.min_years}+ yrs)' if t.min_years else t.name for t in must)}",
        f"Nice-to-have tech: {', '.join(t.name for t in nice)}",
        f"Min IT years: {req.experience.min_total_years}",
        f"Education: level={req.education.min_level}, fields={req.education.fields} (OR), required={req.education.required}",
        f"Tech lead: {req.leadership.tech_lead}, Team lead: {req.leadership.team_lead}",
    ]
    return "\n".join(lines)


def _candidate_block(profile: CandidateProfile) -> str:
    techs = ", ".join(
        f"{t.name} ({t.years} yrs)" if t.years is not None else t.name
        for t in profile.technologies.items
    )
    edu = ", ".join(f"{e.level} in {e.field}" for e in profile.education.items)
    return "\n".join(
        [
            f"Name: {profile.identity.name}",
            f"Technologies: {techs}",
            f"Total IT years: {profile.experience.total_years}",
            f"Education: {edu}",
            f"Tech lead: {profile.leadership.tech_lead}, Team lead: {profile.leadership.team_lead}",
        ]
    )


async def match_candidate(
    requirements: Requirements,
    profile: CandidateProfile,
    raw_jd: str,
    raw_cv: str,
) -> MatchResult:
    low = _low_confidence_sections(requirements, profile)
    prompt = load_prompt(
        "screening.txt",
        requirements_block=_requirements_block(requirements),
        candidate_block=_candidate_block(profile),
        low_confidence_sections=", ".join(low) if low else "none",
        jd_ambiguities=json.dumps(requirements.ambiguities),
        cv_ambiguities=json.dumps(profile.ambiguities),
        raw_jd=_truncate(raw_jd, settings.max_jd_chars),
        raw_cv=_truncate(raw_cv, settings.max_resume_chars),
    )
    result = await generate_json(prompt, MatchResult)
    if not result.candidate_name:
        result = result.model_copy(update={"candidate_name": profile.identity.name})
    return result
