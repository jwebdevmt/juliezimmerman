import html
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("docs")
CONFIG_FILE = Path("config.json")
CONTENT_DIR = Path("content") / "writing"
ADAPTIVE_DIR = Path("content") / "adaptive-experiences"
PROBLEMS_DIR = Path("content") / "problems"
ASSETS_DIR = Path("assets")
TEMPLATES_DIR = Path("templates")
CNAME_FILE = Path("CNAME")


def e(value):
    return html.escape("" if value is None else str(value), quote=True)


def load_config():
    with CONFIG_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_json_files(folder, label):
    items = []
    seen = set()

    if not folder.exists():
        return items

    for path in folder.glob("*.json"):
        slug = path.stem

        if slug in seen:
            raise RuntimeError(f"Slug collision detected in {label}: {slug}")

        seen.add(slug)

        try:
            with path.open("r", encoding="utf-8") as f:
                item = json.load(f)
        except json.JSONDecodeError as err:
            print(f"Skipping {path.name}: malformed JSON — {err}")
            continue

        item["slug"] = slug
        items.append(item)

    items.sort(key=lambda p: p.get("date", ""), reverse=True)
    return items


def load_posts():
    return load_json_files(CONTENT_DIR, "writing")


def load_adaptive_pages():
    return load_json_files(ADAPTIVE_DIR, "adaptive-experiences")
    
    
def load_problem_pages():
    return load_json_files(PROBLEMS_DIR, "problems")


def published_posts(posts):
    return [p for p in posts if p.get("published", False)]


def excerpt(post, words=34):
    if post.get("excerpt"):
        return post["excerpt"]

    body = post.get("body", [])
    text = str(body[0]) if isinstance(body, list) and body else str(body or "")
    bits = text.split()

    if len(bits) <= words:
        return text

    return " ".join(bits[:words]).rstrip(".,;:") + "…"


def read_template(name):
    path = TEMPLATES_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing template: {path}")
    return path.read_text(encoding="utf-8")


def render(template, **values):
    output = template
    for key, value in values.items():
        output = output.replace("{{ " + key + " }}", str(value))
        output = output.replace("{{" + key + "}}", str(value))
    return output


def asset_prefix(level="root"):
    if level == "nested":
        return "../"
    if level == "deep":
        return "../../"
    return ""


def page_href(slug, level="root"):
    prefix = asset_prefix(level)

    if slug == "index":
        return f"{prefix}index.html"
    if slug == "writing":
        return f"{prefix}writing.html"
    if slug == "adaptive-experiences":
        return f"{prefix}adaptive-experiences/index.html"
    if slug == "problems":
        return f"{prefix}problems/index.html"

    return f"{prefix}{slug}.html"


def post_href(post, level="root"):
    return f"{asset_prefix(level)}writing/{post['slug']}.html"


def adaptive_href(page, level="root"):
    prefix = asset_prefix(level)

    if page["slug"] == "index":
        return f"{prefix}adaptive-experiences/index.html"

    return f"{prefix}adaptive-experiences/{page['slug']}/index.html"


def problem_href(page, level="root"):
    prefix = asset_prefix(level)

    if page["slug"] == "index":
        return f"{prefix}problems/index.html"

    return f"{prefix}problems/{page['slug']}/index.html"


def nav_links(config, active="index", level="root"):
    rows = []

    for item in config.get("nav", []):
        slug = item.get("slug", "")
        label = item.get("label", slug.title())
        active_class = " active" if slug == active else ""

        rows.append(
            f'<a class="nav-link{active_class}" href="{page_href(slug, level)}">{e(label)}</a>'
        )

    return "\n        ".join(rows)


def base_page(config, title, description, content, active="index", level="root"):
    site = config.get("site", {})
    owner = config.get("owner", {})
    template = read_template("base.html")

    return render(
        template,
        title=e(title),
        description=e(description or site.get("intro") or site.get("tagline") or ""),
        site_title=e(site.get("title", "Julie Zimmerman")),
        owner_name=e(owner.get("name", site.get("title", "Julie Zimmerman"))),
        asset_prefix=asset_prefix(level),
        nav_links=nav_links(config, active, level),
        content=content,
        footer_note=e(site.get("tagline", "WordPress systems, data integrations, and practical problem-solving")),
        year=datetime.now().year,
    )


def article_card(post, level="root"):
    template = read_template("article-card.html")
    return render(
        template,
        url=post_href(post, level),
        title=e(post.get("title", "Untitled")),
        description=e(excerpt(post)),
        category=e(post.get("category", "Systems")),
        date=e(post.get("date", "")),
    )


def work_cards(config):
    cards = []

    for area in config.get("work_areas", []):
        title = e(area.get("title", "Work"))
        description = e(area.get("description", ""))
        cards.append(f'''<article class="card">
          <span class="tag">{title}</span>
          <h3>{title}</h3>
          <p>{description}</p>
        </article>''')

    return "\n".join(cards)


def build_home(config, posts):
    site = config.get("site", {})
    owner = config.get("owner", {})

    recent = "\n".join(article_card(p) for p in published_posts(posts)[:4])
    if not recent:
        recent = "<p>Writing coming soon.</p>"

    template = read_template("home.html")
    content = render(
        template,
        owner_name=e(owner.get("name", site.get("title", "Julie Zimmerman"))),
        tagline=e(site.get("tagline", "Systems. Solutions. Insight.")),
        intro=e(site.get("intro", "")),
        work_cards=work_cards(config),
        recent_articles=recent,
    )

    return base_page(config, "Home", site.get("intro", ""), content, active="index")


def paragraphs(items):
    if not items:
        return ""
    return "\n".join(f"<p>{e(item)}</p>" for item in items)


def skill_cloud(skills):
    if not skills:
        return ""

    pills = "\n".join(f'<span class="skill-pill">{e(skill)}</span>' for skill in skills)

    return f'''<section class="skill-cloud" aria-label="Technical skills">
{pills}
</section>'''


def build_about(config):
    about = config.get("about", {})
    body = paragraphs(about.get("body", []))
    skills = skill_cloud(about.get("skills", []))

    content = f'''<main class="site-shell">
  <article class="article-layout">
    <p class="eyebrow">About</p>
    <h1>Systems work with practical consequences.</h1>
    {body}
    <h2>Technical range</h2>
    {skills}
  </article>
</main>'''

    return base_page(config, "About", "About Julie Zimmerman", content, active="about")


def build_writing(config, posts):
    cards = "\n".join(article_card(p) for p in published_posts(posts))
    if not cards:
        cards = "<p>Writing coming soon.</p>"

    content = f'''<main class="site-shell">
  <section class="section hex-accent">
    <div class="section-header">
      <p class="eyebrow">Writing</p>
      <h1 class="page-title">Technical notes from the work.</h1>
      <p class="section-intro">Articles on WordPress systems, data integrations, accessibility, AI-assisted workflows, and real production constraints.</p>
    </div>
    <div class="grid two">
      {cards}
    </div>
  </section>
</main>'''

    return base_page(config, "Writing", "Technical writing by Julie Zimmerman", content, active="writing")


def build_contact(config):
    owner = config.get("owner", {})
    contact = config.get("contact", {})
    zee_url = owner.get("zee_url", "https://zeecreative.com")
    email = owner.get("email", "")

    email_block = ""
    if email:
        email_block = f'<p><a class="button" href="mailto:{e(email)}" data-track="contact_email_click">Email Julie</a></p>'

    content = f'''<main class="site-shell">
  <article class="article-layout">
    <p class="eyebrow">Contact</p>
    <h1>Technical conversations and project inquiries.</h1>
    <p>{e(contact.get("intro", "For technical conversations, speaking opportunities, or project inquiries, get in touch directly."))}</p>
    <p>{e(contact.get("routing_note", "Most client project work is handled through Zee Creative."))}</p>
    <p><a class="button primary" href="{e(zee_url)}" target="_blank" rel="noopener" data-track="zee_click">Zee Creative</a></p>
    {email_block}
  </article>
</main>'''

    return base_page(config, "Contact", "Contact Julie Zimmerman", content, active="contact")


def render_body(items):
    body_parts = []

    for item in items:
        text = str(item)
        if text.strip().startswith("<"):
            body_parts.append(text)
        else:
            body_parts.append(f"<p>{e(text)}</p>")

    return "\n".join(body_parts)


def build_post(config, post):
    body = render_body(post.get("body", []))

    content = f'''<main class="site-shell">
  <article class="article-layout">
    <p class="eyebrow">{e(post.get("category", "Writing"))} · {e(post.get("date", ""))}</p>
    <h1>{e(post.get("title", "Untitled"))}</h1>
    {body}
    <p class="article-back"><a class="button" href="../writing.html">Back to writing</a></p>
  </article>
</main>'''

    desc = post.get("excerpt") or (post.get("body", [""])[0] if post.get("body") else "")

    return base_page(config, post.get("title", "Untitled"), desc, content, active="writing", level="nested")


def build_adaptive_index(config, pages):
    index_page = next((p for p in pages if p["slug"] == "index"), None)

    if index_page:
        title = index_page.get("title", "Adaptive Experiences")
        desc = index_page.get("excerpt", "Adaptive Experiences")
        body = render_body(index_page.get("body", []))
    else:
        title = "Adaptive Experiences"
        desc = "Adaptive Experiences"
        body = "<p>Adaptive Experiences explores systems designed around real human behavior rather than ideal conditions.</p>"

    links = []

    for page in published_posts(pages):
        if page["slug"] == "index":
            continue

        href = adaptive_href(page, level="nested")
        links.append(f'<li><a href="{href}">{e(page.get("title", "Untitled"))}</a></li>')

    links_html = ""

    if links:
        links_html = f'''<h2>Pages</h2>
<ul>
  {"".join(links)}
</ul>'''

    content = f'''<main class="site-shell">
  <article class="article-layout">
    <p class="eyebrow">Adaptive Experiences</p>
    <h1>{e(title)}</h1>
    {body}
    {links_html}
  </article>
</main>'''

    return base_page(config, title, desc, content, active="adaptive-experiences", level="nested")


def build_adaptive_page(config, page):
    body = render_body(page.get("body", []))

    content = f'''<main class="site-shell">
  <article class="article-layout">
    <p class="eyebrow">Adaptive Experiences</p>
    <h1>{e(page.get("title", "Untitled"))}</h1>
    {body}
    <p class="article-back"><a class="button" href="../index.html">Back to Adaptive Experiences</a></p>
  </article>
</main>'''

    desc = page.get("excerpt") or (page.get("body", [""])[0] if page.get("body") else "")

    return base_page(config, page.get("title", "Untitled"), desc, content, active="adaptive-experiences", level="deep")


def build_problem_index(config, pages):
    index_page = next((p for p in pages if p["slug"] == "index"), None)

    if index_page:
        title = index_page.get("title", "Problems I've Solved")
        desc = index_page.get("excerpt", "Problems I've Solved")
        body = render_body(index_page.get("body", []))
    else:
        title = "Problems I've Solved"
        desc = "Problems I've Solved"
        body = "<p>Examples of problems solved when software assumptions stopped matching reality.</p>"

    content = f"""<main class="site-shell">
  <article class="article-layout">
    <p class="eyebrow">Problems I've Solved</p>
    <h1>{e(title)}</h1>
    {body}
  </article>
</main>"""

    return base_page(config, title, desc, content, active="problems", level="nested")


def build_problem_page(config, page):
    body = render_body(page.get("body", []))

    content = f"""<main class="site-shell">
  <article class="article-layout">
    <p class="eyebrow">Problems I've Solved</p>
    <h1>{e(page.get("title", "Untitled"))}</h1>
    {body}
    <p class="article-back"><a class="button" href="../index.html">Back to Problems I've Solved</a></p>
  </article>
</main>"""

    desc = page.get("excerpt") or (page.get("body", [""])[0] if page.get("body") else "")

    return base_page(config, page.get("title", "Untitled"), desc, content, active="problems", level="deep")


def copy_assets():
    if not ASSETS_DIR.exists():
        raise FileNotFoundError("Missing assets/ folder. Copy the theme assets into assets/ first.")

    dest = OUTPUT_DIR / "assets"

    if dest.exists():
        shutil.rmtree(dest)

    shutil.copytree(ASSETS_DIR, dest)


def write_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_site(config, posts, adaptive_pages, problem_pages):
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    copy_assets()

    count = 0

    write_text(OUTPUT_DIR / "index.html", build_home(config, posts))
    count += 1

    write_text(OUTPUT_DIR / "about.html", build_about(config))
    count += 1

    write_text(OUTPUT_DIR / "writing.html", build_writing(config, posts))
    count += 1

    write_text(OUTPUT_DIR / "contact.html", build_contact(config))
    count += 1

    write_text(
        OUTPUT_DIR / "adaptive-experiences" / "index.html",
        build_adaptive_index(config, adaptive_pages)
    )
    count += 1
    
    write_text(
        OUTPUT_DIR / "problems" / "index.html",
        build_problem_index(config, problem_pages)
    )
    count += 1

    for post in published_posts(posts):
        write_text(
            OUTPUT_DIR / "writing" / f"{post['slug']}.html",
            build_post(config, post)
        )
        count += 1

    for page in published_posts(adaptive_pages):
        if page["slug"] == "index":
            continue

        write_text(
            OUTPUT_DIR / "adaptive-experiences" / page["slug"] / "index.html",
            build_adaptive_page(config, page)
        )
        count += 1
        
    for page in published_posts(problem_pages):
        if page["slug"] == "index":
            continue

        write_text(
            OUTPUT_DIR / "problems" / page["slug"] / "index.html",
            build_problem_page(config, page)
        )
        count += 1

    write_text(OUTPUT_DIR / ".nojekyll", "")

    if CNAME_FILE.exists():
        shutil.copy2(CNAME_FILE, OUTPUT_DIR / "CNAME")

    return count


def push():
    subprocess.run(
        ["git", "add", "build.py", "assets", "templates", "docs", "content", "config.json"],
        check=True
    )

    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if result.returncode == 0:
        print("No changes to commit.")
        return

    subprocess.run(
        ["git", "commit", "-m", f"Build {datetime.now().strftime('%Y-%m-%d %H:%M')}"],
        check=True
    )
    subprocess.run(["git", "push"], check=True)
    print("Pushed to GitHub Pages.")


def ask_to_push():
    return input("Push to GitHub now? [y/N]: ").strip().lower() in ("y", "yes")


def main():
    print("Loading config...")
    config = load_config()

    print("Loading content...")
    posts = load_posts()
    visible = published_posts(posts)
    print(f"Found {len(posts)} posts ({len(visible)} published).")

    print("Loading adaptive experiences...")
    adaptive_pages = load_adaptive_pages()
    visible_adaptive = published_posts(adaptive_pages)
    print(f"Found {len(adaptive_pages)} adaptive pages ({len(visible_adaptive)} published).")

    print("Loading problems...")
    problem_pages = load_problem_pages()
    visible_problem_pages = published_posts(problem_pages)
    print(f"Found {len(problem_pages)} problem pages ({len(visible_problem_pages)} published).")

    print("Building modern theme site...")
    count = build_site(config, posts, adaptive_pages, problem_pages)

    print(f"Build complete. {count} page(s) generated in '{OUTPUT_DIR}/'.")

    if ask_to_push():
        push()
    else:
        print("Skipping push. Site built locally.")


if __name__ == "__main__":
    main()
