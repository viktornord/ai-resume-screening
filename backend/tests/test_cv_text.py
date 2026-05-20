from app.services.cv_text import clean_cv_text


def test_clean_cv_text_strips_nbsp_and_bullets():
    raw = "SKILLS\nLLMs\n\u00a0\u00a0Python\nPROFILE\n\u00b7 Design RAG"
    cleaned = clean_cv_text(raw)
    assert "\xa0" not in cleaned
    assert "LLMs" in cleaned
    assert "Python" in cleaned
