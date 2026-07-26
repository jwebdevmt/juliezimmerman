from __future__ import annotations

from collections import Counter
from pathlib import PurePosixPath

from .core import ValidationIssue


def validate_unique_output_paths(posts, adaptive_pages, problem_pages) -> list[ValidationIssue]:
    paths: list[str] = []
    paths.extend(str(PurePosixPath("writing") / f"{item['slug']}.html") for item in posts if item.get("slug"))
    paths.extend(str(PurePosixPath("adaptive-experiences") / item["slug"] / "index.html") for item in adaptive_pages if item.get("slug") and item["slug"] != "index")
    paths.extend(str(PurePosixPath("problems") / item["slug"] / "index.html") for item in problem_pages if item.get("slug") and item["slug"] != "index")

    issues: list[ValidationIssue] = []
    for path, count in Counter(paths).items():
        if count > 1:
            issues.append(ValidationIssue("uniqueness", "error", f"Generated output path '{path}' is produced {count} times"))
    return issues


def validate_unique_nav(config) -> list[ValidationIssue]:
    nav = config.get("nav", [])
    labels: list[str] = []
    targets: list[str] = []

    def collect(item) -> None:
        label = item.get("label", item.get("slug", ""))
        if label:
            labels.append(label)
        target = item.get("href") or item.get("slug")
        if target:
            targets.append(target)
        for child in item.get("children", []):
            collect(child)

    for item in nav:
        collect(item)

    issues: list[ValidationIssue] = []
    for label, count in Counter(labels).items():
        if count > 1:
            issues.append(ValidationIssue("uniqueness", "warning", f"Navigation label '{label}' appears {count} times"))
    for target, count in Counter(targets).items():
        if count > 1:
            issues.append(ValidationIssue("uniqueness", "warning", f"Navigation target '{target}' appears {count} times"))
    return issues
