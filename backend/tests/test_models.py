import pytest

from app.models.requirements import Requirements
from app.services.mock_llm import MOCK_REQUIREMENTS


def test_requirements_mock_validates():
    req = Requirements.model_validate(MOCK_REQUIREMENTS)
    assert req.role.title == "Senior Python Engineer"
    assert req.technologies.items[0].name == "Python"
    assert "reasoning" in req.model_dump()
    assert "confidence" in req.role.model_dump()
    assert "reasoning" not in req.role.model_dump()
