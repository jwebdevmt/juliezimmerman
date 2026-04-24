import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = "docs"
CONFIG_FILE = "config.json"
CONTENT_DIR = "content"

FORBIDDEN_PATTERNS = [
    "google-analytics",
    "googletagmanager",
    "doubleclick",
    "adsbygoogle",
    "facebook.net",
    "document.cookie",
    "navigator.sendBeacon",
    "localStorage",
    "sessionStorage",
    "XMLHttpRequest",
    "fetch("
]

# ─── LOAD CONFIG ─────────────────────────────────────────

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_config(config):
    required = ["site", "nav", "owner"]
    for key in required:
        if key not in config:
            raise Exception(f"Missing '{key}' block in config.json")
    if not config["site"].get("title"):
        raise Exception("Missing site title")
    if not config["site"].get("tagline"):
        raise Exception("Missing site tagline")

# ─── LOAD CONTENT ────────────────────────────────────────

def load_posts():
    posts = []
    content_path = Path(CONTENT_DIR) / "writing"
    if not content_path.exists():
        return posts

    for f in sorted(content_path.glob("*.json"), reverse=True):
        with open(f, "r", encoding="utf-8") as fh:
            post = json.load(fh)
            post["slug"] = f.stem
            posts.append(post)

    return posts

def published_posts(posts):
    return [p for p in posts if p.get("published", False)]

# ─── HTML COMPONENTS ─────────────────────────────────────

def build_head(title, config):
    site = config["site"]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — {site["title"]}</title>
<meta name="description" content="{site["tagline"]}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600&family=Source+Serif+4:ital,wght@0,300;0,400;1,300&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
:root {{
    --bg: #fafaf8;
    --surface: #f4f3ef;
    --border: #e2e0d9;
    --text: #1c1c1a;
    --muted: #6b6960;
    --accent: #2c4a6e;
    --accent-light: #e8edf4;
    --mono: 'JetBrains Mono', monospace;
    --serif: 'Source Serif 4', Georgia, serif;
    --display: 'Playfair Display', Georgia, serif;
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
    background: var(--bg);
    color: var(--text);
    font-family: var(--serif);
    font-size: 1.05rem;
    line-height: 1.75;
    padding: 0;
}}

a {{
    color: var(--accent);
    text-decoration: none;
}}

a:hover {{
    text-decoration: underline;
    text-underline-offset: 3px;
}}

/* ─── LAYOUT ─── */

.site-wrapper {{
    max-width: 760px;
    margin: 0 auto;
    padding: 0 2rem;
}}

/* ─── HEADER ─── */

header {{
    border-bottom: 1px solid var(--border);
    padding: 1.5rem 0;
    margin-bottom: 3rem;
}}

.header-inner {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 1rem;
}}

.site-name {{
    font-family: var(--display);
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text);
    letter-spacing: 0.01em;
}}

.site-name a {{
    color: var(--text);
}}

nav {{
    display: flex;
    gap: 1.5rem;
}}

nav a {{
    font-family: var(--mono);
    font-size: 0.78rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--muted);
}}

nav a:hover {{
    color: var(--accent);
    text-decoration: none;
}}

nav a.active {{
    color: var(--accent);
    border-bottom: 1px solid var(--accent);
}}

/* ─── MAIN ─── */

main {{
    padding-bottom: 5rem;
}}

/* ─── HERO ─── */

.hero {{
    padding: 3rem 0 4rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 3.5rem;
}}

.hero h1 {{
    font-family: var(--display);
    font-size: clamp(2rem, 5vw, 3rem);
    font-weight: 400;
    line-height: 1.2;
    margin-bottom: 1rem;
    color: var(--text);
}}

.hero .tagline {{
    font-family: var(--mono);
    font-size: 0.85rem;
    color: var(--accent);
    letter-spacing: 0.04em;
    margin-bottom: 1.5rem;
    text-transform: uppercase;
}}

.hero p {{
    font-size: 1.1rem;
    color: var(--muted);
    max-width: 580px;
    line-height: 1.8;
}}

/* ─── SECTIONS ─── */

.section {{
    margin-bottom: 3.5rem;
}}

.section-label {{
    font-family: var(--mono);
    font-size: 0.72rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 1.25rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
}}

/* ─── WORK AREAS ─── */

.work-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1px;
    background: var(--border);
    border: 1px solid var(--border);
    margin-bottom: 0.5rem;
}}

.work-item {{
    background: var(--bg);
    padding: 1.25rem 1.5rem;
}}

.work-item h3 {{
    font-family: var(--display);
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 0.4rem;
}}

.work-item p {{
    font-size: 0.88rem;
    color: var(--muted);
    line-height: 1.6;
}}

/* ─── POST LIST ─── */

.post-list {{
    list-style: none;
}}

.post-item {{
    padding: 1.25rem 0;
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 1rem;
}}

.post-item:last-child {{
    border-bottom: none;
}}

.post-title {{
    font-family: var(--display);
    font-size: 1.05rem;
    font-weight: 400;
}}

.post-title a {{
    color: var(--text);
}}

.post-title a:hover {{
    color: var(--accent);
}}

.post-meta {{
    font-family: var(--mono);
    font-size: 0.72rem;
    color: var(--muted);
    white-space: nowrap;
    letter-spacing: 0.04em;
}}

.post-category {{
    font-family: var(--mono);
    font-size: 0.68rem;
    color: var(--accent);
    background: var(--accent-light);
    padding: 0.1em 0.5em;
    border-radius: 3px;
    margin-left: 0.5rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    vertical-align: middle;
}}

/* ─── ARTICLE ─── */

article {{
    max-width: 680px;
}}

article h1 {{
    font-family: var(--display);
    font-size: clamp(1.6rem, 4vw, 2.2rem);
    font-weight: 400;
    line-height: 1.25;
    margin-bottom: 0.75rem;
}}

.article-meta {{
    font-family: var(--mono);
    font-size: 0.75rem;
    color: var(--muted);
    letter-spacing: 0.04em;
    margin-bottom: 2.5rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--border);
}}

article h2 {{
    font-family: var(--display);
    font-size: 1.3rem;
    font-weight: 600;
    margin: 2.5rem 0 0.75rem;
}}

article p {{
    margin-bottom: 1.25rem;
}}

article code {{
    font-family: var(--mono);
    font-size: 0.85em;
    background: var(--surface);
    padding: 0.15em 0.4em;
    border-radius: 3px;
    color: var(--accent);
}}

article pre {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    padding: 1.25rem 1.5rem;
    overflow-x: auto;
    margin: 1.5rem 0;
    font-family: var(--mono);
    font-size: 0.85rem;
    line-height: 1.6;
}}

article ul, article ol {{
    padding-left: 1.5rem;
    margin-bottom: 1.25rem;
}}

article li {{
    margin-bottom: 0.4rem;
}}

/* ─── PAGE CONTENT ─── */

.page-content h1 {{
    font-family: var(--display);
    font-size: clamp(1.6rem, 4vw, 2.2rem);
    font-weight: 400;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
}}

.page-content p {{
    margin-bottom: 1.25rem;
    max-width: 620px;
}}

.page-content h2 {{
    font-family: var(--display);
    font-size: 1.2rem;
    font-weight: 600;
    margin: 2rem 0 0.75rem;
}}

/* ─── ZEE CALLOUT ─── */

.zee-note {{
    background: var(--accent-light);
    border-left: 3px solid var(--accent);
    padding: 1rem 1.25rem;
    margin-top: 2rem;
    font-size: 0.9rem;
    color: var(--muted);
}}

.zee-note a {{
    color: var(--accent);
}}

/* ─── CONTACT ─── */

.contact-block {{
    padding: 2rem 0;
}}

.contact-block .email-link {{
    font-family: var(--mono);
    font-size: 1rem;
    color: var(--accent);
    display: inline-block;
    margin-bottom: 1rem;
}}

/* ─── FOOTER ─── */

footer {{
    border-top: 1px solid var(--border);
    padding: 1.5rem 0;
    margin-top: 4rem;
}}

.footer-inner {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
}}

.footer-inner p {{
    font-family: var(--mono);
    font-size: 0.72rem;
    color: var(--muted);
    letter-spacing: 0.04em;
}}

@media (max-width: 600px) {{
    .work-grid {{ grid-template-columns: 1fr; }}
    .header-inner {{ flex-direction: column; gap: 0.75rem; }}
    nav {{ gap: 1rem; }}
}}
</style>
</head>
<body>
<div class="site-wrapper">"""

def build_header(config, active_page=""):
    nav_items = config["nav"]
    nav_links = ""
    for item in nav_items:
        active = ' class="active"' if item["slug"] == active_page else ""
        filename = "index.html" if item["slug"] == "index" else f"{item['slug']}.html"
        nav_links += f'<a href="/{filename}"{active}>{item["label"]}</a>'

    return f"""
<header>
    <div class="header-inner">
        <div class="site-name"><a href="/index.html">{config["site"]["title"]}</a></div>
        <nav>{nav_links}</nav>
    </div>
</header>"""

def build_footer(config):
    year = datetime.now().year
    return f"""
<footer>
    <div class="footer-inner">
        <p>© {year} {config["owner"]["name"]}</p>
    </div>
</footer>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
<script>
function revealEmail() {{
    const el = document.getElementById('contact-email');
    if (el) {{
        const user = 'jwebdevmt';
        const domain = 'gmail.com';
        const address = user + '@' + domain;
        el.href = 'mailto:' + address;
        el.textContent = address;
    }}
}}
document.addEventListener('DOMContentLoaded', revealEmail);
</script>
</body>
</html>"""

# ─── PAGE BUILDERS ───────────────────────────────────────

def build_home(config, posts):
    featured = published_posts(posts)

    post_items = ""
    for p in featured:
        category = p.get('category', '')
        cat_tag = f' <span class="post-category">{category}</span>' if category else ''
        post_items += f"""
        <li class="post-item">
            <span class="post-title"><a href="/writing/{p['slug']}.html">{p['title']}</a>{cat_tag}</span>
            <span class="post-meta">{p.get('date', '')}</span>
        </li>"""

    if not post_items:
        post_items = '<li class="post-item"><span class="post-meta">Writing coming soon.</span></li>'



    work_areas = config.get("work_areas", [])
    work_grid = ""
    for area in work_areas:
        work_grid += f"""
        <div class="work-item">
            <h3>{area['title']}</h3>
            <p>{area['description']}</p>
        </div>"""

    owner = config["owner"]
    site = config["site"]

    return f"""{build_head("Home", config)}
{build_header(config, "index")}
<main>
    <div class="hero">
        <div class="tagline">{site['tagline']}</div>
        <h1>{owner['name']}</h1>
        <p>{site['intro']}</p>
    </div>

    <div class="section">
        <div class="section-label">What I work on</div>
        <div class="work-grid">{work_grid}</div>
    </div>

    <div class="section">
        <div class="section-label">Selected writing</div>
        <ul class="post-list">{post_items}</ul>
        <p style="margin-top:1rem;font-size:0.9rem;"><a href="/writing.html">All writing →</a></p>
    </div>

    <div class="zee-note">
        Project work is handled through <a href="{owner.get('zee_url', '#')}" target="_blank" rel="noopener">Zee Creative</a>.
    </div>
</main>
{build_footer(config)}"""

def build_about(config):
    owner = config["owner"]
    about = config.get("about", {})

    paragraphs = "".join(f"<p>{p}</p>" for p in about.get("body", []))

    skills = about.get("skills", [])
    skill_items = "".join(f"<li>{s}</li>" for s in skills)
    skill_block = f"<h2>Technical range</h2><ul>{skill_items}</ul>" if skills else ""

    return f"""{build_head("About", config)}
{build_header(config, "about")}
<main>
    <div class="page-content">
        <h1>About</h1>
        {paragraphs}
        {skill_block}
        <div class="zee-note">
            Client project work is handled through <a href="{owner.get('zee_url', '#')}" target="_blank" rel="noopener">Zee Creative</a>.
        </div>
    </div>
</main>
{build_footer(config)}"""

def build_writing_index(config, posts):
    visible = published_posts(posts)

    items = ""
    for p in visible:
        items += f"""
        <li class="post-item">
            <span class="post-title"><a href="/writing/{p['slug']}.html">{p['title']}</a></span>
            <span class="post-meta">{p.get('date', '')}</span>
        </li>"""

    if not items:
        items = '<li class="post-item"><span class="post-meta">Writing coming soon.</span></li>'

    return f"""{build_head("Writing", config)}
{build_header(config, "writing")}
<main>
    <div class="page-content">
        <h1>Writing</h1>
        <ul class="post-list">{items}</ul>
    </div>
</main>
{build_footer(config)}"""

def build_post(config, post):
    body = post.get("body", "")
    # Simple paragraph rendering
    paragraphs = "".join(f"<p>{p}</p>" for p in body) if isinstance(body, list) else f"<p>{body}</p>"

    return f"""{build_head(post['title'], config)}
{build_header(config, "writing")}
<main>
    <article>
        <h1>{post['title']}</h1>
        <div class="article-meta">{post.get('date', '')} · {post.get('category', 'Systems')}</div>
        {paragraphs}
    </article>
</main>
{build_footer(config)}"""

def build_contact(config):
    owner = config["owner"]
    contact = config.get("contact", {})

    return f"""{build_head("Contact", config)}
{build_header(config, "contact")}
<main>
    <div class="page-content">
        <h1>Contact</h1>
        <p>{contact.get('intro', 'For technical conversations or project inquiries.')}</p>
        <div class="contact-block">
            <a id="contact-email" class="email-link" href="#">Loading...</a>
            <p style="font-size:0.9rem;color:var(--muted);">{contact.get('routing_note', '')}</p>
        </div>
        <div class="zee-note">
            Project work is handled through <a href="{owner.get('zee_url', '#')}" target="_blank" rel="noopener">Zee Creative</a>.
        </div>
    </div>
</main>
{build_footer(config)}"""

# ─── BUILD SITE ──────────────────────────────────────────

def build_site(config, posts):
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)
    os.makedirs(os.path.join(OUTPUT_DIR, "writing"), exist_ok=True)

    pages_built = 0

    # Home
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(build_home(config, posts))
    pages_built += 1

    # About
    with open(os.path.join(OUTPUT_DIR, "about.html"), "w", encoding="utf-8") as f:
        f.write(build_about(config))
    pages_built += 1

    # Writing index
    with open(os.path.join(OUTPUT_DIR, "writing.html"), "w", encoding="utf-8") as f:
        f.write(build_writing_index(config, posts))
    pages_built += 1

    # Contact
    with open(os.path.join(OUTPUT_DIR, "contact.html"), "w", encoding="utf-8") as f:
        f.write(build_contact(config))
    pages_built += 1

    # Individual posts
    for post in published_posts(posts):
        path = os.path.join(OUTPUT_DIR, "writing", f"{post['slug']}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(build_post(config, post))
        pages_built += 1

    # No Jekyll
    open(os.path.join(OUTPUT_DIR, ".nojekyll"), "w").close()

    return pages_built

# ─── MORALITY CHECK ──────────────────────────────────────

def check_output():
    for root, _, files in os.walk(OUTPUT_DIR):
        for file in files:
            if not file.endswith(".html"):
                continue
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().lower()
                for pattern in FORBIDDEN_PATTERNS:
                    if pattern.lower() in content:
                        raise Exception(f"HARD STOP: Forbidden pattern '{pattern}' in {file}")

# ─── GIT PUSH ────────────────────────────────────────────

def push():
    subprocess.run(["git", "add", "docs"], check=True)
    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if result.returncode == 0:
        print("No changes to commit.")
        return
    subprocess.run(["git", "commit", "-m", f"Build {datetime.now().strftime('%Y-%m-%d %H:%M')}"], check=True)
    subprocess.run(["git", "push"], check=True)
    print("Pushed to GitHub Pages.")

def ask_to_push():
    answer = input("Push to GitHub now? [y/N]: ").strip().lower()
    return answer in ("y", "yes")

# ─── MAIN ────────────────────────────────────────────────

def main():
    print("Loading config...")
    config = load_config()
    validate_config(config)

    print("Loading content...")
    posts = load_posts()
    print(f"Found {len(posts)} posts ({len(published_posts(posts))} published)")

    print("Building site...")
    pages_built = build_site(config, posts)

    print("Running integrity checks...")
    check_output()

    print(f"Build complete. {pages_built} pages generated in '{OUTPUT_DIR}/'.")

    if ask_to_push():
        push()
    else:
        print("Skipping push. Site built locally.")

if __name__ == "__main__":
    main()
