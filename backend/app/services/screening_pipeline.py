import asyncio
import time
from dataclasses import dataclass

from app.api.schemas import CandidateResponse, ScreenResponse
from app.config import settings
from app.models.requirements import Requirements
from app.services import jd_extract, llm_screening, ranking, resume_extract
from app.services.ranking import trim_list, trim_text


@dataclass
class ResumeInput:
    filename: str
    text: str


async def _process_one_resume(
    requirements: Requirements,
    raw_jd: str,
    resume: ResumeInput,
    semaphore: asyncio.Semaphore,
) -> CandidateResponse:
    async with semaphore:
        profile = await resume_extract.extract_profile(resume.text, resume.filename)
        match = await llm_screening.match_candidate(
            requirements, profile, raw_jd, resume.text
        )
        return ranking.build_candidate_response(match, resume.filename)


async def run_screening(
    jd_text: str,
    resumes: list[ResumeInput],
) -> ScreenResponse:
    start = time.perf_counter()
    requirements = await jd_extract.extract_requirements(jd_text)

    semaphore = asyncio.Semaphore(settings.max_concurrent_llm)
    tasks = [
        _process_one_resume(requirements, jd_text, r, semaphore) for r in resumes
    ]
    candidates = await asyncio.gather(*tasks)
    ranked = ranking.sort_candidates(list(candidates))

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    from datetime import datetime, timezone

    return ScreenResponse(
        job_title_hint=requirements.role.title,
        requirements_reasoning=trim_text(requirements.reasoning),
        requirements_ambiguities=trim_list(requirements.ambiguities),
        candidates=ranked,
        screened_at=datetime.now(timezone.utc),
        processing_ms=elapsed_ms,
    )
