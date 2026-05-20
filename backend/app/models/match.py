from typing import Literal

from pydantic import BaseModel, Field

from app.schemas import field_descriptions as fd

YearsMatch = Literal["clear", "not_enough", "ambiguous", "n/a"]


class MatchingSkill(BaseModel):
    name: str = Field(description=fd.MATCH_SKILL_NAME)
    years_match: YearsMatch = Field(description=fd.YEARS_MATCH)
    description: str = Field(description=fd.MATCH_SKILL_DESC)


class NotMentionedSkill(BaseModel):
    name: str = Field(description=fd.NOT_MENTIONED_NAME)
    description: str = Field(description=fd.NOT_MENTIONED_DESC)


class MatchResult(BaseModel):
    candidate_name: str
    match_score: int = Field(ge=0, le=100, description=fd.MATCH_SCORE_DESC)
    matching_skills: list[MatchingSkill] = Field(default_factory=list)
    not_mentioned_skills: list[NotMentionedSkill] = Field(default_factory=list)
    reasoning: str = Field(description=fd.REASONING)
    ambiguities: list[str] = Field(default_factory=list, description=fd.AMBIGUITIES)
