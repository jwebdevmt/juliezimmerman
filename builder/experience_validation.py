from __future__ import annotations

from typing import Any


class ExperienceValidationError(RuntimeError):
    pass


def _require_mapping(record: dict[str, Any], key: str, source: str) -> dict[str, Any]:
    value = record.get(key)
    if not isinstance(value, dict) or not value:
        raise ExperienceValidationError(f"{source}: '{key}' must be a non-empty mapping")
    return value


def _require_text(record: dict[str, Any], key: str, source: str) -> None:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ExperienceValidationError(f"{source}: '{key}' must be non-empty text")


def validate_experience(record: dict[str, Any], source: str) -> None:
    for key in ("schema_version", "slug", "title", "summary", "experience", "perspectives", "synthesis", "publishing"):
        if key not in record or record[key] in (None, "", [], {}):
            raise ExperienceValidationError(f"{source}: missing required field '{key}'")

    if record["schema_version"] != 1:
        raise ExperienceValidationError(f"{source}: unsupported schema_version {record['schema_version']!r}; expected 1")
    for key in ("slug", "title", "summary"):
        _require_text(record, key, source)

    experience = _require_mapping(record, "experience", source)
    for key in ("type", "destination", "audience"):
        if not isinstance(experience.get(key), str) or not experience[key].strip():
            raise ExperienceValidationError(f"{source}: experience.{key} must be non-empty text")

    constraints = record.get("constraints", [])
    if not isinstance(constraints, list) or not constraints or not all(isinstance(item, str) and item.strip() for item in constraints):
        raise ExperienceValidationError(f"{source}: constraints must be a non-empty list of text")

    perspectives = record["perspectives"]
    if not isinstance(perspectives, list) or not perspectives:
        raise ExperienceValidationError(f"{source}: perspectives must be a non-empty list")
    seen: set[str] = set()
    for index, perspective in enumerate(perspectives, start=1):
        if not isinstance(perspective, dict):
            raise ExperienceValidationError(f"{source}: perspective {index} must be a mapping")
        for key in ("id", "name", "role", "excerpt", "full_text"):
            if not isinstance(perspective.get(key), str) or not perspective[key].strip():
                raise ExperienceValidationError(f"{source}: perspective {index}.{key} must be non-empty text")
        pid = perspective["id"]
        if pid in seen:
            raise ExperienceValidationError(f"{source}: duplicate perspective id '{pid}'")
        seen.add(pid)
        pin = perspective.get("pin", {})
        if pin is not None and not isinstance(pin, dict):
            raise ExperienceValidationError(f"{source}: perspective {index}.pin must be a mapping")

    synthesis = _require_mapping(record, "synthesis", source)
    for key in ("principle", "summary", "lessons"):
        if key not in synthesis or synthesis[key] in (None, "", []):
            raise ExperienceValidationError(f"{source}: synthesis.{key} is required")
    if not isinstance(synthesis["lessons"], list) or not all(isinstance(item, str) and item.strip() for item in synthesis["lessons"]):
        raise ExperienceValidationError(f"{source}: synthesis.lessons must be a list of text")

    publishing = _require_mapping(record, "publishing", source)
    outputs = publishing.get("outputs", [])
    if not isinstance(outputs, list) or not outputs:
        raise ExperienceValidationError(f"{source}: publishing.outputs must be a non-empty list")

    taxonomy = record.get("taxonomy", {})
    if taxonomy is not None:
        if not isinstance(taxonomy, dict):
            raise ExperienceValidationError(f"{source}: taxonomy must be a mapping")
        for key, values in taxonomy.items():
            if not isinstance(values, list) or not all(isinstance(item, str) and item.strip() for item in values):
                raise ExperienceValidationError(f"{source}: taxonomy.{key} must be a list of text")
