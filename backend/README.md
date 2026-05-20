# Resume Screening API

Python 3.11+ backend managed with [uv](https://docs.astral.sh/uv/).

## Setup

```bash
cd backend
uv sync --all-groups
```

## Run

```bash
# Mock LLM (no Ollama required)
MOCK_LLM=true uv run uvicorn app.main:app --reload --port 8000

# With Ollama
OLLAMA_BASE_URL=http://localhost:11434 OLLAMA_MODEL=mistral uv run uvicorn app.main:app --reload --port 8000
```

## Test

```bash
MOCK_LLM=true uv run pytest
```

## Environment

| Variable | Default |
|----------|---------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` |
| `OLLAMA_MODEL` | `mistral` |
| `MOCK_LLM` | `false` |
| `MATCH_THRESHOLD_GOOD_FIT` | `70` |
| `CONFIDENCE_THRESHOLD` | `0.6` |
| `MAX_RESUME_CHARS` | `8000` |
| `MAX_CONCURRENT_LLM` | `3` |
