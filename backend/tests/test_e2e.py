import io

import pytest
from docx import Document


def _docx_bytes(text: str) -> bytes:
    doc = Document()
    doc.add_paragraph(text)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ok", "degraded")
    assert data["ollama_reachable"] is True


@pytest.mark.asyncio
async def test_screen_mock_two_resumes(client):
    jd = _docx_bytes("Senior Python Engineer with 5+ years Python and FastAPI.")
    files = [
        (
            "job_description",
            ("jd.docx", io.BytesIO(jd), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ),
        (
            "resumes",
            ("anu.docx", io.BytesIO(_docx_bytes("Anu Kumar Python FastAPI")), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ),
        (
            "resumes",
            ("alice.docx", io.BytesIO(_docx_bytes("Alice Smith Python only")), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ),
    ]
    resp = await client.post("/api/screen", files=files)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "requirements_reasoning" in data
    assert "requirements_ambiguities" in data
    assert len(data["candidates"]) == 2
    assert data["candidates"][0]["match_score"] >= data["candidates"][1]["match_score"]
    c0 = data["candidates"][0]
    assert "matching_skills" in c0
    assert c0["matching_skills"][0]["years_match"] in (
        "clear",
        "not_enough",
        "ambiguous",
        "n/a",
    )
    assert "not_mentioned_skills" in c0
    assert "reasoning" in c0
    assert "ambiguities" in c0
    assert c0["recommendation"] in ("Good fit", "Bad fit")
