import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from app.api.schemas import ScreenResponse
from app.config import settings
from app.services import jd_extract, llm_screening, ranking
from app.services.ranking import trim_list, trim_text
from app.structured_logging import log_event, log_timing, match_summary

logger = logging.getLogger(__name__)


@dataclass
class ResumeInput:
    filename: str
    text: str


async def _run_limited(
    semaphore: asyncio.Semaphore,
    coro,
    *,
    resume: str,
):
    log_event(logger, "screen_resume.queued", resume=resume)
    async with semaphore:
        return await coro


async def run_screening(
    jd_text: str,
    resumes: list[ResumeInput],
) -> ScreenResponse:
    """
    F-first pipeline (1 + N LLM calls):
      1. JD → Requirements (once)
      2. Per resume: CV → CandidateProfile + match (one call each, parallel)
    """
    started = time.perf_counter()
    resume_names = [r.filename for r in resumes]
    with log_timing(
        logger,
        "screening",
        resume_count=len(resumes),
        resumes=resume_names,
        jd_chars=len(jd_text),
        max_concurrent_llm=settings.max_concurrent_llm,
        mock_llm=settings.mock_llm,
    ):
        semaphore = asyncio.Semaphore(settings.max_concurrent_llm)

        requirements = await jd_extract.extract_requirements(jd_text)

        screen_tasks = [
            _run_limited(
                semaphore,
                llm_screening.screen_resume(requirements, jd_text, r.text, r.filename),
                resume=r.filename,
            )
            for r in resumes
        ]
        results = await asyncio.gather(*screen_tasks)

        candidates = [
            ranking.build_candidate_response(result.match, resume.filename)
            for result, resume in zip(results, resumes, strict=True)
        ]
        ranked = ranking.sort_candidates(candidates)

    log_event(
        logger,
        "screening.ranked",
        job_title=requirements.role.title,
        candidates=[
            {
                "resume": resume.filename,
                **match_summary(result.match),
            }
            for result, resume in zip(results, resumes, strict=True)
        ],
    )

    return ScreenResponse(
        job_title_hint=requirements.role.title,
        requirements_reasoning=trim_text(requirements.reasoning),
        requirements_ambiguities=trim_list(requirements.ambiguities),
        candidates=ranked,
        screened_at=datetime.now(timezone.utc),
        processing_ms=int((time.perf_counter() - started) * 1000),
    )
