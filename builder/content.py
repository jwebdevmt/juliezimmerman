from __future__ import annotations
from typing import Any

def normalize_item(item: dict[str, Any], slug: str, collection: str) -> dict[str, Any]:
    """Return one predictable metadata shape without breaking legacy content."""
    normalized = dict(item)
    normalized["slug"] = slug
    normalized.setdefault("content_type", collection)
    normalized.setdefault("summary", normalized.get("excerpt", ""))
    normalized.setdefault("excerpt", normalized.get("summary", ""))
    category = normalized.get("category")
    normalized.setdefault("categories", [category] if category else [])
    normalized.setdefault("tags", [])
    normalized.setdefault("featured", False)
    normalized.setdefault("display_order", 999)
    normalized.setdefault("principles", [])
    normalized.setdefault("related", [])
    normalized.setdefault("perspectives", [])
    normalized.setdefault("looking_back", "")
    return normalized
