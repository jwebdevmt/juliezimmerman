from __future__ import annotations

from pathlib import Path
from typing import Any

from .core import BuildResult, CONTENT_DIR
from .experience_models import ExperienceRecord
from .experience_relationships import related_records
from .experience_renderers import render_archives, render_json, render_pinterest, render_rss
from .experience_validation import validate_experience
from .simple_yaml import load as load_yaml

EXPERIENCE_DIR = CONTENT_DIR / "experiences"


def load_experiences() -> list[ExperienceRecord]:
    records: list[ExperienceRecord] = []
    if not EXPERIENCE_DIR.exists():
        return records
    slugs: set[str] = set()
    for path in sorted(EXPERIENCE_DIR.glob("*.yaml")):
        raw = load_yaml(path)
        raw.setdefault("slug", path.stem)
        validate_experience(raw, str(path))
        record = ExperienceRecord.from_mapping(raw, path)
        if record.slug in slugs:
            raise RuntimeError(f"{path}: duplicate experience slug '{record.slug}'")
        slugs.add(record.slug)
        if record.published:
            records.append(record)
    return records


def build(config: dict[str, Any]) -> BuildResult:
    records = load_experiences()
    if not records:
        return BuildResult("canonical experiences", 0)
    relationships = related_records(records)
    count = 0
    count += render_json(records, relationships)
    count += render_pinterest(records)
    count += render_archives(config, records)
    count += render_rss(config, records)
    return BuildResult("canonical experience publishing engine", count)
