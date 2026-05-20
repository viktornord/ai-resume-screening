import json
import logging
import re

from app.config import settings
from app.models.requirements import Requirements
from app.models.resume_screening import ResumeScreeningResult
from app.services.llm_client import generate_json
from app.services.prompt_loader import load_prompt
from app.structured_logging import log_event, log_timing, resume_screening_summary

logger = logging.getLogger(__name__)

SCREEN_SYSTEM = (
    "Extract profile from the resume only; then match vs the job description. "
    "profile.technologies must list only tool/language names that literally appear on the CV — "
    "never copy JD requirements into profile, never infer stacks from job titles. "
    "Respond with JSON only: top-level keys profile and match (both required)."
)


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 50] + "\n\n[... truncated ...]"


def _clean_cv_text(cv_text: str) -> str:
    text = cv_text.replace("\xa0", " ")
    text = re.sub(r"[·•]\s*", "\n- ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _low_confidence_requirement_sections(requirements: Requirements) -> list[str]:
    threshold = settings.confidence_threshold
    sections: list[str] = []
    for name, conf in [
        ("role", requirements.role.confidence),
        ("technologies", requirements.technologies.confidence),
        ("soft_skills", requirements.soft_skills.confidence),
        ("leadership", requirements.leadership.confidence),
        ("education", requirements.education.confidence),
        ("experience", requirements.experience.confidence),
    ]:
        if conf < threshold:
            sections.append(f"requirements.{name}")
    return sections


def _requirements_block(req: Requirements) -> str:
    must = [t for t in req.technologies.items if t.priority == "must"]
    nice = [t for t in req.technologies.items if t.priority == "nice"]
    tech_lines = [
        "Technologies (per-item priority from JD extract — respect must vs nice):",
    ]
    for t in req.technologies.items:
        years = f", min_years={t.min_years}" if t.min_years is not None else ""
        tech_lines.append(f"  - {t.name}: priority={t.priority}{years}")
    lines = [
        f"Title: {req.role.title} ({req.role.seniority})",
        *tech_lines,
        f"Must-have summary: {', '.join(f'{t.name} ({t.min_years}+ yrs)' if t.min_years else t.name for t in must) or '(none)'}",
        f"Nice-to-have summary: {', '.join(t.name for t in nice) or '(none)'}",
        f"Min IT years: {req.experience.min_total_years}",
        f"Education: level={req.education.min_level}, fields={req.education.fields} (OR), required={req.education.required}",
        f"Tech lead: {req.leadership.tech_lead}, Team lead: {req.leadership.team_lead}",
    ]
    return "\n".join(lines)


async def screen_resume(
    requirements: Requirements,
    raw_jd: str,
    raw_cv: str,
    filename: str = "",
) -> ResumeScreeningResult:
    """One LLM call: CV → CandidateProfile + match vs Requirements."""
    resume_name = filename or "resume"
    cv_text = _clean_cv_text(raw_cv)
    low = _low_confidence_requirement_sections(requirements)

    with log_timing(
        logger,
        "screen_resume",
        resume=resume_name,
        cv_chars=len(cv_text),
        low_confidence_sections=low,
    ):
        prompt = load_prompt(
            "screen_resume.md",
            confidence_threshold=str(settings.confidence_threshold),
            requirements_block=_requirements_block(requirements),
            low_confidence_sections=", ".join(low) if low else "none",
            jd_ambiguities=json.dumps(requirements.ambiguities),
            raw_jd=_truncate(raw_jd, settings.max_jd_chars),
            raw_cv=_truncate(cv_text, settings.max_resume_chars),
        )
        result = await generate_json(
            prompt,
            ResumeScreeningResult,
            system=SCREEN_SYSTEM,
            step=f"screen_resume:{resume_name}",
        )

    if not result.match.candidate_name and result.profile.identity.name:
        result = result.model_copy(
            update={
                "match": result.match.model_copy(
                    update={"candidate_name": result.profile.identity.name}
                )
            }
        )

    log_event(
        logger,
        "screen_resume.result",
        resume=resume_name,
        **resume_screening_summary(result),
    )
    return result
