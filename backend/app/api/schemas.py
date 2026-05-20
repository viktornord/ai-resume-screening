from datetime import datetime

from pydantic import BaseModel, Field

from app.models.match import MatchingSkill, NotMentionedSkill


class CandidateResponse(BaseModel):
    candidate_name: str
    match_score: int
    matching_skills: list[MatchingSkill]
    not_mentioned_skills: list[NotMentionedSkill]
    recommendation: str
    source_filename: str
    reasoning: str
    ambiguities: list[str]


class ScreenResponse(BaseModel):
    job_title_hint: str | None = None
    requirements_reasoning: str
    requirements_ambiguities: list[str]
    candidates: list[CandidateResponse]
    screened_at: datetime
    processing_ms: int


class HealthResponse(BaseModel):
    status: str
    ollama_reachable: bool
    model_ready: bool
