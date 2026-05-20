import pytest

from app.services.llm_client import (
    LLMError,
    _loads_json_object,
    _sanitize_json_text,
    _sanitize_parsed_dict,
)


def test_loads_json_object_repairs_trailing_comma():
    raw = '{"a": 1, "b": {"c": 2,},}'
    assert _loads_json_object(raw) == {"a": 1, "b": {"c": 2}}


def test_loads_json_object_accepts_dict():
    assert _loads_json_object({"x": 1}) == {"x": 1}


def test_loads_json_object_fails_fast_on_garbage():
    with pytest.raises(LLMError, match="Invalid JSON"):
        _loads_json_object('{"a": 1 "b": 2}')


def test_sanitize_runaway_decimal_digits():
    raw = '{"confidence": 0.5555555555555555555555555555555555555555}'
    parsed = _loads_json_object(raw)
    assert parsed["confidence"] == pytest.approx(0.56, abs=0.001)


def test_sanitize_parsed_dict_rounds_confidence():
    data = {
        "profile": {
            "identity": {"confidence": 0.5555555555555555},
            "technologies": {"confidence": 0.9999999, "items": []},
        }
    }
    out = _sanitize_parsed_dict(data)
    assert out["profile"]["identity"]["confidence"] == 0.56
    assert out["profile"]["technologies"]["confidence"] == 1.0
