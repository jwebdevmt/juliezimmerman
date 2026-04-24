import html
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("docs")
CONFIG_FILE = Path("config.json")
CONTENT_DIR = Path("content") / "writing"
ASSET_FOLDERS = ["css", "js", "images", "webfonts"]


CUSTOM_CSS = r"""
/* Julie Zimmerman custom layer over Zinc */
.interior-card { background:#fff; border-radius:18px; padding:2.25rem; box-shadow:0 18px 45px rgba(31,45,61,.08); border:1px solid rgba(31,45,61,.07); }
.interior-lede { font-size:1.12rem; line-height:1.85; color:#5f6670; margin-bottom:2rem; }
.skill-cloud { display:flex; flex-wrap:wrap; gap:.65rem; margin:1rem 0 2rem; }
.skill-pill { display:inline-block; border-radius:999px; background:#f2f6fb; color:#2b4a6f; border:1px solid #dbe6f4; padding:.45rem .75rem; font-size:.9rem; }
.writing-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:1.25rem; margin-top:2rem; }
.article-card { background:#fff; border-radius:16px; padding:1.35rem; box-shadow:0 14px 34px rgba(31,45,61,.07); border:1px solid rgba(31,45,61,.07); height:100%; }
.article-card h2,.article-card h3 { font-size:1.18rem; line-height:1.35; margin-bottom:.7rem; }
.article-card h2 a,.article-card h3 a { color:#1f2d3d; text-decoration:none; }
.article-card h2 a:hover,.article-card h3 a:hover { color:#2557a7; }
.article-meta-line { display:flex; flex-wrap:wrap; align-items:center; gap:.5rem; margin-bottom:.75rem; color:#737b86; font-size:.86rem; }
.article-category { background:#eef4ff; color:#2b4a6f; border-radius:999px; padding:.15rem .55rem; font-size:.75rem; font-weight:700; text-transform:uppercase; letter-spacing:.04em; }
.article-excerpt { color:#5f6670; line-height:1.7; margin-bottom:1rem; }
.read-more { font-weight:700; text-decoration:none; }
.article-shell { background:#fff; border-radius:18px; padding:min(7vw,3rem); box-shadow:0 18px 45px rgba(31,45,61,.08); border:1px solid rgba(31,45,61,.07); }
.article-shell .article-meta-line { margin-bottom:2rem; padding-bottom:1.25rem; border-bottom:1px solid #e6ebf1; }
.article-body p { font-size:1.05rem; line-height:1.9; margin-bottom:1.35rem; }
.article-actions { margin-top:2.25rem; padding-top:1.25rem; border-top:1px solid #e6ebf1; }
.featured-writing .article-card { margin-bottom:1rem; }
@media (max-width:768px){ .interior-card,.article-shell{ padding:1.4rem; } }
"""


def e(value):
    return html.escape("" if value is None else str(value), quote=True)


def load_config():
    with CONFIG_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_posts():
    posts = []
    if not CONTENT_DIR.exists():
        return posts

    for f in CONTENT_DIR.glob("*.json"):
        with f.open("r", encoding="utf-8") as fh:
            post = json.load(fh)
        post["slug"] = f.stem
        posts.append(post)

    posts.sort(key=lambda p: p.get("date", ""), reverse=True)
    return posts


def published_posts(posts):
    return [p for p in posts if p.get("published", False)]


def excerpt(post, words=34):
    if post.get("excerpt"):
        return post["excerpt"]
    body = post.get("body", [])
    text = body[0] if isinstance(body, list) and body else str(body or "")
    bits = text.split()
    if len(bits) <= words:
        return text
    return " ".join(bits[:words]).rstrip(".,;:") + "…"


def find_template_root():
    candidates = [
        Path("zinc-main"),
        Path("template") / "zinc-main",
        Path("template"),
        Path("."),
    ]
    for candidate in candidates:
        if all((candidate / folder).exists() for folder in ["css", "js", "images"]):
            return candidate
    return None


def copy_assets():
    template_root = find_template_root()
    if not template_root:
        print("WARNING: Zinc template assets not found. Expected css/, js/, images/ or zinc-main/css, zinc-main/js, zinc-main/images.")
        return

    for folder in ASSET_FOLDERS:
        source = template_root / folder
        if source.exists():
            dest = OUTPUT_DIR / folder
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(source, dest)

    css_dir = OUTPUT_DIR / "css"
    css_dir.mkdir(parents=True, exist_ok=True)
    (css_dir / "jz-custom.css").write_text(CUSTOM_CSS, encoding="utf-8")


def asset_prefix(level="root"):
    return "../" if level == "nested" else ""


def page_href(slug, level="root"):
    prefix = asset_prefix(level)
    if slug == "index":
        return f"{prefix}index.html"
    if slug == "writing":
        return f"{prefix}writing.html"
    return f"{prefix}{slug}.html"


def post_href(post, level="root"):
    prefix = asset_prefix(level)
    return f"{prefix}writing/{post['slug']}.html"


def head(title, config, level="root", description=None):
    prefix = asset_prefix(level)
    site = config["site"]
    desc = description or site.get("tagline") or site.get("intro") or site.get("description", "")
    owner = config.get("owner", {}).get("name", site.get("title", ""))
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <meta name="description" content="{e(desc)}">
    <meta name="author" content="{e(owner)}">
    <meta property="og:site_name" content="{e(site.get('title', ''))}">
    <meta property="og:title" content="{e(title)}">
    <meta property="og:description" content="{e(desc)}">
    <meta name="twitter:card" content="summary_large_image">
    <title>{e(title)} — {e(site['title'])}</title>
    <link href="https://fonts.googleapis.com/css2?family=Open+Sans:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">
    <link href="{prefix}css/bootstrap.min.css" rel="stylesheet">
    <link href="{prefix}css/fontawesome-all.min.css" rel="stylesheet">
    <link href="{prefix}css/swiper.css" rel="stylesheet">
    <link href="{prefix}css/styles.css" rel="stylesheet">
    <link href="{prefix}css/jz-custom.css" rel="stylesheet">
    <link rel="icon" href="{prefix}images/favicon.png">
</head>'''


def nav(config, active="index", level="root", extra_page=False):
    cls = "navbar navbar-expand-lg fixed-top navbar-light"
    if extra_page:
        cls += " extra-page"

    items = []
    for item in config.get("nav", []):
        slug = item["slug"]
        label = item["label"]
        active_cls = " active" if slug == active else ""
        aria = ' aria-current="page"' if slug == active else ""
        items.append(f'<li class="nav-item"><a class="nav-link{active_cls}"{aria} href="{page_href(slug, level)}">{e(label)}</a></li>')

    return f'''
    <nav id="navbarExample" class="{cls}" aria-label="Main navigation">
        <div class="container">
            <a class="navbar-brand logo-text" href="{page_href('index', level)}">{e(config['site']['title'])}</a>
            <button class="navbar-toggler p-0 border-0" type="button" id="navbarSideCollapse" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="navbar-collapse offcanvas-collapse" id="navbarsExampleDefault">
                <ul class="navbar-nav ms-auto navbar-nav-scroll">
                    {''.join(items)}
                </ul>
                <span class="nav-item">
                    <a class="btn-solid-sm" href="{page_href('contact', level)}">Contact</a>
                </span>
            </div>
        </div>
    </nav>'''


def scripts(level="root"):
    prefix = asset_prefix(level)
    return f'''
    <button onclick="topFunction()" id="myBtn">
        <img src="{prefix}images/up-arrow.png" alt="Back to top">
    </button>
    <script src="{prefix}js/bootstrap.min.js"></script>
    <script src="{prefix}js/swiper.min.js"></script>
    <script src="{prefix}js/purecounter.min.js"></script>
    <script src="{prefix}js/isotope.pkgd.min.js"></script>
    <script src="{prefix}js/scripts.js"></script>
</body>
</html>'''


def footer(config, level="root"):
    year = datetime.now().year
    owner = config.get("owner", {})
    site = config["site"]
    zee_url = owner.get("zee_url", "https://zeecreative.com")
    return f'''
    <div class="footer bg-gray">
        <img class="decoration-city" src="{asset_prefix(level)}images/decoration-city.svg" alt="">
        <div class="container">
            <div class="row">
                <div class="col-lg-12">
                    <h4>{e(site.get('tagline', 'WordPress systems, data integrations, and practical problem-solving'))}</h4>
                    <p>Project work is handled through <a href="{e(zee_url)}" target="_blank" rel="noopener">Zee Creative</a>.</p>
                </div>
            </div>
        </div>
    </div>
    <div class="copyright bg-gray">
        <div class="container">
            <div class="row">
                <div class="col-lg-6">
                    <ul class="list-unstyled li-space-lg p-small">
                        <li><a href="{page_href('writing', level)}">Writing</a></li>
                        <li><a href="{page_href('about', level)}">About</a></li>
                        <li><a href="{page_href('contact', level)}">Contact</a></li>
                    </ul>
                </div>
                <div class="col-lg-6">
                    <p class="p-small statement">Copyright © {year} <a href="{page_href('index', level)}">{e(owner.get('name', site['title']))}</a></p>
                </div>
            </div>
        </div>
    </div>'''


def work_cards(config):
    icons = ["far fa-file-alt", "fas fa-database", "fas fa-shield-alt", "fas fa-sitemap"]
    colors = ["blue", "yellow", "red", "blue"]
    cards = []
    for i, area in enumerate(config.get("work_areas", [])):
        cards.append(f'''
                    <div class="card">
                        <div class="card-icon {colors[i % len(colors)]}">
                            <span class="{icons[i % len(icons)]}"></span>
                        </div>
                        <div class="card-body">
                            <h5 class="card-title">{e(area['title'])}</h5>
                            <p>{e(area['description'])}</p>
                        </div>
                    </div>''')
    return "\n".join(cards)


def post_list(posts, level="root", limit=None, cards=False):
    visible = published_posts(posts)
    if limit:
        visible = visible[:limit]
    if not visible:
        return '<p>Writing coming soon.</p>'

    if cards:
        rows = []
        for p in visible:
            category = p.get("category", "")
            cat = f'<span class="article-category">{e(category)}</span>' if category else ""
            rows.append(f"""
                <article class="article-card">
                    <div class="article-meta-line">
                        <span>{e(p.get('date', ''))}</span>
                        {cat}
                    </div>
                    <h3><a href="{post_href(p, level)}">{e(p['title'])}</a></h3>
                    <p class="article-excerpt">{e(excerpt(p))}</p>
                    <a class="read-more" href="{post_href(p, level)}">Read article →</a>
                </article>""")
        return f'<div class="writing-grid">{"".join(rows)}</div>'

    rows = []
    for p in visible:
        category = p.get("category", "")
        cat = f'<span class="article-category">{e(category)}</span>' if category else ""
        rows.append(f"""
            <li class="article-card mb-3">
                <div class="article-meta-line"><span>{e(p.get('date', ''))}</span>{cat}</div>
                <h3><a href="{post_href(p, level)}">{e(p['title'])}</a></h3>
                <p class="article-excerpt">{e(excerpt(p))}</p>
                <a class="read-more" href="{post_href(p, level)}">Read article →</a>
            </li>""")
    return f'<ul class="list-unstyled li-space-lg">{"".join(rows)}</ul>'


def build_home(config, posts):
    site = config["site"]
    owner = config["owner"]
    return f'''{head('Home', config)}
<body data-bs-spy="scroll" data-bs-target="#navbarExample">
{nav(config, 'index')}
<header id="header" class="header">
    <div class="container">
        <div class="row">
            <div class="col-lg-6 col-xl-5">
                <div class="text-container">
                    <div class="section-title">{e(site.get('tagline', 'Developer / Systems Architect'))}</div>
                    <h1 class="h1-large">{e(owner.get('name', site['title']))}</h1>
                    <p class="p-large">{e(site.get('intro', ''))}</p>
                    <a class="btn-solid-lg" href="about.html">About</a>
                    <a class="quote" href="contact.html"><i class="fas fa-paper-plane"></i>Contact</a>
                </div>
            </div>
            <div class="col-lg-6 col-xl-7">
                <div class="image-container">
                    <img class="img-fluid" src="images/header-illustration.svg" alt="Developer site illustration">
                </div>
            </div>
        </div>
    </div>
</header>
<div id="services" class="cards-1">
    <div class="container">
        <div class="row"><div class="col-lg-12"><h2 class="h2-heading">What I work on</h2></div></div>
        <div class="row"><div class="col-lg-12">{work_cards(config)}</div></div>
    </div>
</div>
<div id="writing" class="basic-1 bg-gray">
    <div class="container">
        <div class="row">
            <div class="col-lg-12">
                <div class="section-title">Selected writing</div>
                <h2>Technical notes from the work</h2>
                <div class="featured-writing">{post_list(posts, 'root', limit=5, cards=True)}</div>
                <a class="btn-solid-reg" href="writing.html">All writing</a>
            </div>
        </div>
    </div>
</div>
<div id="contact" class="form-1">
    <div class="container">
        <div class="row">
            <div class="col-lg-12">
                <h2 class="h2-heading"><span>Project work is handled through</span><br>Zee Creative</h2>
                <p class="p-heading">For technical conversations, speaking opportunities, or project inquiries, get in touch directly.</p>
                <ul class="list-unstyled li-space-lg">
                    <li><i class="fas fa-map-marker-alt"></i> &nbsp;{e(owner.get('location', ''))}</li>
                    <li><i class="fas fa-globe"></i> &nbsp;<a href="{e(owner.get('zee_url', 'https://zeecreative.com'))}" target="_blank" rel="noopener">Zee Creative</a></li>
                    <li><i class="fas fa-envelope"></i> &nbsp;<a href="contact.html">Contact Julie</a></li>
                </ul>
            </div>
        </div>
    </div>
</div>
{footer(config)}
{scripts()}'''


def extra_header(title):
    return f'''
    <header class="ex-header">
        <div class="container">
            <div class="row">
                <div class="col-xl-10 offset-xl-1">
                    <h1>{e(title)}</h1>
                </div>
            </div>
        </div>
    </header>'''


def build_about(config):
    about = config.get("about", {})
    body = "\n".join(f"<p>{e(p)}</p>" for p in about.get("body", []))
    skills = "".join(f'<span class="skill-pill">{e(s)}</span>' for s in about.get("skills", []))
    skill_block = f'<h2 class="mb-3">Technical range</h2><div class="skill-cloud">{skills}</div>' if skills else ""
    return f'''{head('About', config)}
<body>
{nav(config, 'about', extra_page=True)}
{extra_header('About')}
<div class="ex-basic-1 pt-5 pb-5">
    <div class="container"><div class="row"><div class="col-xl-10 offset-xl-1">
        <div class="interior-card">
            {body}
            {skill_block}
            <a class="btn-solid-reg mb-5" href="contact.html">Contact</a>
        </div>
    </div></div></div>
</div>
{footer(config)}
{scripts()}'''


def build_writing(config, posts):
    return f'''{head('Writing', config)}
<body>
{nav(config, 'writing', extra_page=True)}
{extra_header('Writing')}
<div class="ex-basic-1 pt-5 pb-5">
    <div class="container"><div class="row"><div class="col-xl-10 offset-xl-1">
        <div class="interior-card">
            <p class="interior-lede">Technical writing on WordPress systems, data integrations, accessibility, and real production constraints.</p>
            {post_list(posts, 'root', cards=True)}
        </div>
    </div></div></div>
</div>
{footer(config)}
{scripts()}'''


def build_contact(config):
    owner = config.get("owner", {})
    contact = config.get("contact", {})
    return f'''{head('Contact', config)}
<body>
{nav(config, 'contact', extra_page=True)}
{extra_header('Contact')}
<div class="ex-basic-1 pt-5 pb-5">
    <div class="container"><div class="row"><div class="col-xl-10 offset-xl-1">
        <div class="interior-card">
            <p class="interior-lede">{e(contact.get('intro', 'For technical conversations or project inquiries.'))}</p>
            <p>{e(contact.get('routing_note', 'Most client project work is handled through Zee Creative.'))}</p>
            <p><a class="btn-solid-reg" href="{e(owner.get('zee_url', 'https://zeecreative.com'))}" target="_blank" rel="noopener">Zee Creative</a></p>
        </div>
    </div></div></div>
</div>
{footer(config)}
{scripts()}'''


def build_post(config, post):
    body = "\n".join(f"<p>{e(p)}</p>" for p in post.get("body", []))
    return f'''{head(post['title'], config, level='nested', description=post.get('body', [''])[0] if post.get('body') else None)}
<body>
{nav(config, 'writing', level='nested', extra_page=True)}
{extra_header(post['title'])}
<div class="ex-basic-1 pt-5 pb-5">
    <div class="container"><div class="row"><div class="col-xl-10 offset-xl-1">
        <article class="article-shell">
            <div class="article-meta-line">
                <span>{e(post.get('date', ''))}</span>
                <span class="article-category">{e(post.get('category', 'Systems'))}</span>
            </div>
            <div class="article-body">
                {body}
            </div>
            <div class="article-actions">
                <a class="btn-solid-reg mt-4" href="../writing.html">Back to writing</a>
            </div>
        </article>
    </div></div></div>
</div>
{footer(config, level='nested')}
{scripts(level='nested')}'''


def write_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_site(config, posts):
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    copy_assets()

    pages_built = 0
    write_text(OUTPUT_DIR / "index.html", build_home(config, posts)); pages_built += 1
    write_text(OUTPUT_DIR / "about.html", build_about(config)); pages_built += 1
    write_text(OUTPUT_DIR / "writing.html", build_writing(config, posts)); pages_built += 1
    write_text(OUTPUT_DIR / "contact.html", build_contact(config)); pages_built += 1

    for post in published_posts(posts):
        write_text(OUTPUT_DIR / "writing" / f"{post['slug']}.html", build_post(config, post)); pages_built += 1

    write_text(OUTPUT_DIR / ".nojekyll", "")
    return pages_built


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
    return input("Push to GitHub now? [y/N]: ").strip().lower() in ("y", "yes")


def main():
    print("Loading config...")
    config = load_config()
    print("Loading content...")
    posts = load_posts()
    print(f"Found {len(posts)} posts ({len(published_posts(posts))} published)")
    print("Building Zinc template site...")
    pages = build_site(config, posts)
    print(f"Build complete. {pages} page(s) generated in '{OUTPUT_DIR}/'.")
    if ask_to_push():
        push()
    else:
        print("Skipping push. Site built locally.")


if __name__ == "__main__":
    main()
