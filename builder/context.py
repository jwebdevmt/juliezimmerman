from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class BuildContext:
    """Filesystem staging area for one complete site build."""

    stage_dir: Path
    output: Path = field(init=False)

    def __post_init__(self) -> None:
        self.output = self.stage_dir

    def prepare(self) -> None:
        if self.stage_dir.exists():
            shutil.rmtree(self.stage_dir)
        self.stage_dir.mkdir(parents=True, exist_ok=True)

    def cleanup(self) -> None:
        if self.stage_dir.exists():
            shutil.rmtree(self.stage_dir)


class BuildValidationError(RuntimeError):
    """Raised when staged output contains errors that must block publish."""

    def __init__(self, issues) -> None:
        self.issues = list(issues)
        errors = sum(issue.severity == "error" for issue in self.issues)
        super().__init__(f"Build blocked by {errors} validation error(s)")


def publish(stage: BuildContext, output_dir: Path) -> None:
    """Replace output_dir with staged output while retaining rollback safety."""

    output_dir = output_dir.resolve()
    backup = output_dir.with_name(f"{output_dir.name}-backup")

    if backup.exists():
        shutil.rmtree(backup)

    if output_dir.exists():
        output_dir.rename(backup)

    try:
        stage.output.resolve().rename(output_dir)
    except Exception:
        if backup.exists() and not output_dir.exists():
            backup.rename(output_dir)
        raise

    if backup.exists():
        shutil.rmtree(backup)
