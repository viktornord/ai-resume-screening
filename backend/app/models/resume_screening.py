from pydantic import BaseModel, Field

from app.models.candidate_profile import CandidateProfile
from app.models.match import MatchResult

PROFILE_DESC = (
    "Structured candidate profile extracted from the resume "
    "(sections + section confidence; profile-level reasoning and ambiguities)."
)
MATCH_DESC = (
    "Match score and skill breakdown vs the job requirements "
    "(match-level reasoning and ambiguities only)."
)


class ResumeScreeningResult(BaseModel):
    profile: CandidateProfile = Field(description=PROFILE_DESC)
    match: MatchResult = Field(description=MATCH_DESC)
