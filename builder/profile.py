from __future__ import annotations
from typing import Any
from . import legacy
from .core import BuildResult, CONTENT_DIR, OUTPUT_DIR, esc, load_json, read_template, render, write_text


def _paragraphs(values: list[str]) -> str:
    return "\n".join(f"<p>{esc(v)}</p>" for v in values)


def _list(values: list[str], class_name: str = "discipline-list") -> str:
    return f'<ul class="{class_name}">' + "".join(f"<li>{esc(v)}</li>" for v in values) + "</ul>"


def _competencies(groups: list[dict[str, Any]]) -> str:
    rows=[]
    for group in groups:
        pills=''.join(f'<span class="skill-pill">{esc(x)}</span>' for x in group.get('items',[]))
        rows.append(f'<div class="technology-group"><h3>{esc(group.get("label",""))}</h3><div class="skill-cloud">{pills}</div></div>')
    return "\n".join(rows)


def _experience(items: list[dict[str, Any]]) -> str:
    rows=[]
    for item in items:
        rows.append(f'''<article class="resume-role">
<div class="resume-role-heading"><div><p class="eyebrow">{esc(item.get("organization",""))}</p><h3>{esc(item.get("role",""))}</h3></div><p class="resume-dates">{esc(item.get("dates",""))}</p></div>
{_list(item.get("bullets",[]), "experience-evidence")}
</article>''')
    return "\n".join(rows)


def build_resume(config: dict[str, Any]) -> BuildResult:
    page=load_json(CONTENT_DIR/'resume.json')
    cards=''.join(f'<a class="related-card" href="{esc(url)}"><strong>{esc(title)}</strong><span>{esc(desc)}</span></a>' for title,url,desc in page['disciplines'])
    add=page['additional']
    additional=f'''<article class="resume-role"><div class="resume-role-heading"><div><p class="eyebrow">{esc(add['organization'])}</p><h3>{esc(add['role'])}</h3></div><p class="resume-dates">{esc(add['dates'])}</p></div><p>{esc(add['body'])}</p></article>'''
    content=render(read_template('resume.html'),eyebrow=esc(page['hero']['eyebrow']),headline=esc(page['hero']['headline']),hero_intro=_paragraphs(page['hero']['intro']),summary=esc(page['summary']),disciplines=cards,competencies=_competencies(page['competencies']),experience=_experience(page['experience']),additional=additional,education=esc(page['education']),contact_url=esc(page['contact_url']))
    html=legacy.base_page(config,'Experience',page['seo']['description'],content,active='resume',level='nested')
    write_text(OUTPUT_DIR/'resume'/'index.html',html)
    return BuildResult('master resume',1)


def build_how_i_work(config: dict[str, Any]) -> BuildResult:
    page=load_json(CONTENT_DIR/'how-i-work.json')
    sections=[]
    for section in page['sections']:
        sections.append(f'''<section class="discipline-section"><p class="eyebrow">Method</p><h2>{esc(section['title'])}</h2>{_paragraphs(section['body'])}</section>''')
    content=render(read_template('how-i-work.html'),eyebrow=esc(page['hero']['eyebrow']),headline=esc(page['hero']['headline']),hero_intro=_paragraphs(page['hero']['intro']),sections='\n'.join(sections),principles=_list(page['principles'],'principle-list'),contact_url=esc(page['contact_url']))
    html=legacy.base_page(config,'How I Solve Problems',page['seo']['description'],content,active='how-i-work',level='root')
    write_text(OUTPUT_DIR/'how-i-work.html',html)
    return BuildResult('engineering philosophy',1)


def build(config: dict[str, Any]) -> list[BuildResult]:
    return [build_resume(config),build_how_i_work(config)]
