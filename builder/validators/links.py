from __future__ import annotations

from pathlib import Path

from .core import ValidationIssue
from .htmlrefs import ReferenceParser
from .paths import resolve_local


def _target_exists(target: Path, href: str) -> bool:
    if target.exists():
        return True
    if href.split("?", 1)[0].split("#", 1)[0].endswith("/"):
        return (target / "index.html").exists()
    return False


def validate_links(output_root: Path) -> tuple[list[ValidationIssue], int]:
    issues: list[ValidationIssue] = []
    checked = 0

    for html_file in output_root.rglob("*.html"):
        parser = ReferenceParser()
        parser.feed(html_file.read_text(encoding="utf-8", errors="ignore"))
        rel_source = html_file.relative_to(output_root)

        for href in parser.links:
            if href.startswith("#"):
                continue
            target, error = resolve_local(html_file, href, output_root)
            if target is None:
                continue
            checked += 1
            if error:
                issues.append(ValidationIssue("links", "error", f"Unsafe link '{href}': {error}", str(rel_source)))
            elif not _target_exists(target, href):
                issues.append(ValidationIssue("links", "error", f"Broken internal link '{href}'", str(rel_source)))

    return issues, checked
