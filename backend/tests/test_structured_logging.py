import json
import logging

from app.structured_logging import configure_logging, log_event, resolve_log_format


def test_structured_json_formatter_emits_json(capsys):
    configure_logging("INFO", "json")
    logger = logging.getLogger("test.structured")
    log_event(logger, "test.event", foo="bar", count=2)
    out = capsys.readouterr().err.strip()
    payload = json.loads(out)
    assert payload["event"] == "test.event"
    assert payload["foo"] == "bar"
    assert payload["count"] == 2
    assert "ts" in payload


def test_pretty_formatter_emits_indented_json(capsys):
    configure_logging("DEBUG", "pretty")
    logger = logging.getLogger("test.structured.pretty")
    log_event(logger, "test.pretty", ok=True)
    out = capsys.readouterr().err
    assert '\n  "event": "test.pretty"' in out
    payload = json.loads(out.strip())
    assert payload["event"] == "test.pretty"
    assert payload["ok"] is True


def test_resolve_log_format_auto():
    assert resolve_log_format("DEBUG", "auto") == "pretty"
    assert resolve_log_format("INFO", "auto") == "json"
