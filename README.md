# JulieZimmerman.me

A transactional static publishing platform powering my professional website.

Rather than editing HTML by hand or relying on a database-driven CMS, this site is generated from structured JSON content using a deterministic build pipeline with staged generation, validation, and atomic publication.

The result is a fast, maintainable website designed to scale as new articles, projects, and content types are added.

---

## Why I Built It

Over the years I've maintained hundreds of WordPress websites, migrated platforms, remediated malware, improved accessibility, and supported complex publishing workflows.

While WordPress is an excellent platform, I wanted to explore what publishing could look like when the goals were:

- deterministic builds
- minimal maintenance
- no production database
- version-controlled content
- repeatable deployments
- validation before publication

This project became both my professional website and an engineering exercise in reliable publishing.

---

## Features

- Structured JSON content
- Automatic page generation
- Homepage aggregation
- Writing collections
- Generated navigation
- Build validation
- Asset validation
- Internal link validation
- Duplicate output detection
- Build reports
- Atomic publishing
- GitHub Pages deployment

---

## Architecture

```
Content (JSON)
        │
        ▼
 Build Context
        │
        ▼
 Template Rendering
        │
        ▼
 Validators
        │
        ▼
 Build Report
        │
        ▼
 Atomic Publish
        │
        ▼
 GitHub Pages
```

The website is treated as generated output rather than authored HTML.

---

## Design Goals

This project prioritizes:

- Reliability over complexity
- Deterministic output
- Low operational overhead
- Human-readable content
- Static hosting
- Version control
- Simple deployment

---

## Content Model

Pages are authored as structured JSON rather than HTML.

Examples include:

- Articles
- Projects
- Writing
- Documentation

The build process determines:

- page generation
- navigation
- collections
- homepage summaries
- metadata
- related organization

from the source content.

---

## Validation Pipeline

Before publication the builder verifies:

- Internal links
- Referenced assets
- Duplicate output paths
- Navigation integrity

If validation fails, publication is aborted and the existing site remains unchanged.

---

## Publishing

Generation occurs in a temporary staging directory.

Only after a successful build and validation is the staged output promoted to production.

This transactional approach prevents incomplete or invalid builds from replacing the published site.

---

## Current Technology

- Python
- HTML
- CSS
- JSON
- Git
- GitHub Pages

---

## Future Work

Potential enhancements include:

- Additional content types
- Search improvements
- RSS enhancements
- Image optimization
- Incremental builds
- Creator-focused editing experience

---

## Related Projects

### FYN (Finding Your Neighborhood)

A privacy-first static publishing platform exploring community discovery without centralized data collection.

Many architectural ideas developed for FYN have influenced this publishing engine.

---

## License

Personal project.