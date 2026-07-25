from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape as xml_escape

from . import legacy
from .core import OUTPUT_DIR, esc, write_text
from .experience_models import ExperienceRecord

DATA_DIR = OUTPUT_DIR / "adaptive-experiences" / "data"


def _generated() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def render_json(records: list[ExperienceRecord], related: dict[str, list[dict[str, object]]]) -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    public = []
    count = 0
    for record in records:
        item = record.public_dict()
        item["related_experiences"] = related.get(record.slug, [])
        public.append(item)
        write_text(DATA_DIR / f"{record.slug}.json", json.dumps(item, indent=2, ensure_ascii=False))
        count += 1
    write_text(DATA_DIR / "experiences.json", json.dumps({"schema_version": 1, "generated": _generated(), "records": public}, indent=2, ensure_ascii=False))
    write_text(DATA_DIR / "relationships.json", json.dumps({"schema_version": 1, "generated": _generated(), "records": related}, indent=2, ensure_ascii=False))
    return count + 2


def pin_records(records: list[ExperienceRecord]) -> list[dict[str, Any]]:
    pins: list[dict[str, Any]] = []
    for record in records:
        for perspective in record.perspectives:
            pin = perspective.pin
            pins.append({
                "id": f"{record.slug}--{perspective.id}",
                "experience_slug": record.slug,
                "experience_title": record.title,
                "perspective_id": perspective.id,
                "perspective_name": perspective.name,
                "perspective_role": perspective.role,
                "title": pin.get("title") or f"{perspective.name} on {record.title}",
                "description": pin.get("description") or perspective.excerpt,
                "quote": pin.get("quote") or perspective.excerpt,
                "destination_url": record.canonical_url,
                "board": pin.get("board") or record.publishing.get("pinterest_board", "Adaptive Experiences"),
                "image_template": pin.get("image_template", "perspective-quote"),
                "image": pin.get("image", record.publishing.get("default_image", "/assets/project-adaptive.svg")),
                "alt": pin.get("alt") or f"{perspective.name} perspective for {record.title}",
                "status": pin.get("status", "ready"),
                "topics": sorted(record.tags),
            })
    return pins


def render_pinterest(records: list[ExperienceRecord]) -> int:
    pins = pin_records(records)
    write_text(DATA_DIR / "pins.json", json.dumps({"schema_version": 1, "generated": _generated(), "records": pins}, indent=2, ensure_ascii=False))
    by_perspective: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pin in pins:
        by_perspective[pin["perspective_id"]].append(pin)
    count = 1
    for pid, entries in by_perspective.items():
        write_text(DATA_DIR / "pins" / f"{pid}.json", json.dumps({"schema_version": 1, "generated": _generated(), "records": entries}, indent=2, ensure_ascii=False))
        count += 1
    return count


def perspective_archives(records: list[ExperienceRecord]) -> dict[str, dict[str, Any]]:
    archives: dict[str, dict[str, Any]] = {}
    for record in records:
        for perspective in record.perspectives:
            archive = archives.setdefault(perspective.id, {"id": perspective.id, "name": perspective.name, "role": perspective.role, "entries": []})
            archive["entries"].append({
                "experience_slug": record.slug,
                "experience_title": record.title,
                "excerpt": perspective.excerpt,
                "url": record.canonical_url,
                "topics": sorted(record.tags),
            })
    return archives


def _archive_page(config: dict[str, Any], archive: dict[str, Any]) -> str:
    cards = "".join(
        f'''<article class="perspective-archive-card"><p class="eyebrow">{esc(item['experience_title'])}</p>
        <blockquote><p>{esc(item['excerpt'])}</p></blockquote>
        <a class="button" href="{esc(item['url'])}">Read the complete experience →</a></article>'''
        for item in archive["entries"]
    )
    content = f'''<main class="site-shell"><section class="section writing-page">
      <div class="section-header writing-intro"><p class="eyebrow">Preserved Perspective</p>
      <h1 class="page-title">{esc(archive['name'])}</h1><p class="section-intro">{esc(archive['role'])}. Every appearance is generated from the canonical experience records.</p></div>
      <div class="perspective-archive-grid">{cards}</div></section></main>'''
    return legacy.base_page(config, f"{archive['name']} Perspectives", archive["role"], content, active="adaptive-experiences", level="archive")


def render_archives(config: dict[str, Any], records: list[ExperienceRecord]) -> int:
    archives = perspective_archives(records)
    for pid, archive in archives.items():
        write_text(OUTPUT_DIR / "adaptive-experiences" / "perspectives" / pid / "index.html", _archive_page(config, archive))
    write_text(DATA_DIR / "perspectives.json", json.dumps({"schema_version": 1, "generated": _generated(), "records": list(archives.values())}, indent=2, ensure_ascii=False))
    return len(archives) + 1


def render_rss(config: dict[str, Any], records: list[ExperienceRecord]) -> int:
    base_url = str(config.get("site_url", "https://juliezimmerman.me")).rstrip("/")
    items = []
    for record in records:
        link = base_url + record.canonical_url
        items.append(f"""<item><title>{xml_escape(record.title)}</title><link>{xml_escape(link)}</link><guid>{xml_escape(link)}</guid><description>{xml_escape(record.summary)}</description></item>""")
    now = format_datetime(datetime.now(timezone.utc))
    rss = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Adaptive Experiences</title><link>{xml_escape(base_url + '/adaptive-experiences/')}</link><description>Human-centered planning through preserved perspectives and structured synthesis.</description><lastBuildDate>{now}</lastBuildDate>{''.join(items)}</channel></rss>'''
    write_text(OUTPUT_DIR / "adaptive-experiences" / "feed.xml", rss)
    return 1
