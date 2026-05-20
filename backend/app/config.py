from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral"
    match_threshold_good_fit: int = 70
    confidence_threshold: float = 0.6
    max_resume_chars: int = 8000
    max_jd_chars: int = 16000
    max_concurrent_llm: int = 3
    mock_llm: bool = False
    max_file_size_mb: int = 5
    max_resumes: int = 20


settings = Settings()
