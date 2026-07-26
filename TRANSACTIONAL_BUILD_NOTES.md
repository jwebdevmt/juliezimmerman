# Transactional publishing platform integration

## Build flow

The top-level builder now runs the complete site through three phases:

1. **Stage** — all generators write into `docs-build-temp/`.
2. **Validate** — internal links, referenced assets, navigation duplication, and generated output-path collisions are checked.
3. **Publish** — the staged directory replaces `docs/` only after validation succeeds.

A generation or validation failure removes the staging directory and leaves the existing `docs/` tree unchanged.

## Added

- `builder/context.py` — staging lifecycle, validation exception, rollback-safe publish
- `builder/report.py` — Markdown and JSON reports under `docs/build-report/`
- `builder/validators/` — HTML-reference parsing, link checks, asset checks, path safety, and uniqueness checks
- `tests/test_build_pipeline.py` — root-relative URL and transactional publish tests

## Changed

- `builder/site.py` now owns the transaction for the entire multi-builder site, not only legacy pages.
- `builder/legacy.py` renders into a supplied output directory and no longer deletes `docs/`.
- `writing_group()` prefers explicit `group` metadata.
- Existing writing JSON files now include `group`.
- `push()` stages the complete repository with `git add -A`, so new builder modules are included.

## Verification performed

- `python -m unittest discover -s tests -v`
- `python build.py --no-push`
- Simulated a missing-template failure during generation and confirmed the live `docs/` digest remained unchanged byte-for-byte.
