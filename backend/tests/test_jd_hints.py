from pathlib import Path

from app.models.requirements import Requirements
from app.services.jd_hints import extract_job_title, infer_jd_hints, infer_leadership
from app.services.llm_normalize import normalize_requirements

SIMULMEDIA_SNIPPET = """
Simulmedia - Lead AI
Engineer — Agentic Products
& Platform
About the Role Simulmedia is building
AI into how TV advertising is planned,
activated, and measured.
This is a lead individual contributor role with
broad technical influence. You are not
managing a team.
"""


def test_extract_simulmedia_title():
    title = extract_job_title(SIMULMEDIA_SNIPPET)
    assert title is not None
    assert "Lead" in title
    assert "Engineer" in title


def test_infer_leadership_lead_ic_not_people_manager():
    title = "Lead AI Engineer — Agentic Products & Platform"
    flags = infer_leadership(title, SIMULMEDIA_SNIPPET)
    assert flags["tech_lead"] is True
    assert flags["team_lead"] is False


def test_normalize_requirements_uses_jd_hints_not_unknown():
    raw = {
        "reasoning": "x",
        "ambiguities": [],
        "role": {"confidence": 0.75},
        "technologies": {"items": [], "confidence": 0.8},
        "soft_skills": {"items": [], "confidence": 0.7},
        "leadership": {"confidence": 0.75},
        "education": {"confidence": 0.7},
        "experience": {"confidence": 0.7},
    }
    req = Requirements.model_validate(
        normalize_requirements(raw, jd_text=SIMULMEDIA_SNIPPET)
    )
    assert "Lead" in req.role.title
    assert req.role.seniority == "lead"
    assert req.leadership.tech_lead is True
    assert req.leadership.team_lead is False
    assert req.technologies.items == []
    assert req.soft_skills.items == []


def test_simulmedia_pdf_file_if_present():
    pdf = Path("/Users/vurbanas/Downloads/Simulmedia - Lead AI Engineer — Agentic Products & Platform.pdf")
    if not pdf.exists():
        return
    from app.services.document_parser import extract_text

    text = extract_text(pdf.read_bytes(), pdf.name)
    title = extract_job_title(text)
    assert title and "Engineer" in title
    hints = infer_jd_hints(text)
    assert hints["tech_lead"] is True
    assert hints["team_lead"] is False
