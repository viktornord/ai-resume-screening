"""JSON Schema from Pydantic models for Mistral structured outputs."""

from copy import deepcopy
from typing import Any

from pydantic import BaseModel


def _resolve_refs(node: Any, defs: dict[str, Any]) -> Any:
    if isinstance(node, dict):
        if "$ref" in node:
            ref_name = node["$ref"].rsplit("/", 1)[-1]
            if ref_name not in defs:
                raise ValueError(f"Unresolved schema $ref: {node['$ref']}")
            return _resolve_refs(deepcopy(defs[ref_name]), defs)
        return {key: _resolve_refs(value, defs) for key, value in node.items()}
    if isinstance(node, list):
        return [_resolve_refs(item, defs) for item in node]
    return node


def _prepare_for_mistral_strict(node: Any) -> Any:
    """Mistral strict json_schema requires additionalProperties: false on objects."""
    if isinstance(node, dict):
        out = {key: _prepare_for_mistral_strict(value) for key, value in node.items()}
        if out.get("type") == "object" and "additionalProperties" not in out:
            out["additionalProperties"] = False
        return out
    if isinstance(node, list):
        return [_prepare_for_mistral_strict(item) for item in node]
    return node


def model_json_schema(model_class: type[BaseModel]) -> dict[str, Any]:
    """Resolved JSON Schema for Mistral `response_format.json_schema.schema`."""
    schema = model_class.model_json_schema()
    defs = dict(schema.pop("$defs", {}))
    defs.update(schema.pop("definitions", {}))
    resolved = _resolve_refs(schema, defs)
    if not isinstance(resolved, dict):
        raise TypeError(f"Expected object schema for {model_class.__name__}")
    resolved.pop("$defs", None)
    resolved.pop("definitions", None)
    resolved.pop("title", None)
    return _prepare_for_mistral_strict(resolved)
