from fastapi import APIRouter, File, HTTPException, UploadFile

from app.api.schemas import HealthResponse, ScreenResponse
from app.config import settings
from app.services import document_parser, screening_pipeline
from app.services.ollama_client import check_health
from app.services.screening_pipeline import ResumeInput

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    reachable, ready = await check_health()
    status = "ok" if reachable and (ready or settings.mock_llm) else "degraded"
    return HealthResponse(
        status=status,
        ollama_reachable=reachable or settings.mock_llm,
        model_ready=ready or settings.mock_llm,
    )


@router.post("/api/screen", response_model=ScreenResponse)
async def screen(
    job_description: UploadFile = File(...),
    resumes: list[UploadFile] = File(...),
) -> ScreenResponse:
    if not resumes:
        raise HTTPException(400, "At least one resume is required.")
    if len(resumes) > settings.max_resumes:
        raise HTTPException(400, f"Maximum {settings.max_resumes} resumes allowed.")

    try:
        jd_bytes = await job_description.read()
        jd_text = document_parser.extract_text(jd_bytes, job_description.filename or "jd.pdf")
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    if not jd_text.strip():
        raise HTTPException(400, "Job description is empty or unreadable.")

    resume_inputs: list[ResumeInput] = []
    for upload in resumes:
        try:
            content = await upload.read()
            text = document_parser.extract_text(content, upload.filename or "resume.pdf")
            if not text.strip():
                raise HTTPException(400, f"Resume {upload.filename} is empty or unreadable.")
            resume_inputs.append(
                ResumeInput(filename=upload.filename or "resume.pdf", text=text)
            )
        except ValueError as e:
            raise HTTPException(400, str(e)) from e

    try:
        return await screening_pipeline.run_screening(jd_text, resume_inputs)
    except Exception as e:
        raise HTTPException(502, f"Screening failed: {e}") from e
