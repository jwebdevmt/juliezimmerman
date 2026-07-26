from __future__ import annotations

from pathlib import Path

from .core import ValidationIssue
from .htmlrefs import ReferenceParser
from .paths import resolve_local


def validate_assets(output_root: Path) -> tuple[list[ValidationIssue], int]:
    issues: list[ValidationIssue] = []
    checked = 0

    for html_file in output_root.rglob("*.html"):
        parser = ReferenceParser()
        parser.feed(html_file.read_text(encoding="utf-8", errors="ignore"))
        rel_source = html_file.relative_to(output_root)

        for ref, kind in parser.assets:
            target, error = resolve_local(html_file, ref, output_root)
            if target is None:
                continue
            checked += 1
            if error:
                issues.append(ValidationIssue("assets", "error", f"Unsafe {kind} reference '{ref}': {error}", str(rel_source)))
            elif not target.exists():
                issues.append(ValidationIssue("assets", "error", f"Missing {kind} '{ref}'", str(rel_source)))

    return issues, checked
