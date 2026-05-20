"""Single source of truth for LLM field descriptions (prompts + Pydantic)."""

ROLE_TITLE = "Job title as written or best short label."
ROLE_SENIORITY = "junior | mid | senior | lead | unknown from title/level wording."
TECH_NAME = "Technology, language, framework, or tool name."
TECH_MIN_YEARS = (
    "Minimum years using this tech in an IT/software role for this JD; "
    "null if JD does not state a duration. Not generic employment length."
)
TECH_PRIORITY = "must if required; nice if optional/preferred."
TECH_CV_YEARS = (
    "Estimated years using this tech in IT/software roles. "
    "Follow Prompt constraints: Technology years; null if not estimable."
)
SOFT_SKILL = "Non-technical behaviors (communication, ownership, etc.)."
TECH_LEAD = "Technical leadership (architecture, mentoring, lead IC) — not HR people management."
TEAM_LEAD = "People management (direct reports, hiring, performance reviews)."
EDU_MIN_LEVEL = "Minimum degree level if stated."
EDU_FIELDS = "Acceptable majors/fields; OR only (any one satisfies)."
EDU_REQUIRED = "true if degree is mandatory."
EDU_ITEM_LEVEL = "Degree or certification level."
EDU_ITEM_FIELD = "Major or field of study."
EXP_MIN_TOTAL = (
    "Minimum IT / relevant professional years for the role. "
    "Exclude unrelated jobs unless JD explicitly counts general experience. "
    "null if not stated."
)
EXP_TOTAL = (
    "Total years in IT / relevant professional roles. "
    "Exclude non-IT career time unless clearly tied to the target role. "
    "null if not inferable."
)
IDENTITY_NAME = "Candidate full name from resume header."
REASONING = "One paragraph: overall reading of the document or match."
AMBIGUITIES = "Bullet-level unclear points (empty array if none)."
SECTION_CONFIDENCE = "0-1 confidence for that section only."
MATCH_SKILL_NAME = "Skill that appears on CV and is relevant to JD."
YEARS_MATCH = (
    "clear | not_enough | ambiguous | n/a — compare JD min_years vs CV per-tech years; "
    "also consider min_total_years vs total_years when JD states overall IT experience."
)
MATCH_SKILL_DESC = "One short line: match quality for this skill."
NOT_MENTIONED_NAME = "JD must/nice tech absent from CV (may be omission, not gap)."
NOT_MENTIONED_DESC = "Why it matters; suggest clarification if critical."
MATCH_SCORE = "0-100 conservative overall fit."

PROMPT_CONSTRAINTS = """
EXTRACTION / MATCHING RULES

Evidence & hallucination:
- List a technology only if it appears in the resume or JD text.
- Do not invent employers, projects, or durations not supported by text.
- If evidence is weak, lower section confidence and add object-level ambiguities[].

Technology years (CV extract + match):
- Count years per tech within dated project windows when described; prefer over company tenure.
- Outsource/outstaff/consulting: never equate agency employment length with tech years.
- Skills list without dates: do not assign multi-year tenure; use null or low confidence.
- Overlapping roles: do not double-count calendar time per tech.

Total IT years:
- Sum dated IT role intervals; exclude clearly non-IT jobs unless JD asks otherwise.
- Do not use full company tenure at outsource shops without project detail.

Leadership & education:
- tech_lead / team_lead require behavioral or title evidence.
- Education fields: OR only; if JD implies AND, note in ambiguities.

Match scoring:
- years_match clear only when JD and CV evidence align with same scope.
- not_mentioned_skills: absence from CV is not proof candidate lacks the skill.
- When in doubt: lower confidence, add ambiguities, prefer raw JD/CV in match.
"""
