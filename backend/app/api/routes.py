import logging
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.api.schemas import HealthResponse, ScreenResponse
from app.config import settings
from app.services import document_parser, screening_pipeline
from app.services.llm_client import LLMError, check_health, ensure_model_ready
from app.services.screening_pipeline import ResumeInput
from app.structured_logging import bind_request, clear_request, log_event, log_timing

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    reachable, ready = await check_health()
    status = "ok" if reachable and (ready or settings.mock_llm) else "degraded"
    return HealthResponse(
        status=status,
        llm_reachable=reachable or settings.mock_llm,
        model_ready=ready or settings.mock_llm,
    )


@router.post("/api/screen", response_model=ScreenResponse)
async def screen(
    job_description: UploadFile = File(...),
    resumes: list[UploadFile] = File(...),
) -> ScreenResponse:
    screening_id = uuid.uuid4().hex[:12]
    bind_request(screening_id=screening_id)

    try:
        if not resumes:
            raise HTTPException(400, "At least one resume is required.")
        if len(resumes) > settings.max_resumes:
            raise HTTPException(400, f"Maximum {settings.max_resumes} resumes allowed.")

        log_event(
            logger,
            "api.screen.request",
            jd_filename=job_description.filename,
            resume_count=len(resumes),
            resume_filenames=[u.filename for u in resumes],
        )

        with log_timing(logger, "parse_documents", resume_count=len(resumes)):
            try:
                jd_bytes = await job_description.read()
                jd_text = document_parser.extract_text(
                    jd_bytes, job_description.filename or "jd.pdf"
                )
            except ValueError as e:
                raise HTTPException(400, str(e)) from e

            if not jd_text.strip():
                raise HTTPException(400, "Job description is empty or unreadable.")

            resume_inputs: list[ResumeInput] = []
            for upload in resumes:
                try:
                    content = await upload.read()
                    text = document_parser.extract_text(
                        content, upload.filename or "resume.pdf"
                    )
                    if not text.strip():
                        raise HTTPException(
                            400, f"Resume {upload.filename} is empty or unreadable."
                        )
                    resume_inputs.append(
                        ResumeInput(filename=upload.filename or "resume.pdf", text=text)
                    )
                except ValueError as e:
                    raise HTTPException(400, str(e)) from e

        log_event(
            logger,
            "parse_documents.result",
            jd_chars=len(jd_text),
            resume_chars={r.filename: len(r.text) for r in resume_inputs},
        )

        if not settings.mock_llm:
            try:
                await ensure_model_ready()
            except LLMError as e:
                raise HTTPException(503, str(e)) from e

        response = await screening_pipeline.run_screening(jd_text, resume_inputs)
        log_event(
            logger,
            "api.screen.response",
            processing_ms=response.processing_ms,
            candidate_count=len(response.candidates),
            job_title=response.job_title_hint,
        )
        return response
    except LLMError as e:
        log_event(logger, "api.screen.error", level=logging.ERROR, error=str(e))
        raise HTTPException(503, str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        log_event(
            logger,
            "api.screen.error",
            level=logging.ERROR,
            error_type=type(e).__name__,
            error=str(e),
        )
        raise HTTPException(502, f"Screening failed: {e}") from e
    finally:
        clear_request()
