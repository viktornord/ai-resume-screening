from app.models.candidate_profile import CandidateProfile
from app.models.requirements import Requirements
from app.services.llm_normalize import (
    normalize_candidate_profile,
    normalize_requirements,
    normalize_resume_screening,
)


def test_normalize_requirements_llama_flat_sections():
    raw = {
        "reasoning": "Lead AI role.",
        "ambiguities": [],
        "role": {"title": "Lead AI Engineer", "seniority": "senior"},
        "technologies": [
            {"name": "LLMs", "min_years": 3, "priority": "must", "confidence": 1},
            {"name": "Python", "min_years": None, "priority": "nice", "confidence": 0.9},
        ],
        "soft_skills": ["Communication", "Collaboration", "Problem-solving"],
        "leadership": {"tech_lead": True, "team_lead": False},
        "education": {"min_level": "bachelor", "fields": ["CS"], "required": True},
        "experience": {"min_total_years": 5},
    }
    req = Requirements.model_validate(normalize_requirements(raw))
    assert req.role.confidence == 0.75
    assert req.technologies.items[0].name == "LLMs"
    assert req.technologies.confidence > 0
    assert req.soft_skills.items == ["Communication", "Collaboration", "Problem-solving"]
    assert req.leadership.confidence == 0.75


def test_normalize_jd_tech_priority_aliases():
    raw = {
        "reasoning": "x",
        "ambiguities": [],
        "role": {"title": "Engineer", "seniority": "senior", "confidence": 0.9},
        "technologies": {
            "items": [
                {"name": "Python", "priority": "required"},
                {"name": "Go", "priority": "plus"},
            ],
            "confidence": 0.85,
        },
        "soft_skills": {"items": [], "confidence": 0.7},
        "leadership": {"tech_lead": False, "team_lead": False, "confidence": 0.8},
        "education": {"confidence": 0.7},
        "experience": {"confidence": 0.7},
    }
    req = Requirements.model_validate(normalize_requirements(raw))
    assert req.technologies.items[0].priority == "must"
    assert req.technologies.items[1].priority == "nice"  # "plus" -> nice


def test_normalize_requirements_confidence_only_no_validation_error():
    raw = {
        "reasoning": "Partial tool output.",
        "ambiguities": [],
        "role": {"confidence": 0.75},
        "technologies": {"items": [], "confidence": 0.8},
        "soft_skills": {"items": [], "confidence": 0.7},
        "leadership": {"confidence": 0.75},
        "education": {"confidence": 0.7},
        "experience": {"confidence": 0.7},
    }
    req = Requirements.model_validate(normalize_requirements(raw))
    assert req.role.title == ""
    assert req.role.seniority == "unknown"
    assert req.leadership.tech_lead is False
    assert req.leadership.team_lead is False


def test_normalize_cv_tech_string_and_years_in_parens():
    raw = {
        "reasoning": "CV ok.",
        "ambiguities": [],
        "identity": {"name": "Viktor Urbanas"},
        "technologies": [
            "Python (6 years)",
            {"name": "LangGraph", "years": 2},
            "FastAPI",
        ],
        "soft_skills": {"items": [], "confidence": 0.5},
        "leadership": {"tech_lead": True, "team_lead": True, "confidence": 0.8},
        "education": {"items": [{"level": "master", "field": "Engineering"}]},
        "experience": {"total_years": 10},
    }
    profile = CandidateProfile.model_validate(normalize_candidate_profile(raw))
    assert profile.technologies.items[0].name == "Python"
    assert profile.technologies.items[0].years == 6.0
    assert profile.technologies.items[1].name == "LangGraph"
    assert profile.technologies.items[2].name == "FastAPI"
    assert profile.technologies.items[2].years is None


def test_normalize_resume_screening_hoists_root_match_fields():
    from app.models.resume_screening import ResumeScreeningResult

    raw = {
        "profile": {
            "reasoning": "x",
            "ambiguities": [],
            "identity": {"name": "Anu", "confidence": 0.9},
            "technologies": {"items": [{"name": "Python", "years": 5}], "confidence": 0.8},
            "soft_skills": {"items": [], "confidence": 0.5},
            "leadership": {"tech_lead": False, "team_lead": False, "confidence": 0.7},
            "education": {"items": [], "confidence": 0.7},
            "experience": {"total_years": 5, "confidence": 0.7},
        },
        "match_score": 72,
        "candidate_name": "Anu",
        "matching_skills": ["Python"],
        "reasoning": "Good overlap.",
    }
    result = ResumeScreeningResult.model_validate(normalize_resume_screening(raw))
    assert result.match.match_score == 72
    assert result.match.matching_skills[0].name == "Python"


def test_normalize_resume_screening_drops_profile_tech_from_not_mentioned():
    from app.models.resume_screening import ResumeScreeningResult

    raw = {
        "profile": {
            "reasoning": "x",
            "ambiguities": [],
            "identity": {"name": "Viktor", "confidence": 0.9},
            "technologies": {"items": [{"name": "LangGraph", "years": 2}], "confidence": 0.8},
            "soft_skills": {"items": [], "confidence": 0.5},
            "leadership": {"tech_lead": False, "team_lead": False, "confidence": 0.7},
            "education": {"items": [], "confidence": 0.7},
            "experience": {"total_years": 10, "confidence": 0.7},
        },
        "match": {
            "candidate_name": "Viktor",
            "match_score": 85,
            "matching_skills": [],
            "not_mentioned_skills": ["LangGraph", "CrewAI"],
            "reasoning": "x",
            "ambiguities": [],
        },
    }
    result = ResumeScreeningResult.model_validate(normalize_resume_screening(raw))
    not_names = [s.name for s in result.match.not_mentioned_skills]
    assert "LangGraph" not in not_names
    assert "CrewAI" in not_names


def test_normalize_candidate_profile_soft_skill_objects():
    raw = {
        "reasoning": "CV ok.",
        "ambiguities": [],
        "identity": {"name": "Anu"},
        "technologies": [{"name": "Python", "years": 6}],
        "soft_skills": [{"name": "Communication"}, {"name": "Problem-solving"}],
        "leadership": {"tech_lead": True, "team_lead": False},
        "education": [{"level": "bachelor", "field": "CS"}],
        "experience": {"total_years": 6},
    }
    profile = CandidateProfile.model_validate(normalize_candidate_profile(raw))
    assert profile.soft_skills.items == ["Communication", "Problem-solving"]
    assert profile.technologies.items[0].years == 6
