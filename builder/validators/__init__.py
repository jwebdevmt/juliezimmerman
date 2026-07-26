from __future__ import annotations

from pathlib import Path

from .assets import validate_assets
from .core import ValidationIssue
from .links import validate_links
from .uniqueness import validate_unique_nav, validate_unique_output_paths


def run_all_validators(output_root: Path, config, posts, adaptive_pages, problem_pages) -> tuple[list[ValidationIssue], int, int]:
    issues: list[ValidationIssue] = []
    link_issues, link_checks = validate_links(output_root)
    asset_issues, asset_checks = validate_assets(output_root)
    issues.extend(link_issues)
    issues.extend(asset_issues)
    issues.extend(validate_unique_output_paths(posts, adaptive_pages, problem_pages))
    issues.extend(validate_unique_nav(config))
    return issues, link_checks, asset_checks
