# Resume Screening API

FastAPI backend: JD → structured requirements → per-resume profile + match (Mistral API).

## Setup

```bash
uv sync --all-groups
```

Copy repo root `.env.example` to `.env` and set `MISTRAL_API_KEY`.

## Run

```bash
# Mock (no API key)
MOCK_LLM=true uv run uvicorn app.main:app --reload --port 8000

# Mistral
uv run uvicorn app.main:app --reload --port 8000
```

## Tests

```bash
MOCK_LLM=true uv run pytest
```

## Environment

| Variable | Default |
|----------|---------|
| `MISTRAL_API_KEY` | (required unless `MOCK_LLM=true`) |
| `MISTRAL_MODEL` | `mistral-small-latest` |
| `MOCK_LLM` | `false` |
| `MAX_CONCURRENT_LLM` | `4` |
| `LLM_TIMEOUT_SECONDS` | `900` |
| `LLM_MAX_TOKENS` | `8192` |
| `MATCH_THRESHOLD_GOOD_FIT` | `70` |
| `CONFIDENCE_THRESHOLD` | `0.6` |
