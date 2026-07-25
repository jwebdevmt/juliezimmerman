from __future__ import annotations

from typing import Any

from . import legacy
from .core import BuildResult, OUTPUT_DIR, esc, load_collection, read_template, related_items, render, validate_schema, write_text


def _paragraphs(values: list[str]) -> str:
    return "\n".join(f"<p>{esc(value)}</p>" for value in values)


def _list(values: list[str], class_name: str = "discipline-list") -> str:
    if not values:
        return ""
    return f'<ul class="{class_name}">' + "".join(f"<li>{esc(value)}</li>" for value in values) + "</ul>"


def _project_card(project: dict[str, Any]) -> str:
    subtitle = f'<p class="project-subtitle">{esc(project.get("subtitle"))}</p>' if project.get("subtitle") else ""
    highlights = _list(project.get("highlights", []), "project-highlights")
    return f'''<article class="discipline-project-card">
<h3>{esc(project.get("title", "Untitled project"))}</h3>
{subtitle}
<p>{esc(project.get("summary", ""))}</p>
{_paragraphs(project.get("details", []))}
{highlights}
</article>'''


def _experience_card(item: dict[str, Any]) -> str:
    evidence = _list(item.get("evidence", []), "experience-evidence")
    return f'''<article class="experience-card">
<p class="eyebrow">{esc(item.get("organization", ""))}</p>
<h3>{esc(item.get("role", ""))}</h3>
<p>{esc(item.get("summary", ""))}</p>
{evidence}
</article>'''


def _technology_groups(groups: list[dict[str, Any]]) -> str:
    rows = []
    for group in groups:
        pills = "".join(f'<span class="skill-pill">{esc(item)}</span>' for item in group.get("items", []))
        rows.append(f'<div class="technology-group"><h3>{esc(group.get("label", ""))}</h3><div class="skill-cloud">{pills}</div></div>')
    return "\n".join(rows)


def _related_writing(page: dict[str, Any], writing: list[dict[str, Any]]) -> str:
    config = page.get("related_writing", {})
    desired_tags = {str(tag).casefold() for tag in config.get("match_tags", [])}
    proxy = {"slug": page.get("slug"), "tags": list(desired_tags)}
    matches = related_items(proxy, [p for p in writing if p.get("published", False)], config.get("limit", 6))
    manual = config.get("manual_items", [])
    cards = []
    for link in manual:
        cards.append(f'<a class="related-card" href="{esc(link.get("url", "#"))}"><strong>{esc(link.get("label", "Read more"))}</strong></a>')
    for post in matches:
        cards.append(f'<a class="related-card" href="../writing/{esc(post["slug"])}.html"><strong>{esc(post.get("title", "Untitled"))}</strong><span>{esc(legacy.excerpt(post, 24))}</span></a>')
    if not cards:
        return ""
    return f'''<section class="discipline-section">
<p class="eyebrow">Writing</p><h2>{esc(config.get("title", "Related Writing"))}</h2>
<p>{esc(config.get("intro", ""))}</p>
<div class="related-grid">{"".join(cards)}</div>
</section>'''


def render_page(config: dict[str, Any], page: dict[str, Any], projects: dict[str, dict[str, Any]], writing: list[dict[str, Any]]) -> str:
    philosophy = page["philosophy"]
    problems = page["problems"]
    approach = page["approach"]
    selected_projects = [projects[slug] for slug in page.get("projects", []) if slug in projects]
    project_html = "\n".join(_project_card(project) for project in selected_projects)
    experience_html = "\n".join(_experience_card(item) for item in page.get("experience", []))
    business = page.get("business_value")
    business_html = ""
    if business:
        business_html = f'''<section class="discipline-section discipline-value">
<p class="eyebrow">Business Value</p><h2>{esc(business.get("title", ""))}</h2>{_paragraphs(business.get("paragraphs", []))}
</section>'''
    contact = page["contact"]
    cta = contact["cta"]
    template = read_template("discipline.html")
    content = render(
        template,
        eyebrow=esc(page["hero"].get("eyebrow", page["title"])),
        headline=esc(page["hero"]["headline"]),
        hero_intro=_paragraphs(page["hero"].get("intro", [])),
        philosophy_title=esc(philosophy["title"]),
        philosophy_anchor=esc(philosophy["anchor"]),
        philosophy_intro=esc(philosophy.get("intro", "")),
        principles=_list(philosophy.get("principles", []), "principle-list"),
        philosophy_closing=esc(philosophy.get("closing", "")),
        problems_title=esc(problems["title"]),
        problems_intro=esc(problems.get("intro", "")),
        problems_items=_list(problems.get("items", [])),
        approach_title=esc(approach["title"]),
        approach_body=_paragraphs(approach.get("paragraphs", [])),
        projects=project_html,
        experience=experience_html,
        technologies=_technology_groups(page.get("technologies", [])),
        related_writing=_related_writing(page, writing),
        business_value=business_html,
        contact_title=esc(contact["title"]),
        contact_body=_paragraphs(contact.get("paragraphs", [])),
        contact_url=esc(cta.get("url", "/contact/")),
        contact_label=esc(cta.get("label", "Contact Julie")),
        closing_statement=esc(page.get("closing_statement", "")),
    )
    return legacy.base_page(config, page["seo"]["title"].split(" | ")[0], page["seo"]["description"], content, active="resume", level="nested")


def build(config: dict[str, Any], writing: list[dict[str, Any]]) -> BuildResult:
    pages = load_collection("disciplines")
    project_items = load_collection("projects")
    projects = {item["slug"]: item for item in project_items}
    count = 0
    for page in pages:
        validate_schema(page, "discipline-page.schema.json")
        if page.get("status") != "published":
            continue
        missing = [slug for slug in page.get("projects", []) if slug not in projects]
        if missing:
            raise RuntimeError(f"Discipline {page['slug']} references missing projects: {', '.join(missing)}")
        write_text(OUTPUT_DIR / page["slug"] / "index.html", render_page(config, page, projects, writing))
        count += 1
    return BuildResult("disciplines", count)
