from __future__ import annotations

from .experience_models import ExperienceRecord


def related_records(records: list[ExperienceRecord], limit: int = 3) -> dict[str, list[dict[str, object]]]:
    output: dict[str, list[dict[str, object]]] = {}
    for current in records:
        matches: list[tuple[int, ExperienceRecord, list[str]]] = []
        for candidate in records:
            if candidate.slug == current.slug:
                continue
            shared = sorted(current.tags & candidate.tags)
            score = len(shared)
            if current.experience.get("destination") == candidate.experience.get("destination"):
                score += 3
            if current.experience.get("type") == candidate.experience.get("type"):
                score += 2
            if score:
                matches.append((score, candidate, shared))
        matches.sort(key=lambda item: (-item[0], item[1].title.lower()))
        output[current.slug] = [
            {
                "slug": candidate.slug,
                "title": candidate.title,
                "summary": candidate.summary,
                "url": candidate.canonical_url,
                "score": score,
                "shared_topics": shared,
            }
            for score, candidate, shared in matches[:limit]
        ]
    return output
