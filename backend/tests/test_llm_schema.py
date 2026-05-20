import json

from app.models.requirements import Requirements
from app.models.resume_screening import ResumeScreeningResult
from app.services.llm_schema import model_json_schema


def test_llm_schema_inlines_defs_no_ref():
    schema = model_json_schema(Requirements)
    dumped = json.dumps(schema)
    assert "$ref" not in dumped
    assert schema["type"] == "object"
    assert "role" in schema.get("properties", {})


def test_resume_screening_schema_resolves():
    schema = model_json_schema(ResumeScreeningResult)
    assert "profile" in schema.get("properties", {})
    assert "match" in schema.get("properties", {})
