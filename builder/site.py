from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from . import core, discipline, experience_renderers, experiences, legacy, profile, search
from .context import BuildContext, BuildValidationError, publish
from .core import BuildResult
from .report import write_build_report
from .validators import run_all_validators

STAGE_DIR = core.ROOT / "docs-build-temp"


@contextmanager
def _staged_output(output_dir: Path):
    """Redirect builders that imported OUTPUT_DIR at module load time."""

    originals = {
        "core": core.OUTPUT_DIR,
        "discipline": discipline.OUTPUT_DIR,
        "profile": profile.OUTPUT_DIR,
        "search": search.OUTPUT_DIR,
        "experience_renderers": experience_renderers.OUTPUT_DIR,
        "experience_data": experience_renderers.DATA_DIR,
    }
    core.OUTPUT_DIR = output_dir
    discipline.OUTPUT_DIR = output_dir
    profile.OUTPUT_DIR = output_dir
    search.OUTPUT_DIR = output_dir
    experience_renderers.OUTPUT_DIR = output_dir
    experience_renderers.DATA_DIR = output_dir / "adaptive-experiences" / "data"
    try:
        yield
    finally:
        core.OUTPUT_DIR = originals["core"]
        discipline.OUTPUT_DIR = originals["discipline"]
        profile.OUTPUT_DIR = originals["profile"]
        search.OUTPUT_DIR = originals["search"]
        experience_renderers.OUTPUT_DIR = originals["experience_renderers"]
        experience_renderers.DATA_DIR = originals["experience_data"]


def build_all(config, posts, adaptive_pages, problem_pages) -> list[BuildResult]:
    """Build the whole site transactionally: stage, validate, then publish."""

    stage = BuildContext(STAGE_DIR)
    stage.prepare()

    try:
        with _staged_output(stage.output):
            legacy_count = legacy.build_site(
                config,
                posts,
                adaptive_pages,
                problem_pages,
                output_dir=stage.output,
            )
            results = [BuildResult("legacy pages", legacy_count)]
            results.append(discipline.build(config, posts))
            results.extend(profile.build(config))
            results.append(experiences.build(config))
            results.append(search.build())

        issues, link_checks, asset_checks = run_all_validators(
            stage.output,
            config,
            posts,
            adaptive_pages,
            problem_pages,
        )
        counts = {result.collection: result.count for result in results}
        write_build_report(
            stage.output,
            counts=counts,
            link_checks=link_checks,
            asset_checks=asset_checks,
            issues=issues,
        )

        for issue in issues:
            print(f"  {issue.line()}")

        errors = [issue for issue in issues if issue.severity == "error"]
        if errors:
            raise BuildValidationError(issues)

        publish(stage, core.ROOT / "docs")
        warnings = sum(issue.severity == "warning" for issue in issues)
        print(f"Validation passed: {link_checks} internal links and {asset_checks} assets checked; {warnings} warning(s).")
        return results
    except Exception:
        stage.cleanup()
        raise
