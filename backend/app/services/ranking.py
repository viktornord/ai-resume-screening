from app.api.schemas import CandidateResponse
from app.config import settings
from app.models.match import MatchResult


def recommendation_for_score(score: int) -> str:
    return "Good fit" if score >= settings.match_threshold_good_fit else "Bad fit"


def clamp_score(score: int) -> int:
    return max(0, min(100, score))


def trim_text(text: str, max_len: int = 2000) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def trim_list(items: list[str], max_items: int = 20) -> list[str]:
    return items[:max_items]


def build_candidate_response(
    match: MatchResult,
    source_filename: str,
) -> CandidateResponse:
    score = clamp_score(match.match_score)
    return CandidateResponse(
        candidate_name=match.candidate_name,
        match_score=score,
        matching_skills=match.matching_skills,
        not_mentioned_skills=match.not_mentioned_skills,
        recommendation=recommendation_for_score(score),
        source_filename=source_filename,
        reasoning=trim_text(match.reasoning),
        ambiguities=trim_list(match.ambiguities),
    )


def sort_candidates(candidates: list[CandidateResponse]) -> list[CandidateResponse]:
    return sorted(candidates, key=lambda c: c.match_score, reverse=True)
