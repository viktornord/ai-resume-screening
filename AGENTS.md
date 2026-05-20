# AI Resume Screening System — Agent Guide

Implementation plan: [project_plan.md](project_plan.md).

## Project summary

Recruiters upload a JD and multiple resumes. Backend:

1. **LLM once:** JD → `Requirements` (sections + `confidence`; **`reasoning` / `ambiguities` once on the object**).
2. **Per resume:** CV → `CandidateProfile` (same); **match** → score + skills + object-level **`reasoning` / `ambiguities`**.
3. Match uses structured data + raw JD/CV; low section `confidence` → prefer raw text for that section.

| Decision | Choice |
|----------|--------|
| Backend | Python 3.11+, FastAPI |
| Python tooling | **[uv](https://docs.astral.sh/uv/) only** — `pyproject.toml` + `uv.lock`; no `pip install`, `poetry`, or `requirements.txt` |
| Frontend | React 18, TypeScript, Vite, Tailwind + shadcn/ui |
| LLM | Ollama + `mistral` |
| Pipeline | F-first: 1× JD extract + per CV (profile + match) |
| Education match | **OR only** — any one `fields[]` entry; no AND in v1 |
| Explainability | One `reasoning` + one `ambiguities[]` **per LLM object** (not per section) |
| Auth / DB | None |

## Workflow

1. Upload JD + resumes  
2. Extract text (PDF/DOCX)  
3. JD → `Requirements`  
4. Per resume: CV → `CandidateProfile` → match → candidate row  
5. Rank, Good/Bad threshold  

## LLM outputs (three objects)

| Step | Output type | `reasoning` + `ambiguities` | Sections |
|------|-------------|------------------------------|----------|
| JD extract | `Requirements` | once at object root | `confidence` only |
| CV extract | `CandidateProfile` | once at object root | `confidence` only |
| Match | → API candidate | once at object root | n/a |

## Internal models (summary)

Full JSON: [project_plan.md](project_plan.md).

### Sections (`Requirements` / `CandidateProfile`)

`role`, `technologies`, `soft_skills`, `leadership`, `education`, `experience` (+ `identity` on CV) — data + **`confidence`**. `experience.min_total_years` / `total_years` = **IT-relevant years only** (not all career jobs).

JD `education.fields[]`: **OR only in v1** (any one field may match). No AND / `fields_operator` in v1 — see highlighted note in [project_plan.md](project_plan.md).

### Object root (each extract + match)

- `reasoning` (string)  
- `ambiguities` (string[])  

### Low confidence

Section `confidence < 0.6` → match prompt prefers raw JD/CV for that section. Uncertainty text goes in the **object-level** `ambiguities`, not on sections.

## API (public)

### `POST /api/screen`

```json
{
  "job_title_hint": "Senior Python Engineer",
  "requirements_reasoning": "Senior backend role: Python/FastAPI required...",
  "requirements_ambiguities": ["No explicit people-management requirement"],
  "candidates": [
    {
      "candidate_name": "Anu",
      "match_score": 85,
      "matching_skills": [
        { "name": "Python", "years_match": "clear", "description": "6 years on CV meets 5+ required" },
        { "name": "FastAPI", "years_match": "clear", "description": "Listed in current role" }
      ],
      "not_mentioned_skills": [
        { "name": "Docker", "description": "Nice-to-have; not on CV — gap or omission" }
      ],
      "recommendation": "Good fit",
      "source_filename": "anu_resume.pdf",
      "reasoning": "Strong must-have tech match; Docker only nice-to-have gap.",
      "ambiguities": ["JD leadership scope unclear vs tech-lead title only"]
    }
  ],
  "screened_at": "2026-05-20T12:00:00Z",
  "processing_ms": 12340
}
```

`requirements_*` from `Requirements` root. `candidates[].reasoning` / `ambiguities` from **match** root only (not from `CandidateProfile`).

**Match fields (per candidate):** `matching_skills[]`, `not_mentioned_skills[]`; no top-level `experience` on API. Extract: `min_total_years` / `total_years` (IT scope). Prompts must include **field descriptions** (see project_plan). Map spec `missing_skill` → `not_mentioned_skills`.

### `GET /health`

`status`, `ollama_reachable`, `model_ready`.

## Repository layout

```
backend/
  pyproject.toml              # project + [dependency-groups] dev
  uv.lock                     # commit on dep changes
  Dockerfile                  # ghcr.io/astral-sh/uv image; uv sync --frozen
  app/
    models/requirements.py    # Field(description=...) per field-descriptions table
    schemas/field_descriptions.py
    services/jd_extract.py, resume_extract.py, llm_screening.py, ranking.py
    prompts/jd_extract.txt, resume_extract.txt, screening.txt  # FIELD REFERENCE
```

## Python toolchain (uv — required)

All backend work uses **uv** from `backend/`. Do not use bare `python`/`pip` for installs or runs.

| Task | Command |
|------|---------|
| Install deps | `cd backend && uv sync --all-groups` |
| Run API (mock) | `MOCK_LLM=true uv run uvicorn app.main:app --reload --port 8000` |
| Run API (Ollama) | `OLLAMA_BASE_URL=http://localhost:11434 OLLAMA_MODEL=mistral uv run uvicorn app.main:app --reload --port 8000` |
| Tests | `MOCK_LLM=true uv run pytest` |
| Add dependency | `uv add <package>` (updates `pyproject.toml` + `uv.lock`) |
| Add dev dependency | `uv add --group dev <package>` |

**Docker:** `backend/Dockerfile` uses `ghcr.io/astral-sh/uv:python3.11-bookworm-slim`, `uv sync --frozen --no-dev`, and `uv run uvicorn …`. Keep compose aligned with that image — do not switch to `pip install -r`.

**Lockfile:** Commit `uv.lock` whenever dependencies change. CI and Docker rely on `--frozen`.

## Environment

```
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=mistral
MATCH_THRESHOLD_GOOD_FIT=70
CONFIDENCE_THRESHOLD=0.6
MAX_RESUME_CHARS=8000
MAX_CONCURRENT_LLM=3
MOCK_LLM=false
```

## Backend notes

- Pydantic: `Field(description=...)` on every LLM-facing field; forbid `reasoning` / `ambiguities` on sections.
- Prompts: **FIELD REFERENCE** + **Prompt constraints** (tech years from projects not outstaff tenure; see project_plan).
- Retry once on invalid JSON; cap reasoning length if needed.
- `MOCK_LLM=true` for tests.

## Frontend

Expandable **reasoning** / **ambiguities** per candidate; skill rows show `years_match` + `description`; `not_mentioned_skills` labeled as “not on resume”; optional JD `requirements_ambiguities` banner.

## Agent conventions

- **Backend Python:** use `uv sync`, `uv run`, `uv add` only; never `pip install`, `poetry`, or hand-edited `requirements.txt`
- After adding deps, commit both `pyproject.toml` and `uv.lock`
- `Requirements` / `CandidateProfile` — not `JobRequirements`
- API: `matching_skills` (objects), `not_mentioned_skills`; extract has `experience` with IT-years semantics; no `experience` on match API row
- `reasoning` + `ambiguities` **once per object**, not per section
- Education: OR only; no `fields_operator` / AND in v1
- KISS: no judge LLM, no formula matcher, no DB unless asked

## Deliverables checklist

- [ ] `docker compose up` runs all services
- [ ] JD + resumes → ranked JSON with reasoning/ambiguities
- [ ] React shows match explanation per candidate
- [ ] No auth, no DB
- [ ] README with model pull
