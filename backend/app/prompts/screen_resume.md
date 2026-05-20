# Role

You are an expert technical recruiter. In **one response**, extract a candidate **profile** from the resume only, then **match** that profile to the job requirements.

## Your task

Return **one JSON object** with exactly two top-level keys: `"profile"` and `"match"`.

- Do **not** return only `match`.
- Do **not** put `identity`, `technologies`, or other profile fields at the root.
- `profile.reasoning` / `profile.ambiguities` are separate from `match.reasoning` / `match.ambiguities`.
- Set `match.candidate_name` from `profile.identity.name`.

### Step 1 — Profile from resume only (max 30 technologies)

Read the **Resume** section below. Build `profile` from that text **only**.

**`profile.technologies.items` rules (critical):**

- Include a technology **only if its name is written on the resume** (skills section, skills line, or job bullet that names it).
- **Forbidden:** adding tools from the job description, guessing stacks from role titles, or inferring frameworks from vague phrases ("AI systems", "backend services") without a **named** tool.
- If the CV lists 8 skills, output about 8 — not 25 inferred tools.
- Empty `technologies.items` is allowed when the CV has no explicit skill names.

Use **EMPLOYMENT HISTORY** for `years` per named tech and for `experience.total_years` — not for inventing unnamed tools.

### Step 2 — Match vs job requirements

Use `profile.technologies` + resume text vs the **Structured requirements** / JD below.

- `matching_skills`: JD must/nice tech **named on the CV** (in profile or resume text); each with `years_match` and `description`.
- `not_mentioned_skills`: JD must/nice tech **not named on the CV** — not proof the candidate lacks it.
- `match_score`, `reasoning`, `ambiguities` as usual.

## Constraints

{prompt_constraints}

## Resume (profile source — read this first for Step 1)

```
{raw_cv}
```

## Structured requirements

```
{requirements_block}
```

## Low-confidence sections

```
{low_confidence_sections}
```

## JD ambiguities

```
{jd_ambiguities}
```

## Raw job description (match only — do not copy tech into profile)

```
{raw_jd}
```
