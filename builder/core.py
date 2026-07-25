from __future__ import annotations

import html
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
TEMPLATES_DIR = ROOT / "templates"
OUTPUT_DIR = ROOT / "docs"
SCHEMAS_DIR = ROOT / "schemas"


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Malformed JSON in {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"Expected a JSON object in {path.relative_to(ROOT)}")
    return data


def load_collection(name: str, *, include_unpublished: bool = True) -> list[dict[str, Any]]:
    folder = CONTENT_DIR / name
    if not folder.exists():
        return []
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in sorted(folder.glob("*.json")):
        item = load_json(path)
        slug = path.stem
        if slug in seen:
            raise RuntimeError(f"Slug collision in {name}: {slug}")
        seen.add(slug)
        item["slug"] = slug
        item["_source"] = str(path.relative_to(ROOT))
        if include_unpublished or is_published(item):
            items.append(item)
    return items


def is_published(item: dict[str, Any]) -> bool:
    if "published" in item:
        return bool(item["published"])
    return item.get("status") == "published"


def read_template(name: str) -> str:
    path = TEMPLATES_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing template: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def render(template: str, **values: Any) -> str:
    output = template
    for key, value in values.items():
        output = output.replace("{{ " + key + " }}", str(value))
        output = output.replace("{{" + key + "}}", str(value))
    return output


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _schema_type_matches(value: Any, expected: str) -> bool:
    checks = {
        "object": lambda v: isinstance(v, dict),
        "array": lambda v: isinstance(v, list),
        "string": lambda v: isinstance(v, str),
        "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
        "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
        "boolean": lambda v: isinstance(v, bool),
        "null": lambda v: v is None,
    }
    return checks.get(expected, lambda _v: True)(value)


def _resolve_ref(schema: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise RuntimeError(f"Unsupported schema reference: {ref}")
    node: Any = schema
    for part in ref[2:].split("/"):
        node = node[part.replace("~1", "/").replace("~0", "~")]
    if not isinstance(node, dict):
        raise RuntimeError(f"Schema reference does not point to an object: {ref}")
    return node


def _validate_value(value: Any, rule: dict[str, Any], root_schema: dict[str, Any], location: str) -> list[str]:
    import re

    if "$ref" in rule:
        return _validate_value(value, _resolve_ref(root_schema, rule["$ref"]), root_schema, location)

    if "anyOf" in rule:
        branches = [
            _validate_value(value, branch, root_schema, location)
            for branch in rule["anyOf"]
        ]
        if any(not errors for errors in branches):
            return []
        return [f"{location}: value does not match any allowed shape"]

    errors: list[str] = []
    expected = rule.get("type")
    if expected and not _schema_type_matches(value, expected):
        return [f"{location}: expected {expected}, got {type(value).__name__}"]

    if "const" in rule and value != rule["const"]:
        errors.append(f"{location}: expected {rule['const']!r}")
    if "enum" in rule and value not in rule["enum"]:
        errors.append(f"{location}: expected one of {rule['enum']!r}")

    if isinstance(value, str):
        if len(value) < rule.get("minLength", 0):
            errors.append(f"{location}: must not be empty")
        if "maxLength" in rule and len(value) > rule["maxLength"]:
            errors.append(f"{location}: exceeds maximum length {rule['maxLength']}")
        if "pattern" in rule and re.fullmatch(rule["pattern"], value) is None:
            errors.append(f"{location}: does not match required pattern")

    if isinstance(value, list):
        if len(value) < rule.get("minItems", 0):
            errors.append(f"{location}: requires at least {rule['minItems']} item(s)")
        if rule.get("uniqueItems"):
            seen = set()
            for item in value:
                marker = json.dumps(item, sort_keys=True)
                if marker in seen:
                    errors.append(f"{location}: contains duplicate items")
                    break
                seen.add(marker)
        item_rule = rule.get("items")
        if isinstance(item_rule, dict):
            for index, item in enumerate(value):
                errors.extend(_validate_value(item, item_rule, root_schema, f"{location}[{index}]"))

    if isinstance(value, dict):
        required = rule.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{location}.{key}: missing required field")
        properties = rule.get("properties", {})
        if rule.get("additionalProperties") is False:
            allowed = set(properties)
            for key in value:
                if key not in allowed:
                    errors.append(f"{location}.{key}: unexpected field")
        for key, child_rule in properties.items():
            if key in value:
                errors.extend(_validate_value(value[key], child_rule, root_schema, f"{location}.{key}"))

    return errors


def validate_schema(item: dict[str, Any], schema_name: str) -> None:
    """Validate structured content using the supported JSON Schema subset.

    This validator intentionally uses only the Python standard library so a
    normal site build never depends on an installed package. The schema file
    remains the source of truth and documents the accepted content shape.
    """
    schema_path = SCHEMAS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Missing schema: {schema_path.relative_to(ROOT)}")
    schema = load_json(schema_path)
    clean = {k: v for k, v in item.items() if not k.startswith("_")}
    errors = _validate_value(clean, schema, schema, "root")
    if errors:
        source = item.get("_source", item.get("slug", "structured content"))
        details = "\n  - ".join(errors[:20])
        extra = f"\n  - ...and {len(errors) - 20} more" if len(errors) > 20 else ""
        raise RuntimeError(f"Validation error in {source}:\n  - {details}{extra}")


def tag_set(item: dict[str, Any]) -> set[str]:
    return {str(tag).strip().casefold() for tag in item.get("tags", []) if str(tag).strip()}


def related_items(source: dict[str, Any], candidates: Iterable[dict[str, Any]], limit: int = 6) -> list[dict[str, Any]]:
    source_tags = tag_set(source)
    scored: list[tuple[int, str, dict[str, Any]]] = []
    for candidate in candidates:
        if candidate.get("slug") == source.get("slug"):
            continue
        score = len(source_tags & tag_set(candidate))
        if score:
            scored.append((score, str(candidate.get("title", "")), candidate))
    scored.sort(key=lambda row: (-row[0], row[1].casefold()))
    return [row[2] for row in scored[:limit]]


@dataclass(frozen=True)
class BuildResult:
    collection: str
    count: int
