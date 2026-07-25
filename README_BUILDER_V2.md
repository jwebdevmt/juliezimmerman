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
