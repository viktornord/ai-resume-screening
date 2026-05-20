import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_REPO_ROOT = _BACKEND_DIR.parent


def _env_files() -> tuple[str, ...]:
    """Repo root .env first (docker/compose), then backend/.env if present."""
    paths: list[Path] = [_REPO_ROOT / ".env", _BACKEND_DIR / ".env"]
    found = tuple(str(p) for p in paths if p.is_file())
    return found if found else (".env",)


def _bootstrap_dotenv() -> None:
    """Load .env into os.environ so debugger/Docker/uvicorn all see MISTRAL_API_KEY."""
    for env_path in _env_files():
        path = Path(env_path)
        if not path.is_file():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            key, sep, value = line.partition("=")
            if not sep:
                continue
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_bootstrap_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mistral_api_key: str = ""
    mistral_model: str = "mistral-small-latest"
    mistral_base_url: str = "https://api.mistral.ai/v1"
    match_threshold_good_fit: int = 70
    confidence_threshold: float = 0.6
    max_resume_chars: int = 8000
    max_jd_chars: int = 16000
    max_concurrent_llm: int = 4
    llm_timeout_seconds: float = 900.0
    llm_max_tokens: int = 8192
    log_level: str = "INFO"
    # json | pretty | auto (auto = pretty when LOG_LEVEL=DEBUG, else json)
    log_format: str = "auto"
    mock_llm: bool = False
    max_file_size_mb: int = 5
    max_resumes: int = 20


settings = Settings()
