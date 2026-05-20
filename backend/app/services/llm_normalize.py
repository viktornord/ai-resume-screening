"""Coerce common LLM JSON shapes into Pydantic-compatible payloads before validation."""

import re
from typing import Any

from pydantic import BaseModel

from app.models.candidate_profile import CandidateProfile
from app.models.requirements import Requirements
from app.models.resume_screening import ResumeScreeningResult

DEFAULT_CONFIDENCE = 0.7
_VALID_SENIORITY = frozenset({"junior", "mid", "senior", "lead", "unknown"})

_MATCH_ROOT_KEYS = frozenset(
    {
        "candidate_name",
        "match_score",
        "matching_skills",
        "not_mentioned_skills",
        "reasoning",
        "ambiguities",
    }
)


def _clamp_confidence(value: Any, default: float = DEFAULT_CONFIDENCE) -> float:
    if isinstance(value, (int, float)):
        return round(max(0.0, min(1.0, float(value))), 2)
    return default


def _normalize_items_section(
    raw: Any,
    *,
    default_confidence: float = DEFAULT_CONFIDENCE,
) -> dict[str, Any]:
    if raw is None:
        return {"items": [], "confidence": default_confidence}
    if isinstance(raw, dict):
        items = raw.get("items")
        if items is None and any(k in raw for k in ("name", "min_years", "years", "priority")):
            items = [raw]
        elif items is None:
            items = []
        conf = raw.get("confidence", default_confidence)
        return {
            "items": items if isinstance(items, list) else [],
            "confidence": _clamp_confidence(conf, default_confidence),
        }
    if isinstance(raw, list):
        return {"items": raw, "confidence": default_confidence}
    return {"items": [], "confidence": default_confidence}


def _normalize_soft_skills_section(raw: Any) -> dict[str, Any]:
    section = _normalize_items_section(raw)
    items: list[str] = []
    for item in section["items"]:
        if isinstance(item, str):
            items.append(item)
        elif isinstance(item, dict):
            name = item.get("name") or item.get("skill")
            if name:
                items.append(str(name))
    section["items"] = items
    return section


def _coerce_tech_priority(value: Any) -> str:
    if isinstance(value, str) and value.strip().lower() in ("nice", "optional", "preferred", "plus"):
        return "nice"
    return "must"


def _normalize_jd_tech_items(items: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "name": str(item.get("name", "")),
                "min_years": item.get("min_years"),
                "priority": _coerce_tech_priority(item.get("priority")),
            }
        )
    return out


def _parse_cv_tech_string(raw: str) -> dict[str, Any]:
    text = raw.strip()
    match = re.match(r"^(.+?)\s*[\(\-–—]\s*(\d+(?:\.\d+)?)\s*(?:\+?\s*)?years?\s*\)?\s*$", text, re.I)
    if match:
        return {"name": match.group(1).strip(), "years": float(match.group(2))}
    return {"name": text, "years": None}


def _normalize_cv_tech_items(items: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, str) and item.strip():
            out.append(_parse_cv_tech_string(item))
            continue
        if not isinstance(item, dict):
            continue
        years = item.get("years")
        if years is not None and not isinstance(years, (int, float)):
            years = None
        out.append(
            {
                "name": str(item.get("name", "")).strip(),
                "years": float(years) if years is not None else None,
            }
        )
    return [t for t in out if t["name"]]


def _normalize_role_section(raw: Any, *, default_confidence: float = 0.75) -> dict[str, Any]:
    section = raw if isinstance(raw, dict) else {}
    title = str(section.get("title") or "").strip()
    if title.lower() == "unknown":
        title = ""
    seniority = section.get("seniority")
    if seniority not in _VALID_SENIORITY:
        seniority = "unknown"
    return {
        "title": title,
        "seniority": seniority,
        "confidence": _clamp_confidence(section.get("confidence"), default_confidence),
    }


def _normalize_leadership_section(raw: Any, *, default_confidence: float = 0.75) -> dict[str, Any]:
    section = raw if isinstance(raw, dict) else {}
    return {
        "tech_lead": bool(section.get("tech_lead", False)),
        "team_lead": bool(section.get("team_lead", False)),
        "confidence": _clamp_confidence(section.get("confidence"), default_confidence),
    }


def _normalize_jd_education_section(raw: Any, *, default_confidence: float = 0.7) -> dict[str, Any]:
    section = raw if isinstance(raw, dict) else {}
    fields = section.get("fields")
    if not isinstance(fields, list):
        fields = []
    return {
        "min_level": section.get("min_level"),
        "fields": [str(f) for f in fields if f is not None and str(f).strip()],
        "required": bool(section.get("required", False)),
        "confidence": _clamp_confidence(section.get("confidence"), default_confidence),
    }


def _normalize_jd_experience_section(raw: Any, *, default_confidence: float = 0.7) -> dict[str, Any]:
    section = raw if isinstance(raw, dict) else {}
    min_years = section.get("min_total_years")
    if min_years is not None and not isinstance(min_years, (int, float)):
        min_years = None
    return {
        "min_total_years": float(min_years) if min_years is not None else None,
        "confidence": _clamp_confidence(section.get("confidence"), default_confidence),
    }


def _normalize_identity_section(raw: Any, *, default_confidence: float = 0.8) -> dict[str, Any]:
    section = raw if isinstance(raw, dict) else {}
    name = str(section.get("name") or "").strip()
    return {
        "name": name,
        "confidence": _clamp_confidence(section.get("confidence"), default_confidence),
    }


def _normalize_cv_experience_section(raw: Any, *, default_confidence: float = 0.7) -> dict[str, Any]:
    section = raw if isinstance(raw, dict) else {}
    total = section.get("total_years")
    if total is not None and not isinstance(total, (int, float)):
        total = None
    return {
        "total_years": float(total) if total is not None else None,
        "confidence": _clamp_confidence(section.get("confidence"), default_confidence),
    }


def normalize_requirements(data: dict[str, Any]) -> dict[str, Any]:
    out = dict(data)
    out["role"] = _normalize_role_section(out.get("role"))
    tech = _normalize_items_section(out.get("technologies"))
    tech["items"] = _normalize_jd_tech_items(tech["items"])
    out["technologies"] = tech
    out["soft_skills"] = _normalize_soft_skills_section(out.get("soft_skills"))
    out["leadership"] = _normalize_leadership_section(out.get("leadership"))
    out["education"] = _normalize_jd_education_section(out.get("education"))
    out["experience"] = _normalize_jd_experience_section(out.get("experience"))
    out["ambiguities"] = list(out.get("ambiguities") or [])
    out.setdefault("reasoning", "")
    return out


def normalize_candidate_profile(data: dict[str, Any]) -> dict[str, Any]:
    out = dict(data)
    out["identity"] = _normalize_identity_section(out.get("identity"))
    tech = _normalize_items_section(out.get("technologies"))
    tech["items"] = _normalize_cv_tech_items(tech["items"])
    out["technologies"] = tech
    out["soft_skills"] = _normalize_soft_skills_section(out.get("soft_skills"))
    out["leadership"] = _normalize_leadership_section(out.get("leadership"), default_confidence=0.7)
    education = out.get("education")
    if isinstance(education, list):
        out["education"] = {"items": education, "confidence": DEFAULT_CONFIDENCE}
    else:
        edu = _normalize_items_section(education)
        items: list[dict[str, str]] = []
        for item in edu["items"]:
            if isinstance(item, dict):
                items.append(
                    {
                        "level": str(item.get("level", "")),
                        "field": str(item.get("field", "")),
                    }
                )
        edu["items"] = items
        out["education"] = edu
    out["experience"] = _normalize_cv_experience_section(out.get("experience"))
    out.setdefault("ambiguities", [])
    out.setdefault("reasoning", "")
    return out


def _normalize_matching_skills(items: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, str) and item.strip():
            out.append(
                {
                    "name": item.strip(),
                    "years_match": "n/a",
                    "description": "Listed as matching skill",
                }
            )
            continue
        if not isinstance(item, dict):
            continue
        ym = item.get("years_match", "n/a")
        if ym not in ("clear", "not_enough", "ambiguous", "n/a"):
            ym = "ambiguous"
        out.append(
            {
                "name": str(item.get("name", "")).strip(),
                "years_match": ym,
                "description": str(item.get("description", "")).strip() or "Match noted",
            }
        )
    return [s for s in out if s["name"]]


def _normalize_not_mentioned_skills(items: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, str) and item.strip():
            out.append({"name": item.strip(), "description": "Not mentioned on CV"})
            continue
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "name": str(item.get("name", "")).strip(),
                "description": str(item.get("description", "")).strip() or "Not mentioned on CV",
            }
        )
    return [s for s in out if s["name"]]


def _profile_tech_keys(profile: dict[str, Any]) -> set[str]:
    tech = profile.get("technologies")
    if not isinstance(tech, dict):
        return set()
    items = tech.get("items")
    if not isinstance(items, list):
        return set()
    keys: set[str] = set()
    for item in items:
        if isinstance(item, dict):
            name = str(item.get("name", "")).strip()
        elif isinstance(item, str):
            name = item.strip()
        else:
            continue
        if name:
            keys.add(name.lower())
    return keys


def normalize_match_result(data: dict[str, Any]) -> dict[str, Any]:
    section = data if isinstance(data, dict) else {}
    score = section.get("match_score", 0)
    if not isinstance(score, int):
        try:
            score = int(float(score))
        except (TypeError, ValueError):
            score = 0
    matching = section.get("matching_skills")
    if not isinstance(matching, list):
        matching = []
    not_mentioned = section.get("not_mentioned_skills")
    if not isinstance(not_mentioned, list):
        not_mentioned = []
    return {
        "candidate_name": str(section.get("candidate_name", "")).strip(),
        "match_score": max(0, min(100, score)),
        "matching_skills": _normalize_matching_skills(matching),
        "not_mentioned_skills": _normalize_not_mentioned_skills(not_mentioned),
        "reasoning": str(section.get("reasoning", "")).strip(),
        "ambiguities": list(section.get("ambiguities") or []),
    }


def normalize_resume_screening(data: dict[str, Any]) -> dict[str, Any]:
    out = dict(data)
    match: dict[str, Any] = {}
    if isinstance(out.get("match"), dict):
        match = dict(out["match"])
    for key in _MATCH_ROOT_KEYS:
        if key in out and key not in match:
            match[key] = out[key]
    profile: dict[str, Any] = {}
    if isinstance(out.get("profile"), dict):
        profile = normalize_candidate_profile(out["profile"])
        out["profile"] = profile
    match = normalize_match_result(match)
    on_profile = _profile_tech_keys(profile)
    if on_profile:
        match["not_mentioned_skills"] = [
            s
            for s in match["not_mentioned_skills"]
            if s["name"].lower() not in on_profile
        ]
    out["match"] = match
    return out


def normalize_llm_payload(data: dict[str, Any], model_class: type[BaseModel]) -> dict[str, Any]:
    if model_class is Requirements:
        return normalize_requirements(data)
    if model_class is CandidateProfile:
        return normalize_candidate_profile(data)
    if model_class is ResumeScreeningResult:
        return normalize_resume_screening(data)
    return data
