"""
builder/report.py

Generates a build report as a first-class artifact of every build, not
just console output. Written into the staged output before publish, so
the report itself is part of what gets published — anyone can check
/build-report/ on the live site's source to see the health of the last
build, and the report survives in git history for later inspection.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def write_build_report(
    stage_output: Path,
    *,
    counts: dict,
    link_checks: int,
    asset_checks: int,
    issues: list,
) -> None:
    """Write build-report.md and build-report.json into the staged output.

    counts: dict of {collection_name: count} for the summary section.
    link_checks / asset_checks: total number of each kind of reference
    checked, for the report's "X internal links checked" line.
    issues: the full list of ValidationIssue objects from this build.
    """
    report_dir = stage_output / "build-report"
    report_dir.mkdir(parents=True, exist_ok=True)

    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]

    timestamp = datetime.now().isoformat(timespec="seconds")
    status = "PUBLISH BLOCKED" if errors else "PUBLISH APPROVED"

    lines = [
        "# Build Report",
        "",
        f"Generated: {timestamp}",
        f"Status: **{status}**",
        "",
        "## Collections",
        "",
    ]
    for name, count in counts.items():
        lines.append(f"- {count} {name}")

    lines += [
        "",
        "## Validation",
        "",
        f"- {link_checks} internal links checked",
        f"- {asset_checks} assets checked",
        f"- {len(errors)} error(s)",
        f"- {len(warnings)} warning(s)",
        "",
    ]

    if errors:
        lines.append("## Errors (blocking)")
        lines.append("")
        for issue in errors:
            lines.append(f"- {issue.line()}")
        lines.append("")

    if warnings:
        lines.append("## Warnings (non-blocking)")
        lines.append("")
        for issue in warnings:
            lines.append(f"- {issue.line()}")
        lines.append("")

    if not errors and not warnings:
        lines.append("No issues found.")
        lines.append("")

    (report_dir / "build-report.md").write_text("\n".join(lines), encoding="utf-8")

    json_report = {
        "generated": timestamp,
        "status": status,
        "counts": counts,
        "link_checks": link_checks,
        "asset_checks": asset_checks,
        "errors": [
            {"validator": i.validator, "message": i.message, "path": i.path}
            for i in errors
        ],
        "warnings": [
            {"validator": i.validator, "message": i.message, "path": i.path}
            for i in warnings
        ],
    }
    (report_dir / "build-report.json").write_text(
        json.dumps(json_report, indent=2), encoding="utf-8"
    )
