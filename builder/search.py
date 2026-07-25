from __future__ import annotations

import json
from typing import Any

from .core import BuildResult, OUTPUT_DIR, load_collection, write_text


def _summary(item: dict[str, Any]) -> str:
    for key in ("excerpt", "summary", "description"):
        if item.get(key):
            return str(item[key])
    hero = item.get("hero", {})
    intro = hero.get("intro", []) if isinstance(hero, dict) else []
    return str(intro[0]) if intro else ""


def build() -> BuildResult:
    rows = []
    specs = {
        "writing": lambda item: f"writing/{item['slug']}.html",
        "problems": lambda item: f"problems/{item['slug']}/index.html",
        "adaptive-experiences": lambda item: f"adaptive-experiences/{item['slug']}/index.html",
        "disciplines": lambda item: f"{item['slug']}/index.html",
        "projects": lambda item: "current-projects.html",
    }
    for collection, url_for in specs.items():
        for item in load_collection(collection):
            published = item.get("published", item.get("status") == "published")
            if not published or item.get("slug") == "index":
                continue
            rows.append({
                "type": collection,
                "slug": item["slug"],
                "title": item.get("title", item["slug"].replace("-", " ").title()),
                "summary": _summary(item),
                "tags": item.get("tags", []),
                "url": url_for(item),
            })
    rows.sort(key=lambda row: (row["type"], row["title"].casefold()))
    write_text(OUTPUT_DIR / "search.json", json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
    return BuildResult("search", 1)
