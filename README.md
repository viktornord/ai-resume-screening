# AI Resume Screening System

[![CI](https://github.com/viktornord/ai-resume-screening/actions/workflows/ci.yml/badge.svg)](https://github.com/viktornord/ai-resume-screening/actions/workflows/ci.yml)

Recruiters upload a job description and resumes; the backend extracts requirements once (F-first), profiles each CV, matches with an LLM, and returns ranked candidates with explainability.

## Stack

| Layer | Tech |
|-------|------|
| Backend | Python 3.11+, FastAPI, [uv](https://docs.astral.sh/uv/) |
| Frontend | React 18, TypeScript, Vite, Tailwind, shadcn-style UI |
| LLM | Ollama + `mistral` |

## Quick start (Docker)

```bash
# Pull the model (first time only)
docker compose up -d ollama
docker compose exec ollama ollama pull mistral

# Run everything (use MOCK_LLM=true to skip Ollama)
docker compose up --build
```

- **Frontend:** http://localhost:3000  
- **API:** http://localhost:8000  
- **Health:** http://localhost:8000/health  

Mock mode (no GPU / no model):

```bash
MOCK_LLM=true docker compose up --build
```

## Local development

### Backend (uv)

```bash
cd backend
uv sync --all-groups
MOCK_LLM=true uv run uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` and `/health` to `http://localhost:8000`.

## Project layout

```
backend/app/     # FastAPI, models, prompts, pipeline
frontend/src/    # React UI (upload, ranked table, reasoning)
```

See [AGENTS.md](AGENTS.md) and [project_plan.md](project_plan.md) for API and pipeline details.
