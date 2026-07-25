from __future__ import annotations

<<<<<<< HEAD
from . import discipline, legacy, profile, search
=======
from . import discipline, experiences, legacy, profile, search
>>>>>>> 91a585f (publishing context)
from .core import BuildResult


def build_all(config, posts, adaptive_pages, problem_pages) -> list[BuildResult]:
    legacy_count = legacy.build_site(config, posts, adaptive_pages, problem_pages)
    results = [BuildResult("legacy pages", legacy_count)]
    results.append(discipline.build(config, posts))
    results.extend(profile.build(config))
<<<<<<< HEAD
=======
    results.append(experiences.build(config))
>>>>>>> 91a585f (publishing context)
    results.append(search.build())
    return results
