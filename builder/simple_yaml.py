"""Tiny YAML subset loader for the site's canonical content records.

Supports the structures used by Adaptive Experiences: nested mappings, lists,
quoted/unquoted scalars, booleans, nulls, numbers, inline [] lists, and | block
strings. It intentionally rejects advanced YAML features so the build remains
stdlib-only and predictable.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any


class YAMLSubsetError(RuntimeError):
    pass


def _scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return None
    if value in {"null", "Null", "NULL", "~"}:
        return None
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if value.startswith("[") and value.endswith("]"):
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError) as exc:
            raise YAMLSubsetError(f"Invalid inline list: {value}") from exc
        if not isinstance(parsed, list):
            raise YAMLSubsetError(f"Expected inline list: {value}")
        return parsed
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError) as exc:
            raise YAMLSubsetError(f"Invalid quoted scalar: {value}") from exc
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?(?:\d+\.\d*|\d*\.\d+)", value):
        return float(value)
    return value


def loads(text: str, *, source: str = "<yaml>") -> dict[str, Any]:
    raw = text.expandtabs(2).splitlines()
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    pending: dict[int, tuple[Any, str]] = {}
    i = 0

    while i < len(raw):
        original = raw[i]
        i += 1
        if not original.strip() or original.lstrip().startswith("#"):
            continue
        indent = len(original) - len(original.lstrip(" "))
        if indent % 2:
            raise YAMLSubsetError(f"{source}:{i}: indentation must use multiples of two spaces")
        line = original.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        # Materialize a pending mapping key as list/dict based on this line.
        if indent in pending:
            owner, key = pending.pop(indent)
            container: Any = [] if line.startswith("- ") else {}
            owner[key] = container
            parent = container
            stack.append((indent - 1, container))

        if line.startswith("- "):
            if not isinstance(parent, list):
                raise YAMLSubsetError(f"{source}:{i}: list item found outside a list")
            item_text = line[2:].strip()
            if ":" in item_text:
                key, value = item_text.split(":", 1)
                item: dict[str, Any] = {}
                parent.append(item)
                value = value.strip()
                if value == "":
                    item[key.strip()] = None
                    pending[indent + 2] = (item, key.strip())
                elif value == "|":
                    block, i = _read_block(raw, i, indent)
                    item[key.strip()] = block
                else:
                    item[key.strip()] = _scalar(value)
                stack.append((indent, item))
            else:
                parent.append(_scalar(item_text))
            continue

        if ":" not in line:
            raise YAMLSubsetError(f"{source}:{i}: expected key: value")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not isinstance(parent, dict):
            raise YAMLSubsetError(f"{source}:{i}: mapping entry found outside a mapping")
        if value == "|":
            block, i = _read_block(raw, i, indent)
            parent[key] = block
        elif value == "":
            parent[key] = None
            pending[indent + 2] = (parent, key)
        else:
            parent[key] = _scalar(value)

    return root


def _read_block(lines: list[str], index: int, parent_indent: int) -> tuple[str, int]:
    block_lines: list[str] = []
    minimum = parent_indent + 2
    while index < len(lines):
        line = lines[index]
        if line.strip():
            indent = len(line) - len(line.lstrip(" "))
            if indent < minimum:
                break
            block_lines.append(line[minimum:])
        else:
            block_lines.append("")
        index += 1
    return "\n".join(block_lines).rstrip(), index


def load(path: Path) -> dict[str, Any]:
    data = loads(path.read_text(encoding="utf-8"), source=str(path))
    if not isinstance(data, dict):
        raise YAMLSubsetError(f"Expected mapping in {path}")
    return data
