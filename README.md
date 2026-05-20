# AI Resume Screening System

[![CI](https://github.com/viktornord/ai-resume-screening/actions/workflows/ci.yml/badge.svg)](https://github.com/viktornord/ai-resume-screening/actions/workflows/ci.yml)

Recruiters upload a job description and resumes; the backend extracts requirements once (F-first), profiles each CV, matches with an LLM, and returns ranked candidates with explainability.

## Stack

| Layer | Tech |
|-------|------|
| Backend | Python 3.11+, FastAPI, [uv](https://docs.astral.sh/uv/) |
| Frontend | React 18, TypeScript, Vite, Tailwind, shadcn-style UI |
| LLM | [Mistral API](https://docs.mistral.ai/) (`mistral-small-latest` by default) |

## Quick start (Docker)

```bash
cp .env.example .env
# Set MISTRAL_API_KEY in .env (https://console.mistral.ai/)
docker compose up --build
```

- **Frontend:** http://localhost:3000  
- **API:** http://localhost:8000  
- **Health:** http://localhost:8000/health  

Mock mode (no API key, instant):

```bash
MOCK_LLM=true docker compose up --build
```

## Local development

### Backend (uv)

```bash
cd backend
uv sync --all-groups

# Offline
MOCK_LLM=true uv run uvicorn app.main:app --reload --port 8000

# Mistral (from repo root .env)
cd backend && uv run uvicorn app.main:app --reload --port 8000
```

Set `MISTRAL_API_KEY` in `.env` at the repo root (see `.env.example`).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` and `/health` to `http://localhost:8000`.

### Debugger (Cursor / VS Code)

1. `cd backend && uv sync --all-groups`
2. **Run and Debug** → **Backend: FastAPI (mock LLM)** or **Backend: FastAPI (Mistral)** (uses `MISTRAL_API_KEY` from your environment)

Configs: [`.vscode/launch.json`](.vscode/launch.json).

## Environment

| Variable | Description |
|----------|-------------|
| `MISTRAL_API_KEY` | Required for real screening ([Mistral console](https://console.mistral.ai/)) |
| `MISTRAL_MODEL` | Default `mistral-small-latest` |
| `MOCK_LLM` | `true` = deterministic mock responses (tests/CI) |
| `MAX_CONCURRENT_LLM` | Parallel resume LLM calls (default `4`) |

## Project layout

See [AGENTS.md](AGENTS.md) and [project_plan.md](project_plan.md).
