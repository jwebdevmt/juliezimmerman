# juliezimmerman.me Builder v2

This package refactors the existing site builder without replacing the working page renderers all at once. It uses only the Python standard library; no package installation is required.

## What changed

- `build.py` is now a small command-line entry point.
- `builder/legacy.py` preserves the existing home, about, writing, problems, and Adaptive Experiences output.
- `builder/core.py` provides shared collection loading, JSON parsing, schema validation, template rendering, related-content scoring, and output helpers.
- `builder/site.py` is the central build registry/orchestrator.
- `builder/discipline.py` builds reusable professional discipline pages.
- `builder/search.py` creates `docs/search.json` from all published collections.
- `content/disciplines/` stores discipline page data.
- `content/projects/` stores normalized project records referenced by discipline pages.
- `schemas/discipline-page.schema.json` validates discipline content before output is written using the built-in standard-library validator.
- `templates/discipline.html` controls discipline-page presentation.

## Build locally

From the project root:

```bash
python build.py --no-push
```

The finished site is written to `docs/`.

To retain the existing interactive push prompt:

```bash
python build.py
```

## Publish the AI Systems page

The included AI Systems page is already marked `published` and builds to:

```text
docs/ai-systems/index.html
```

The navigation entry is already included in `config.json`.

## Add another discipline

1. Copy `content/disciplines/ai-systems.json`.
2. Change its filename, `slug`, titles, sections, tags, and project references.
3. Add any reusable project files to `content/projects/`.
4. Add the discipline to `config.json` navigation when it should appear in the main menu.
5. Run `python build.py --no-push`.

A missing project reference or invalid discipline structure stops the build with a precise error. No `jsonschema` dependency is required.

## Project references

Discipline files reference project slugs rather than embedding full project records:

```json
"projects": [
  "finding-your-neighborhood",
  "calendar-defender"
]
```

The corresponding records live in `content/projects/` so each project has one source of truth.

## Migration boundary

The existing content types still use their proven renderers through `builder/legacy.py`. This is deliberate: the AI discipline page, normalized project records, shared infrastructure, schema validation, and search index are live now without risking regressions across the existing site.

Future content types can be moved into independent modules one at a time and registered in `builder/site.py`.
<<<<<<< HEAD
=======


## Canonical Adaptive Experience records

Adaptive Experiences now have a channel-neutral source format in `content/experiences/*.yaml`. The YAML record is the source of truth for the experience, its constraints, preserved perspectives, Julie's synthesis, and publication instructions.

The build generates:

- `docs/adaptive-experiences/data/experiences.json` — complete public records
- `docs/adaptive-experiences/data/<slug>.json` — one portable record per experience
- `docs/adaptive-experiences/data/pins.json` — one Pinterest-ready record per preserved perspective
- `docs/adaptive-experiences/data/perspectives.json` — perspective archive index
- `docs/adaptive-experiences/perspectives/<id>/index.html` — generated perspective archive pages

The included YAML loader intentionally supports a small, predictable subset of YAML and requires no installed package. Use two-space indentation. It supports nested mappings, lists, inline lists, quoted scalars, and `|` block text. Advanced YAML features such as anchors and custom tags are deliberately unsupported.

The existing long-form Adaptive Experience pages remain in place during migration. New distribution channels should consume the canonical records rather than scrape HTML. This keeps the website, Pinterest pins, future feeds, and a possible standalone site synchronized from one source.

## Multi-channel Adaptive Experiences pipeline

The canonical experience builder now follows a renderer pipeline rather than embedding every output in one module:

```text
YAML source
  → validation
  → ExperienceRecord internal model
  → relationship scoring
  → JSON, Pinterest, perspective archive, and RSS renderers
```

Key modules:

- `builder/experience_models.py` — channel-neutral internal model
- `builder/experience_validation.py` — strict build-time completeness checks
- `builder/experience_relationships.py` — metadata-driven related-experience scoring
- `builder/experience_renderers.py` — independent output renderers
- `builder/experiences.py` — collection loader and pipeline orchestration
- `schemas/adaptive-experience.schema.json` — documented public schema

Generated outputs now also include:

- `docs/adaptive-experiences/data/relationships.json`
- `docs/adaptive-experiences/data/pins/<perspective-id>.json`
- `docs/adaptive-experiences/feed.xml`

Use `taxonomy` in each YAML record to connect related experiences without hard-coded links:

```yaml
taxonomy:
  domains: ["Disney", "Travel"]
  needs: ["Energy management", "Prioritization"]
  contexts: ["Solo travel", "Halloween"]
```

The build stops before publishing when a record is incomplete, contains duplicate perspective IDs, uses an unsupported schema version, or has malformed taxonomy. This keeps every downstream renderer synchronized with one valid source record.
>>>>>>> 91a585f (publishing context)
