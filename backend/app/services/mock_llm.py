"""Deterministic mock LLM responses for tests and offline dev."""

import re
from typing import TypeVar

from pydantic import BaseModel

from app.models.requirements import Requirements
from app.models.resume_screening import ResumeScreeningResult

T = TypeVar("T", bound=BaseModel)

MOCK_REQUIREMENTS = {
    "reasoning": "Senior backend role: Python/FastAPI required 5+/2+ years; Docker nice-to-have.",
    "ambiguities": ["No explicit people-management requirement"],
    "role": {"title": "Senior Python Engineer", "seniority": "senior", "confidence": 0.9},
    "technologies": {
        "items": [
            {"name": "Python", "min_years": 5, "priority": "must"},
            {"name": "FastAPI", "min_years": 2, "priority": "must"},
            {"name": "Docker", "min_years": None, "priority": "nice"},
        ],
        "confidence": 0.85,
    },
    "soft_skills": {"items": ["communication", "ownership"], "confidence": 0.7},
    "leadership": {"tech_lead": True, "team_lead": False, "confidence": 0.8},
    "education": {
        "min_level": "bachelor",
        "fields": ["Computer Science", "Engineering"],
        "required": True,
        "confidence": 0.75,
    },
    "experience": {"min_total_years": 5, "confidence": 0.9},
}

MOCK_PROFILE = {
    "reasoning": "Backend engineer ~6 years IT; strong Python/FastAPI; BSc CS.",
    "ambiguities": ["IT total years estimated from role dates only"],
    "identity": {"name": "Anu Kumar", "confidence": 0.95},
    "technologies": {
        "items": [
            {"name": "Python", "years": 6},
            {"name": "FastAPI", "years": 3},
        ],
        "confidence": 0.8,
    },
    "soft_skills": {"items": ["mentoring"], "confidence": 0.5},
    "leadership": {"tech_lead": True, "team_lead": False, "confidence": 0.7},
    "education": {
        "items": [{"level": "bachelor", "field": "Computer Science"}],
        "confidence": 0.9,
    },
    "experience": {"total_years": 6, "confidence": 0.75},
}

MOCK_MATCH = {
    "candidate_name": "Anu Kumar",
    "match_score": 85,
    "matching_skills": [
        {
            "name": "Python",
            "years_match": "clear",
            "description": "6 years on CV meets 5+ required",
        },
        {
            "name": "FastAPI",
            "years_match": "clear",
            "description": "Listed in current role; JD requires 2+ years",
        },
    ],
    "not_mentioned_skills": [
        {
            "name": "Docker",
            "description": "JD nice-to-have; not on CV — may be a gap or omitted",
        }
    ],
    "reasoning": "Strong must-have tech match; Docker only a nice-to-have gap.",
    "ambiguities": ["JD leadership scope unclear vs candidate tech-lead title only"],
}


def _apply_name_hints(profile: dict, match: dict, prompt: str) -> None:
    name_match = re.search(r"CANDIDATE NAME HINT:\s*(\S+)", prompt, re.I)
    if name_match:
        profile["identity"] = {**profile["identity"], "name": name_match.group(1)}
        match["candidate_name"] = name_match.group(1)


def mock_response(prompt: str, model_class: type[T]) -> T:
    if model_class is Requirements:
        return Requirements.model_validate(MOCK_REQUIREMENTS)
    if model_class is ResumeScreeningResult:
        profile = dict(MOCK_PROFILE)
        match = dict(MOCK_MATCH)
        _apply_name_hints(profile, match, prompt)
        if "alice" in prompt.lower():
            profile["identity"] = {**profile["identity"], "name": "Alice Smith"}
            match["candidate_name"] = "Alice Smith"
            match["match_score"] = 62
            match["matching_skills"] = [
                {
                    "name": "Python",
                    "years_match": "not_enough",
                    "description": "3 years vs 5+ required",
                }
            ]
            match["not_mentioned_skills"] = [
                {"name": "FastAPI", "description": "Must-have; not found on CV"},
                {"name": "Docker", "description": "Nice-to-have; not on CV"},
            ]
            match["reasoning"] = "Partial Python match; missing FastAPI."
            match["ambiguities"] = []
        return ResumeScreeningResult.model_validate({"profile": profile, "match": match})
    raise ValueError(f"No mock for {model_class}")
