"""Structured logs: JSON lines by default; pretty multi-line JSON in debug mode."""

from __future__ import annotations

import json
import logging
import time
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Iterator

from app.models.candidate_profile import CandidateProfile
from app.models.match import MatchResult
from app.models.requirements import Requirements
from app.models.resume_screening import ResumeScreeningResult

_request_ctx: ContextVar[dict[str, Any]] = ContextVar("request_ctx", default={})


def bind_request(**fields: Any) -> None:
    current = dict(_request_ctx.get())
    current.update({k: v for k, v in fields.items() if v is not None})
    _request_ctx.set(current)


def clear_request() -> None:
    _request_ctx.set({})


def _context_fields() -> dict[str, Any]:
    return dict(_request_ctx.get())


def _build_payload(record: logging.LogRecord) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
        "level": record.levelname,
        "logger": record.name,
        "event": getattr(record, "event", record.getMessage()),
        **_context_fields(),
    }
    fields = getattr(record, "fields", None)
    if isinstance(fields, dict):
        payload.update(fields)
    return payload


class StructuredJsonFormatter(logging.Formatter):
    """One JSON object per line (production default)."""

    def format(self, record: logging.LogRecord) -> str:
        payload = _build_payload(record)
        if record.exc_info and record.levelno >= logging.ERROR:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=False)


class PrettyJsonFormatter(logging.Formatter):
    """Indented JSON blocks (easier to read in debugger / local dev)."""

    def format(self, record: logging.LogRecord) -> str:
        payload = _build_payload(record)
        if record.exc_info and record.levelno >= logging.ERROR:
            payload["exception"] = self.formatException(record.exc_info)
        body = json.dumps(payload, indent=2, default=str, ensure_ascii=False)
        return f"{body}\n"


def resolve_log_format(level: str, log_format: str) -> str:
    """Return 'json' or 'pretty'."""
    fmt = (log_format or "auto").strip().lower()
    if fmt == "auto":
        return "pretty" if level.upper() == "DEBUG" else "json"
    if fmt in ("json", "pretty"):
        return fmt
    return "json"


def configure_logging(level: str = "INFO", log_format: str = "auto") -> None:
    resolved = resolve_log_format(level, log_format)
    formatter: logging.Formatter = (
        PrettyJsonFormatter() if resolved == "pretty" else StructuredJsonFormatter()
    )

    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(level.upper())
    for name in ("httpx", "httpcore", "uvicorn.access"):
        logging.getLogger(name).setLevel(logging.WARNING)


def log_event(
    logger: logging.Logger,
    event: str,
    *,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    logger.log(level, event, extra={"event": event, "fields": fields})


@contextmanager
def log_timing(
    logger: logging.Logger,
    event: str,
    **fields: Any,
) -> Iterator[None]:
    log_event(logger, f"{event}.started", **fields)
    started = time.perf_counter()
    try:
        yield
    except Exception as exc:
        log_event(
            logger,
            f"{event}.failed",
            level=logging.ERROR,
            duration_ms=int((time.perf_counter() - started) * 1000),
            error_type=type(exc).__name__,
            error=str(exc),
            **fields,
        )
        raise
    else:
        log_event(
            logger,
            f"{event}.completed",
            duration_ms=int((time.perf_counter() - started) * 1000),
            **fields,
        )


def requirements_summary(req: Requirements) -> dict[str, Any]:
    must = [t.name for t in req.technologies.items if t.priority == "must"]
    nice = [t.name for t in req.technologies.items if t.priority == "nice"]
    return {
        "role_title": req.role.title,
        "role_seniority": req.role.seniority,
        "role_confidence": req.role.confidence,
        "must_technologies": must,
        "nice_technologies": nice,
        "min_it_years": req.experience.min_total_years,
        "tech_lead": req.leadership.tech_lead,
        "team_lead": req.leadership.team_lead,
        "ambiguities_count": len(req.ambiguities),
        "reasoning_chars": len(req.reasoning),
    }


def profile_summary(profile: CandidateProfile) -> dict[str, Any]:
    return {
        "candidate_name": profile.identity.name,
        "technologies": [t.name for t in profile.technologies.items],
        "total_it_years": profile.experience.total_years,
        "tech_lead": profile.leadership.tech_lead,
        "team_lead": profile.leadership.team_lead,
        "ambiguities_count": len(profile.ambiguities),
    }


def match_summary(match: MatchResult) -> dict[str, Any]:
    return {
        "candidate_name": match.candidate_name,
        "match_score": match.match_score,
        "matching_skills": [s.name for s in match.matching_skills],
        "not_mentioned_skills": [s.name for s in match.not_mentioned_skills],
        "ambiguities_count": len(match.ambiguities),
    }


def resume_screening_summary(result: ResumeScreeningResult) -> dict[str, Any]:
    return {
        "profile": profile_summary(result.profile),
        "match": match_summary(result.match),
    }
