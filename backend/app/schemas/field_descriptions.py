"""Single source of truth for LLM field descriptions (prompts + Pydantic)."""

ROLE_TITLE = "Job title as written or best short label."
ROLE_SENIORITY = "junior | mid | senior | lead | unknown from title/level wording."
TECH_NAME = "Technology, language, framework, or tool name."
TECH_MIN_YEARS = (
    "Minimum years using this tech in an IT/software role for this JD; "
    "null if JD does not state a duration. Not generic employment length."
)
TECH_PRIORITY = (
    "must | nice only. must = required/primary/deep hands-on/qualification bullet without "
    "'plus' or 'preferred'. nice = explicit plus/preferred/optional, or company stack listed "
    "only under Technology Context without a separate requirement sentence."
)
TECH_CV_YEARS = (
    "Estimated years using this tech in IT/software roles from dated EMPLOYMENT HISTORY "
    "where that tech appears; null if only in undated SKILLS list. "
    "Follow Prompt constraints: Technology years."
)
CV_TECH_ITEMS = (
    "Technologies explicitly named on the resume only (max 30). "
    "Include a name only if that exact tool/language/framework appears in the CV text — "
    "not inferred from job titles, not copied from the job description, not guessed from "
    "'similar' work. Empty list is OK if the CV has no explicit skills section."
)
MATCH_SCORE_DESC = (
    "0-100 overall fit vs JD must/nice tech and experience; do not use 0 when there is clear overlap."
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

PROMPT_CONSTRAINTS = """
### Evidence and hallucination

- **Profile `technologies`**: resume/CV text only. Never copy technologies from the job description.
- **Match lists**: compare JD requirements to what is on the CV/profile; JD tech absent from CV → `not_mentioned_skills`.
- Do not invent employers, projects, tools, or durations not supported by text.
- If evidence is weak, lower section `confidence` and add object-level `ambiguities[]`.

### Technology years (CV extract + match)

- Count years per tech within dated project windows when described; prefer over company tenure.
- Outsource/outstaff/consulting: never equate agency employment length with tech years.
- Skills list without dates: do not assign multi-year tenure; use `null` or low confidence.
- Overlapping roles: do not double-count calendar time per tech.

### Total IT years

- Sum dated IT role intervals; exclude clearly non-IT jobs unless JD asks otherwise.
- Do not use full company tenure at outsource shops without project detail.

### Leadership and education

- `tech_lead` / `team_lead` require behavioral or title evidence.
- Education fields: **OR only**; if JD implies AND, note in `ambiguities`.

### Candidate profile (CV extract)

- `technologies.items`: only **literal** names from the resume — SKILLS / TECHNOLOGIES section, skills bullets, or employment bullets that **name** the tool (e.g. "Python", "FastAPI"). Do **not** add a stack because a role sounds like backend/AI work.
- Do **not** add JD must-haves (e.g. LangGraph, CrewAI, Kubernetes) unless that exact name appears on the CV.
- Prefer fewer, accurate items over a long inferred list.
- Per-tech `years`: only from dated roles where that name appears; undated SKILLS list → `years: null`.
- `experience.total_years` = sum of dated IT/software employment intervals (not from JD).

### Technology priority (JD extract)

- **must**: required, primary language, "comfortable with X", "deep hands-on", core stack in
  "What We're Looking For" / qualifications — unless the same phrase says plus/preferred/optional.
- **nice**: "a plus", "preferred", "nice-to-have", "familiarity with", bonus skills; tools named
  only in a company "Technology Context" / platform list without their own requirement sentence.
- Do **not** label every technology as `nice`; split must vs nice from the JD wording per item.
- If priority is unclear for a named tech, add object-level `ambiguities` (do not guess).

### Match scoring

- `years_match` = `clear` only when JD and CV evidence align with the same scope.
- `not_mentioned_skills`: absence from CV is not proof the candidate lacks the skill.
- When in doubt: lower confidence, add ambiguities, prefer raw JD/CV in match.
"""
