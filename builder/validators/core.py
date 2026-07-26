from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationIssue:
    validator: str
    severity: str
    message: str
    path: str = ""

    def line(self) -> str:
        marker = "ERROR" if self.severity == "error" else "WARNING"
        location = f" ({self.path})" if self.path else ""
        return f"{marker} [{self.validator}] {self.message}{location}"
