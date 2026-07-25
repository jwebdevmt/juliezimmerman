from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Perspective:
    id: str
    name: str
    role: str
    excerpt: str
    full_text: str
    pin: dict[str, Any]


@dataclass(frozen=True)
class ExperienceRecord:
    schema_version: int
    slug: str
    title: str
    summary: str
    published: bool
    experience: dict[str, Any]
    constraints: list[str]
    perspectives: tuple[Perspective, ...]
    synthesis: dict[str, Any]
    publishing: dict[str, Any]
    taxonomy: dict[str, list[str]]
    source: Path

    @classmethod
    def from_mapping(cls, data: dict[str, Any], source: Path) -> "ExperienceRecord":
        perspectives = tuple(
            Perspective(
                id=item["id"],
                name=item["name"],
                role=item.get("role", "Preserved perspective"),
                excerpt=item["excerpt"],
                full_text=item.get("full_text", item["excerpt"]),
                pin=dict(item.get("pin", {})),
            )
            for item in data.get("perspectives", [])
        )
        taxonomy = data.get("taxonomy", {}) or {}
        return cls(
            schema_version=int(data["schema_version"]),
            slug=str(data.get("slug") or source.stem),
            title=str(data["title"]),
            summary=str(data["summary"]),
            published=bool(data.get("published", False)),
            experience=dict(data["experience"]),
            constraints=list(data.get("constraints", [])),
            perspectives=perspectives,
            synthesis=dict(data["synthesis"]),
            publishing=dict(data["publishing"]),
            taxonomy={key: list(value or []) for key, value in taxonomy.items()},
            source=source,
        )

    @property
    def canonical_url(self) -> str:
        return self.experience.get("canonical_page") or f"/adaptive-experiences/{self.slug}/"

    @property
    def tags(self) -> set[str]:
        values: set[str] = set()
        for group in self.taxonomy.values():
            values.update(str(value).strip().lower() for value in group if str(value).strip())
        for field in ("type", "destination", "audience"):
            value = self.experience.get(field)
            if value:
                values.add(str(value).strip().lower())
        return values

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "slug": self.slug,
            "title": self.title,
            "summary": self.summary,
            "published": self.published,
            "experience": self.experience,
            "constraints": self.constraints,
            "perspectives": [
                {
                    "id": item.id,
                    "name": item.name,
                    "role": item.role,
                    "excerpt": item.excerpt,
                    "full_text": item.full_text,
                    "pin": item.pin,
                }
                for item in self.perspectives
            ],
            "synthesis": self.synthesis,
            "publishing": self.publishing,
            "taxonomy": self.taxonomy,
        }
